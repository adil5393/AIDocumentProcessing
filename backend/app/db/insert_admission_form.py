from sqlalchemy import text
from fastapi import HTTPException


def insert_admission_form(db,file_id, data):
    sr = data.get("sr")
    if not sr:
        raise HTTPException(status_code=400, detail="SR missing in extracted data")

    sr = sr.strip().upper()

    try:
        # 1️⃣ Check SR in sr_registry
        sr_row = db.execute(
            text("""
                SELECT status
                FROM sr_registry
                WHERE sr_number = :sr
            """),
            {"sr": sr}
        ).fetchone()

        if not sr_row:
            db.execute(text("""
                    UPDATE uploaded_files
                    SET extraction_error = :err
                    WHERE file_id = :file_id
                """), {
                    "err": "No Sr",
                    "file_id": file_id
                })
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"SR {sr} not declared in system"
            )

        sr_status = sr_row.status

        # 2️⃣ Check if admission already exists
        admission_exists = db.execute(
            text("""
                SELECT 1
                FROM admission_forms
                WHERE sr = :sr
            """),
            {"sr": sr}
        ).fetchone()

        # 3️⃣ Decision tree
        if sr_status == "reserved":
            if admission_exists:
                raise HTTPException(
                    status_code=409,
                    detail=f"Admission already exists for SR {sr}"
                )

            # Insert admission
            db.execute(text("""
                INSERT INTO admission_forms (
                    sr,
                    class,
                    student_name,
                    gender,
                    date_of_birth,
                    spen,
                    father_name,
                    mother_name,
                    father_occupation,
                    father_aadhaar,
                    mother_occupation,
                    mother_aadhaar,
                    address,
                    phone1,
                    phone2,
                    student_aadhaar_number,
                    last_school_attended,
                    file_id
                )
                VALUES (
                    :sr,
                    :class,
                    :student_name,
                    :gender,
                    :date_of_birth,
                    :spen
                    :father_name,
                    :mother_name,
                    :father_occupation,
                    :father_aadhaar,
                    :mother_occupation,
                    :mother_aadhaar,
                    :address,
                    :phone1,
                    :phone2,
                    :student_aadhaar_number,
                    :last_school_attended
                    :file_id
                )
            """), {
                **data,
                "sr": sr,
                "file_id":file_id
            })

            # Confirm SR
            db.execute(
                text("""
                    UPDATE sr_registry
                    SET status = 'confirmed',
                        confirmed_at = now()
                    WHERE sr_number = :sr
                      AND status = 'reserved'
                """),
                {"sr": sr}
            )

        elif sr_status == "confirmed":
            if admission_exists:
                raise HTTPException(
                    status_code=409,
                    detail=f"Admission already exists for SR {sr}"
                )

            # Backfill case: SR already confirmed historically
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
                    student_aadhaar_number,
                    last_school_attended,
                    file_id
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
                    :student_aadhaar_number,
                    :last_school_attended,
                    :file_id
                )
            """), {
                **data,
                "sr": sr,
                "file_id":file_id
            })

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid SR status for {sr}"
            )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
