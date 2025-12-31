from sqlalchemy import text
import hashlib
import json


def compute_birth_certificate_hash(data: dict) -> str:
    canonical = {
        "student_name": (data.get("student_name") or "").strip().lower(),
        "father_name": (data.get("father_name") or "").strip().lower(),
        "mother_name": (data.get("mother_name") or "").strip().lower(),
        "dob": str(data.get("dob") or data.get("date_of_birth") or ""),
        "place_of_birth": (data.get("place_of_birth") or "").strip().lower(),
    }

    blob = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def insert_birth_certificate(db, file_id: int, data: dict) -> int:
    content_hash = compute_birth_certificate_hash(data)
    print(data)
    result = db.execute(
        text("""
            INSERT INTO birth_certificates (
                student_name,
                father_name,
                mother_name,
                dob,
                place_of_birth,
                file_id,
                content_hash
            )
            VALUES (
                :student_name,
                :father_name,
                :mother_name,
                :dob,
                :place_of_birth,
                :file_id,
                :content_hash
            )
            RETURNING doc_id
        """),
        {
            "student_name": data.get("student_name"),
            "father_name": data.get("father_name"),
            "mother_name": data.get("mother_name"),
            "dob": data.get("dob") or data.get("date_of_birth"),
            "place_of_birth": data.get("place_of_birth"),
            "file_id": file_id,
            "content_hash": content_hash,
        }
    )

    row = result.fetchone()
    if not row:
        raise RuntimeError("Failed to insert birth certificate")

    doc_id = row.doc_id
    db.commit()
    return doc_id
