from fastapi import HTTPException

def post_admission(sr: str,db):
    
    from sqlalchemy import text


    row = db.execute(
        text("""
            SELECT *
            FROM admission_forms
            WHERE sr = :sr
        """),
        {"sr": sr}
    ).mappings().first()

    if not row:
        raise HTTPException(404, f"Admission form not found for SR {sr}")

    # TEMP: return raw DB row
    return {
        "stage": "fetched_admission_form",
        "data": dict(row)
    }