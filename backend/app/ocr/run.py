from sqlalchemy import text
from app.db.database import SessionLocal
from .google_ocr import process_file
from .extractor import extract_fields
from .doc_classifier import detect_document_type
from .gpt_doc_classifier import gpt_detect_document_type
import os
import json

UPLOAD_DIR = "uploads"

def insert_admission_form(db, data):
    db.execute(text("""
        INSERT INTO admission_forms (
            sr,
            class,
            student_name,
            gender,
            date_of_birth,
            father_name,
            mother_name,
            father_occupation,
            mother_occupation,
            address,
            phone1,
            phone2,
            aadhaar_number,
            last_school_attended
        )
        VALUES (
            :sr,
            :class,
            :student_name,
            :gender,
            :date_of_birth,
            :father_name,
            :mother_name,
            :father_occupation,
            :mother_occupation,
            :address,
            :phone1,
            :phone2,
            :aadhaar_number,
            :last_school_attended
        )
    """), {
        "sr": data.get("sr"),
        "class": data.get("class"),
        "student_name": data.get("student_name"),
        "gender": data.get("gender"),
        "date_of_birth": data.get("date_of_birth"),
        "father_name": data.get("father_name"),
        "mother_name": data.get("mother_name"),
        "father_occupation": data.get("father_occupation"),
        "mother_occupation": data.get("mother_occupation"),
        "address": data.get("address"),
        "phone1": data.get("phone1"),
        "phone2": data.get("phone2"),
        "aadhaar_number": data.get("aadhaar_number"),
        "last_school_attended": data.get("last_school_attended"),
    })
    
def insert_aadhaar(db, data: dict):
    db.execute(text("""
        INSERT INTO aadhaar_documents (
            name,
            date_of_birth,
            aadhaar_number,
            relation_type,
            related_name
        )
        VALUES (
            :name,
            :date_of_birth,
            :aadhaar_number,
            :relation_type,
            :related_name
        )
    """), {
        "name": data.get("name"),
        "date_of_birth": data.get("date_of_birth"),
        "aadhaar_number": data.get("aadhaar_number"),
        "relation_type": data.get("relation_type"),
        "related_name": data.get("related_name"),
    })

def insert_transfer_certificate(db, data: dict):
    db.execute(text("""
        INSERT INTO transfer_certificates (
            student_name,
            father_name,
            mother_name,
            date_of_birth,
            last_class_studied,
            last_school_name
        )
        VALUES (
            :student_name,
            :father_name,
            :mother_name,
            :date_of_birth,
            :last_class_studied,
            :last_school_name
        )
    """), {
        "student_name": data.get("student_name"),
        "father_name": data.get("father_name"),
        "mother_name": data.get("mother_name"),
        "date_of_birth": data.get("date_of_birth"),
        "last_class_studied": data.get("last_class_studied"),
        "last_school_name": data.get("last_school_name")
    })


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
