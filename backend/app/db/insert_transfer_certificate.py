from sqlalchemy import text

def insert_transfer_certificate(db, file_id, data: dict) -> int:
    result = db.execute(
        text("""
            INSERT INTO transfer_certificates (
                student_name,
                father_name,
                mother_name,
                date_of_birth,
                last_class_studied,
                last_school_name,
                file_id
            )
            VALUES (
                :student_name,
                :father_name,
                :mother_name,
                :date_of_birth,
                :last_class_studied,
                :last_school_name,
                :file_id
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
            "file_id": file_id
        }
    )

    doc_id = result.scalar_one()
    return doc_id
