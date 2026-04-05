from sqlalchemy import text
import hashlib
import json

def compute_tc_hash(data: dict) -> str:
    canonical = {
        "student_name": (data.get("student_name") or "").strip().lower(),
        "father_name": (data.get("father_name") or "").strip().lower(),
        "mother_name": (data.get("mother_name") or "").strip().lower(),
        "date_of_birth": str(data.get("date_of_birth") or ""),
        "last_class_studied": (data.get("last_class_studied") or "").strip().lower(),
        "last_school_name": (data.get("last_school_name") or "").strip().lower(),
    }

    blob = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()

def insert_transfer_certificate(db, file_id, data: dict) -> int:
    content_hash = compute_tc_hash(data)

    # 1️⃣ Try insert
    result = db.execute(
        text("""
            INSERT INTO transfer_certificates (
                student_name,
                father_name,
                mother_name,
                date_of_birth,
                last_class_studied,
                last_school_name,
                file_id,
                content_hash
            )
            VALUES (
                :student_name,
                :father_name,
                :mother_name,
                :date_of_birth,
                :last_class_studied,
                :last_school_name,
                :file_id,
                :content_hash
            )
            RETURNING doc_id
        """),
        {
            "student_name": data.get("student_name"),
            "father_name": data.get("father_name"),
            "mother_name": data.get("mother_name"),
            "date_of_birth": data.get("date_of_birth"),
            "last_class_studied": data.get("last_class_studied"),
            "last_school_name": data.get("last_school_name"),
            "file_id": file_id,
            "content_hash": content_hash,
        }
    )

    row = result.fetchone()
    if row:
        doc_id = row.doc_id
    db.commit()
    return doc_id
