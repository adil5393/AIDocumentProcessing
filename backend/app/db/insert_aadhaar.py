from sqlalchemy import text


def insert_aadhaar(db,file_id, data: dict) -> int:
    """
    Inserts Aadhaar document and returns doc_id.
    lookup_status starts as 'pending' by default.
    """

    result = db.execute(
        text("""
            INSERT INTO aadhaar_documents (
                name,
                date_of_birth,
                aadhaar_number,
                relation_type,
                related_name,
                lookup_status,
                lookup_checked_at,
                file_id
            )
            VALUES (
                :name,
                :date_of_birth,
                :aadhaar_number,
                :relation_type,
                :related_name,
                'pending',
                NULL,
                :file_id
            )
            RETURNING doc_id
        """),
        {
            "name": data.get("name"),
            "date_of_birth": data.get("date_of_birth"),
            "aadhaar_number": data.get("aadhaar_number"),
            "relation_type": data.get("relation_type"),
            "related_name": data.get("related_name"),
            "file_id":file_id
        }
    )

    doc_id = result.fetchone().doc_id
    db.commit()
    return doc_id
