from sqlalchemy import text
import hashlib
import json

def compute_marksheet_hash(data: dict) -> str:
    canonical = {
        "student_name": (data.get("student_name") or "").strip().lower(),
        "father_name": (data.get("father_name") or "").strip().lower(),
        "mother_name": (data.get("mother_name") or "").strip().lower(),
        "date_of_birth": str(data.get("date_of_birth") or data.get("date_of_birth") or ""),
        "result_status": (data.get("result_status") or "").strip().lower(),
    }

    blob = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def insert_marksheet(db, file_id: int, data: dict) -> int:
    content_hash = compute_marksheet_hash(data)

    result = db.execute(
        text("""
            INSERT INTO marksheets (
                student_name,
                father_name,
                mother_name,
                date_of_birth,
                result_status,
                file_id,
                content_hash
            )
            VALUES (
                :student_name,
                :father_name,
                :mother_name,
                :date_of_birth,
                :result_status,
                :file_id,
                :content_hash
            )
            RETURNING doc_id
        """),
        {
            "student_name": data.get("student_name"),
            "father_name": data.get("father_name"),
            "mother_name": data.get("mother_name"),
            # handle both key styles safely
            "date_of_birth": data.get("date_of_birth") or data.get("date_of_birth"),
            "result_status": data.get("result_status"),
            "file_id": file_id,
            "content_hash": content_hash,
        }
    )

    row = result.fetchone()
    if not row:
        raise RuntimeError("Failed to insert marksheet")

    doc_id = row.doc_id
    db.commit()
    return doc_id
