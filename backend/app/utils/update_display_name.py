from sqlalchemy import text

def update_display_name(db, file_id: int, display_name: str):
    db.execute(
        text("""
            UPDATE uploaded_files
            SET display_name = :dn
            WHERE file_id = :fid
        """),
        {"dn": display_name, "fid": file_id}
    )