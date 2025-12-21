from sqlalchemy import text

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