from sqlalchemy import text
from app.db.session import SessionLocal
from app.ocr.google_ocr import process_file
from app.ocr.extractor import extract_fields
from app.ocr.doc_classifier import detect_document_type
from app.ocr.gpt_doc_classifier import gpt_detect_document_type
from app.services.insert_admission_form import insert_admission_form
from app.services.insert_aadhaar import insert_aadhaar
from app.services.insert_transfer_certificate import insert_transfer_certificate
from app.services.insert_marksheet import insert_marksheet
from app.jobs.run_aadhaar_lookup import run_aadhaar_lookup
from app.jobs.run_transfer_certificate_lookup import run_tc_lookup
from app.services.insert_birth_certificate import insert_birth_certificate
import os
import json
from app.ocr.set_file_name import clean, tc_display_name,aadhaar_display_name,admission_display_name,highschool_marksheet_display_name,birth_certificate_display_name
from app.utils.update_display_name import update_display_name

UPLOAD_DIR = "uploads"



def run():
    db = SessionLocal()
    try:
        files = db.execute(text("""
            SELECT file_id, file_path, extracted_raw
            FROM uploaded_files
            WHERE extraction_done = false
            ORDER BY created_at
        """)).fetchall()

        for file_id, file_path, extracted_raw in files:
            full_path = os.path.join(UPLOAD_DIR, file_path)

            try:
                # ------------------
                # 1️⃣ OCR
                # ------------------
                ocr_text = None

                row = db.execute(text("""
                    SELECT ocr_done, ocr_text
                    FROM uploaded_files
                    WHERE file_id = :file_id
                """), {"file_id": file_id}).fetchone()

                if not row.ocr_done:
                    ocr_text = process_file(full_path)
                    print(ocr_text)
                    db.execute(text("""
                        UPDATE uploaded_files
                        SET
                            ocr_text = :ocr_text,
                            ocr_done = true,
                            ocr_at = now()
                        WHERE file_id = :file_id
                    """), {
                        "ocr_text": ocr_text,
                        "file_id": file_id
                    })
                else:
                    ocr_text = row.ocr_text

                # ------------------
                # 2️⃣ Extraction
                # ------------------
                doc_type = detect_document_type(ocr_text)
                if doc_type == "unknown":
                    doc_type = gpt_detect_document_type(ocr_text)
                    
                if extracted_raw:
                    structured = extract_fields(doc_type, extracted_raw)
                else:
                    structured = extract_fields(doc_type, ocr_text)
                    
                print(doc_type)
                print(structured)
                if "error" in structured:
                    raise Exception(structured["error"])

                db.execute(text("""
                    UPDATE uploaded_files
                    SET extracted_raw = :raw
                    WHERE file_id = :file_id
                """), {
                    "raw": json.dumps(structured),
                    "file_id": file_id
                })

                # ------------------
                # 3️⃣ Domain insert
                # ------------------
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
                    update_display_name(db, file_id,highschool_marksheet_display_name(structured))
                    run_tc_lookup(db, doc_id)
                
                elif doc_type == "birth_certificate":
                    doc_id = insert_birth_certificate(db, file_id, structured)
                    update_display_name(db, file_id,birth_certificate_display_name(structured))
                    run_tc_lookup(db, doc_id)
                    
                # ------------------
                # 4️⃣ Finalize
                # ------------------
                db.execute(text("""
                    UPDATE uploaded_files
                    SET
                        doc_type = :doc_type,
                        extraction_done = true,
                        extracted_at = now(),
                        extraction_error = NULL
                    WHERE file_id = :file_id
                """), {
                    "doc_type": doc_type,
                    "file_id": file_id
                })

                db.commit()

            except Exception as e:
                db.rollback()
                db.execute(text("""
                    UPDATE uploaded_files
                    SET extraction_error = :err
                    WHERE file_id = :file_id
                """), {
                    "err": str(e),
                    "file_id": file_id
                })
                db.commit()
                print(f"Failed processing file {file_id}:", e)

    finally:
        db.close()

if __name__ == "__main__":
    run()
