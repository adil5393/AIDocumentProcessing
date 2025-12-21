from sqlalchemy import text
from app.db.database import SessionLocal
from .google_ocr import process_file
from .extractor import extract_fields
from .doc_classifier import detect_document_type
from .gpt_doc_classifier import gpt_detect_document_type
from app.db.insert_admission_form import insert_admission_form
from app.db.insert_aadhaar import insert_aadhaar
from app.db.insert_transfer_certificate import insert_transfer_certificate
import os
import json

UPLOAD_DIR = "uploads"

def run():
    db = SessionLocal()
    try:
        # 1️⃣ OCR stage
        files = db.execute(text("""
            SELECT file_id, file_path
            FROM uploaded_files
            WHERE ocr_done = false
        """)).fetchall()

        for file_id, file_path in files:
            full_path = os.path.join(UPLOAD_DIR, file_path)

            try:
                ocr_text = process_file(full_path)

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
                db.commit()

            except Exception as e:
                print(f"OCR failed for {file_path}: {e}")

        # 2️⃣ Extraction stage
        files = db.execute(text("""
            SELECT file_id, file_path, ocr_text
            FROM uploaded_files
            WHERE ocr_done = true
              AND extraction_done = false
        """)).fetchall()

        for file_id, file_path, ocr_text in files:
            doc_type = detect_document_type(ocr_text)
            if doc_type == "unknown":
                doc_type = gpt_detect_document_type(ocr_text)

            structured = extract_fields(doc_type, ocr_text)
            

            
            if "error" in structured:
                continue
            db.execute(text("""
                UPDATE uploaded_files
                SET extracted_raw = :raw
                WHERE file_id = :file_id
            """), {
                "raw": json.dumps(structured),
                "file_id": file_id
            })

            try:
                if doc_type == "admission_form":
                    insert_admission_form(db, structured)
                elif doc_type == "aadhaar":
                    insert_aadhaar(db, structured)
                elif doc_type == "transfer_certificate":
                    insert_transfer_certificate(db, structured)

                db.execute(text("""
                    UPDATE uploaded_files
                    SET
                        doc_type = :doc_type,
                        extraction_done = true,
                        extracted_at = now()
                    WHERE file_id = :file_id
                """), {
                    "doc_type": doc_type,
                    "file_id": file_id
                })

                db.commit()

            except Exception as e:
                db.rollback()
                print("Extraction insert failed:", e)

    finally:
        db.close()
        
        
if __name__ == "__main__":
    run()
