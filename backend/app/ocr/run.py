from sqlalchemy import text
from App.Db.Session import SessionLocal

from App.Ocr.GoogleOcr import process_file
from App.Ocr.Extractor import extract_fields, normalize_from_raw
from App.Ocr.DocClassifier import detect_document_type
from App.Ocr.GptDocClassifier import gpt_detect_document_type

from App.Services.InsertAdmissionForm import insert_admission_form
from App.Services.InsertAadhaar import insert_aadhaar
from App.Services.InsertTransferCertificate import insert_transfer_certificate
from App.Services.InsertMarksheet import insert_marksheet
from App.Services.InsertBirthCertificate import insert_birth_certificate

from App.Jobs.RunAadhaarLookup import run_aadhaar_lookup
from App.Jobs.RunTransferCertificateLookup import run_tc_lookup
from App.Jobs.RunMarksheetLookup import run_marksheet_lookup
from App.Jobs.RunBcLookup import run_bc_lookup

from App.Helper.EnsureRessassesDict import ensure_dict
from App.Utils.UpdateDisplayName import update_display_name

from App.Ocr.SetFileName import (
    tc_display_name,
    aadhaar_display_name,
    admission_display_name,
    highschool_marksheet_display_name,
    birth_certificate_display_name,
)

import os
import json

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
NOW_EXPR = "datetime('now')" if DEV_MODE else "now()"

UPLOAD_DIR = "uploads"


# ==========================================================
# ✅ Reset stuck jobs (worker crash recovery)
# ==========================================================
def reset_stuck_jobs(db):
    if os.getenv("DEV_MODE", "false").lower() == "true":
        db.execute(text("""
            UPDATE uploaded_files
            SET processing = false
            WHERE processing = true
              AND extraction_done = false
              AND created_at < datetime('now', '-15 minutes')
        """))
    else:
        db.execute(text("""
            UPDATE uploaded_files
            SET processing = false
            WHERE processing = true
              AND extraction_done = false
              AND created_at < now() - interval '15 minutes'
        """))
    db.commit()


# ==========================================================
# ✅ Claim ONE file safely (Thread Safe Queue)
# ==========================================================
def claim_next_file(db):
    if os.getenv("DEV_MODE", "false").lower() == "true":
        file = db.execute(text("""
            SELECT file_id, file_path, extracted_raw, display_name
            FROM uploaded_files
            WHERE extraction_done = false
              AND processing = false
              AND extraction_error IS NULL
              AND (
                    display_name IS NULL
                 OR LOWER(display_name) NOT LIKE '%pending_admission%'
              )
            ORDER BY created_at
            LIMIT 1
        """)).fetchone()
    else:
        file = db.execute(text("""
            SELECT file_id, file_path, extracted_raw, display_name
            FROM uploaded_files
            WHERE extraction_done = false
              AND processing = false
              AND extraction_error IS NULL
              AND (
                    display_name IS NULL
                 OR display_name NOT ILIKE '%PENDING_ADMISSION%'
              )
            ORDER BY created_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)).fetchone()

    if not file:
        return None

    file_id = file.file_id

    # ✅ Mark claimed
    db.execute(text("""
        UPDATE uploaded_files
        SET processing = true
        WHERE file_id = :file_id
    """), {"file_id": file_id})

    db.commit()
    return file


# ==========================================================
# ✅ Process One File Fully
# ==========================================================
def process_single_file(db, file_id, file_path, extracted_raw):

    structured = None
    doc_type = "unknown"

    full_path = os.path.join(UPLOAD_DIR, file_path)

    # -------------------------------------------------------
    # 1️⃣ OCR
    # -------------------------------------------------------
    row = db.execute(text("""
        SELECT ocr_done, ocr_text
        FROM uploaded_files
        WHERE file_id = :file_id
    """), {"file_id": file_id}).fetchone()

    if not row.ocr_done:
        ocr_text = process_file(full_path)

        db.execute(text(f"""
            UPDATE uploaded_files
            SET ocr_text = :ocr_text,
                ocr_done = true,
                ocr_at = {NOW_EXPR}
            WHERE file_id = :file_id
        """), {
            "ocr_text": ocr_text,
            "file_id": file_id
        })
    else:
        ocr_text = row.ocr_text

    # -------------------------------------------------------
    # 2️⃣ Document Type Detection
    # -------------------------------------------------------
    doc_type = db.execute(text("""
        SELECT doc_type
        FROM uploaded_files
        WHERE file_id = :file_id
    """), {"file_id": file_id}).scalar()

    if doc_type == "unknown":
        doc_type = detect_document_type(ocr_text)
        if doc_type == "unknown":
            doc_type = gpt_detect_document_type(ocr_text)

    db.execute(text("""
        UPDATE uploaded_files
        SET doc_type = :doc_type
        WHERE file_id = :file_id
    """), {
        "doc_type": doc_type,
        "file_id": file_id
    })
    db.commit()
    # -------------------------------------------------------
    # 3️⃣ Extraction
    # -------------------------------------------------------
    extracted_raw = ensure_dict(extracted_raw)

    if extracted_raw:
        structured = normalize_from_raw(doc_type, extracted_raw)
    else:
        structured = extract_fields(doc_type, ocr_text)

    if structured and "error" in structured:
        raise Exception(structured["error"])

    # ✅ Save extracted_raw IMMEDIATELY (even if inserts fail later)
    db.execute(text("""
        UPDATE uploaded_files
        SET extracted_raw = :raw
        WHERE file_id = :file_id
    """), {
        "raw": json.dumps(structured),
        "file_id": file_id
    })
    db.commit()

    # -------------------------------------------------------
    # 4️⃣ Domain Insert + Display Name Update
    # -------------------------------------------------------
    if doc_type == "admission_form":
        insert_admission_form(db, file_id, structured)
        update_display_name(db, file_id, admission_display_name(structured))

    elif doc_type == "aadhaar":
        doc_id = insert_aadhaar(db, file_id, structured)
        update_display_name(db, file_id, aadhaar_display_name(structured))

        if structured.get("aadhaar_number"):
            run_aadhaar_lookup(db, doc_id)

    elif doc_type == "transfer_certificate":
        doc_id = insert_transfer_certificate(db, file_id, structured)
        update_display_name(db, file_id, tc_display_name(structured))
        run_tc_lookup(db, doc_id)

    elif doc_type == "marksheet":
        doc_id = insert_marksheet(db, file_id, structured)
        update_display_name(db, file_id, highschool_marksheet_display_name(structured))
        run_marksheet_lookup(db, doc_id)

    elif doc_type == "birth_certificate":
        doc_id = insert_birth_certificate(db, file_id, structured)
        update_display_name(db, file_id, birth_certificate_display_name(structured))
        run_bc_lookup(db, doc_id)

    return doc_type


# ==========================================================
# ✅ MAIN THREAD SAFE WORKER LOOP
# ==========================================================
def run():
    db = SessionLocal()

    try:
        print("✅ OCR Worker Started...")

        reset_stuck_jobs(db)

        while True:

            file = claim_next_file(db)

            if not file:
                print("✅ No more pending files.")
                break

            file_id, file_path, extracted_raw, display_name = file
            print(f"🔄 Processing file {file_id}...")

            doc_type = "unknown"

            try:
                # ✅ Process file fully
                doc_type = process_single_file(db, file_id, file_path, extracted_raw)

                # ✅ Finalize success
                db.execute(text(f"""
                    UPDATE uploaded_files
                    SET doc_type = :doc_type,
                        extraction_done = true,
                        extracted_at = {NOW_EXPR},
                        extraction_error = NULL,
                        processing = false
                    WHERE file_id = :file_id
                """), {
                    "doc_type": doc_type,
                    "file_id": file_id
                })

                db.commit()
                print(f"✅ Done file {file_id}")

            except Exception as e:
                db.rollback()

                # ✅ Failure: just save error + release processing
                db.execute(text("""
                    UPDATE uploaded_files
                    SET extraction_error = :err,
                        processing = false
                    WHERE file_id = :file_id
                """), {
                    "err": str(e),
                    "file_id": file_id
                })

                db.commit()
                print(f"❌ Failed file {file_id}: {e}")

    finally:
        db.close()


# ==========================================================
# ✅ ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    run()
