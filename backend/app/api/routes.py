from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Depends, Header
from app.services.amtech import test_connection
from app.services.auth_service import authenticate
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import APIRouter
from app.ocr.run import run
from fastapi import UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from app.db.aadhaar_lookup import run_aadhaar_lookup

import threading, json

import os
import uuid

router = APIRouter(prefix="/api")

class LoginRequest(BaseModel):
    username: str
    password: str

class SRDeclareRequest(BaseModel):
    sr_number: str


def require_token(authorization: str = Header(None)):
    if authorization != "Bearer fake-token-123":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/me")
def me(_: str = Depends(require_token)):
    return {"user": "admin"}

@router.get("/files")
def list_files(
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            file_id,
            file_path,
            doc_type,
            ocr_done,
            extraction_done,
            display_name
        FROM uploaded_files
        ORDER BY created_at DESC
    """)).fetchall()

    return [
        {
            "file_id": r.file_id,
            "file_path": r.file_path,
            "doc_type": r.doc_type,
            "ocr_done": r.ocr_done,
            "extraction_done": r.extraction_done,
            "display_name":r.display_name
        }
        for r in rows
    ]


@router.get("/reserved")
async def get_reserved_srs(
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            sr_number,
            branch_id,
            reserved_by,
            expires_at
        FROM sr_registry
        WHERE status = 'reserved'
        
        ORDER BY expires_at
    """)).fetchall()

    return [
        {
            "sr_number": r.sr_number,
            "branch_id": r.branch_id,
            "reserved_by": r.reserved_by,
            "expires_at": r.expires_at
        }
        for r in rows
    ]

@router.post("/declare")
def declare_sr(
    payload: SRDeclareRequest,
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    sr = payload.sr_number.strip().upper()

    try:
        db.execute(
            text("""
                INSERT INTO sr_registry (
                    sr_number,
                    branch_id,
                    reserved_by,
                    status
                )
                VALUES (
                    :sr_number,
                    :branch_id,
                    :reserved_by,
                    'reserved'
                )
            """),
            {
                "sr_number": sr,
                # TODO: replace these with real values when auth is ready
                "branch_id": 1,
                "reserved_by": 1
            }
        )

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"SR {sr} is already reserved or confirmed"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    return {
        "message": f"SR {sr} reserved successfully",
        "sr_number": sr
    }
@router.delete("/cleanup")
def cleanup_expired_srs(
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                DELETE FROM sr_registry
                WHERE status = 'reserved'
                AND expires_at < now()
            """)
        )

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    return {
        "message": "Expired SRs cleaned up",
        "deleted_count": result.rowcount
    }
@router.post("/aadhaar/{doc_id}/lookup")
def aadhaar_lookup(
    
    doc_id: int,
    force: bool = False,   # 👈 important
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    row = db.execute(
        text("""
            SELECT lookup_status
            FROM aadhaar_documents
            WHERE doc_id = :doc_id
            AND lookup_status NOT IN ('single_match', 'confirmed');
        """),
        {"doc_id": doc_id}
    ).fetchone()

    if not row:
        raise HTTPException(404, "Aadhaar document not found")

    if row.lookup_status != "pending" and not force:
        return {
            "status": row.lookup_status,
            "message": "Lookup already completed. Use force=true to re-run."
        }

    result = run_aadhaar_lookup(db, doc_id)
    return result

@router.post("/aadhaar/lookup/pending")
def run_pending_aadhaar_lookups(
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    
    rows = db.execute(
        text("""
    SELECT doc_id
    FROM aadhaar_documents
    where lookup_status not in ('single match','confirmed')
""")
    ).fetchall()
    processed = 0
    for r in rows:
        try:
            run_aadhaar_lookup(db, r.doc_id)
            processed += 1
        except Exception as e:
            # do NOT crash whole batch
            print (e)
            continue

    return {
        "message": "Pending Aadhaar lookups processed",
        "processed_count": processed
    }   
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/ocr/run")
def run_pipeline():
    threading.Thread(target=run, daemon=True).start()
    return {"status": "started"}

@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # infer doc_type later if needed
    doc_type = "unknown"

    db.execute(
        text("""
            INSERT INTO uploaded_files (file_path, doc_type)
            VALUES (:file_path, :doc_type)
        """),
        {"file_path": filename, "doc_type": doc_type}
    )
    db.commit()

    return {
        "original_name": file.filename,
        "saved_as": filename,
        "content_type": file.content_type,
    }

@router.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    row = db.execute(text("""
        SELECT file_path, extraction_done
        FROM uploaded_files
        WHERE file_id = :file_id
    """), {"file_id": file_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    # if row.extraction_done:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Cannot delete file after extraction"
    #     )

    file_path = os.path.join("uploads", row.file_path)

    try:
        # delete file from disk
        if os.path.exists(file_path):
            os.remove(file_path)

        # delete DB row
        db.execute(text("""
            DELETE FROM uploaded_files
            WHERE file_id = :file_id
        """), {"file_id": file_id})

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "deleted"}

@router.get("/admission-forms")
def list_admission_forms(
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            sr,
            class AS class_name,
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
            created_at
        FROM admission_forms
        ORDER BY created_at DESC
    """)).fetchall()

    return [
    {
        "sr": r.sr,
        "class": r.class_name,
        "student_name": r.student_name,
        "gender": r.gender,
        "date_of_birth": r.date_of_birth,
        "father_name": r.father_name,
        "mother_name": r.mother_name,
        "father_occupation": r.father_occupation,
        "mother_occupation": r.mother_occupation,
        "address": r.address,
        "phone1": r.phone1,
        "phone2": r.phone2,
        "aadhaar_number": r.student_aadhaar_number,
        "last_school_attended": r.last_school_attended,
        "created_at": r.created_at,
    }
    for r in rows
]

@router.get("/aadhaar-documents")
def list_aadhaar_documents(
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            doc_id,
            name,
            date_of_birth,
            aadhaar_number,
            relation_type,
            related_name,
            lookup_status,
            lookup_checked_at,
            created_at
        FROM aadhaar_documents
        ORDER BY created_at DESC
    """)).fetchall()

    return [
        {
            "doc_id": r.doc_id,
            "name": r.name,
            "date_of_birth": r.date_of_birth,
            "aadhaar_number": r.aadhaar_number,
            "relation_type": r.relation_type,
            "related_name": r.related_name,
            "lookup_status": r.lookup_status,
            "lookup_checked_at":r.lookup_checked_at,
            "created_at": r.created_at,
        }
        for r in rows
    ]

@router.get("/transfer-certificates")
def list_transfer_certificates(
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    rows = db.execute(text("""
        SELECT
            doc_id,
            student_name,
            father_name,
            mother_name,
            date_of_birth,
            lookup_status,
            last_class_studied,
            last_school_name,
            created_at
        FROM transfer_certificates
        ORDER BY created_at DESC
    """)).fetchall()

    return [
        {
            "doc_id": r.doc_id,
            "student_name": r.student_name,
            "father_name": r.father_name,
            "mother_name": r.mother_name,
            "date_of_birth": r.date_of_birth,
            "lookup_status":r.lookup_status,
            "last_class_studied": r.last_class_studied,
            "last_school_name": r.last_school_name,
            "created_at": r.created_at,
        }
        for r in rows
    ]

@router.get("/uploads")
def list_uploads(_: str = Depends(require_token)):
    files = []

    if not os.path.exists(UPLOAD_DIR):
        return files

    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)

        if os.path.isfile(file_path):
            files.append({
                "filename": filename,
                "size": os.path.getsize(file_path)
            })

    return files

@router.get("/uploads/{filename}")
def get_uploaded_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)

@router.get("/aadhaar/{doc_id}/candidates")
def get_aadhaar_candidates(
    doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    try:
        rows = db.execute(
            text("""
                SELECT
                    sr,
                    role,
                    student_name,
                    total_score,
                    signals
                FROM aadhaar_lookup_candidates
                WHERE doc_id = :d
                ORDER BY total_score DESC
            """),
            {"d": doc_id}
        ).fetchall()

        return [
            {
                "sr": r.sr,
                "role": r.role,
                "student_name":r.student_name,
                "total_score": float(r.total_score),
                "signals": r.signals if isinstance(r.signals, dict)
                           else json.loads(r.signals)
            }
            for r in rows
        ]

    finally:
        db.close()

@router.get("/tc/{doc_id}/candidates")
def get_tc_candidates(
    doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                sr,
                total_score,
                signals
            FROM transfer_certificate_candidates
            WHERE doc_id = :d
            ORDER BY total_score DESC
        """),
        {"d": doc_id}
    ).fetchall()

    return [
        {
            "sr": r.sr,
            "total_score": float(r.total_score),
            "signals": r.signals if isinstance(r.signals, dict)
                       else json.loads(r.signals)
        }
        for r in rows
    ]

@router.post("/tc/{doc_id}/lookup")
def rerun_tc_lookup(
    doc_id: int,
    force: bool = True,
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    from app.db.transfer_certificate_lookup import run_tc_lookup

    if force:
        db.execute(
            text("""
                UPDATE transfer_certificates
                SET lookup_status = 'pending',
                    lookup_checked_at = NULL
                WHERE doc_id = :d
            """),
            {"d": doc_id}
        )
        db.commit()

    run_tc_lookup(db, doc_id)
    return {"status": "ok"}

@router.post("/tc/lookup/pending")
def run_pending_tc_lookups(
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    from app.db.transfer_certificate_lookup import run_tc_lookup

    rows = db.execute(
        text("""
            SELECT doc_id
            FROM transfer_certificates
            WHERE lookup_status IS DISTINCT FROM 'single_match'
        """)
    ).fetchall()

    for r in rows:
        run_tc_lookup(db, r.doc_id)

    return {"processed_count": len(rows)}

@router.post("/aadhaar/{doc_id}/confirm")
def confirm_aadhaar_match(
    doc_id: int,
    payload: dict,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    sr = payload["sr"]
    role = payload["role"]
    score = payload.get("score", 0)
    method = payload.get("method", "manual")

    # 1️⃣ Insert final match
    db.execute(
        text("""
            INSERT INTO aadhaar_matches (
                sr_number,
                aadhaar_doc_id,
                match_role,
                match_score,
                match_method,
                is_confirmed,
                confirmed_on
            )
            VALUES (
                :sr, :doc_id, :role, :score, :method, true, now()
            )
        """),
        {
            "sr": sr,
            "doc_id": doc_id,
            "role": role,
            "score": int(score * 100),  # normalize
            "method": method,
        }
    )

    # 2️⃣ Remove all candidates for this Aadhaar doc
    db.execute(
        text("""
            DELETE FROM aadhaar_lookup_candidates
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    # 3️⃣ Update Aadhaar document status
    db.execute(
        text("""
            UPDATE aadhaar_documents
            SET lookup_status = 'confirmed',
                lookup_checked_at = now()
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    db.commit()
    return {"status": "confirmed"}


@router.post("/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "admin":
        return {
            "access_token": "fake-token-123",
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/service-token")
def get_service_token():
    token = authenticate()
    return {"token": token}

@router.get("/status")
def status():
    return {"status": "ok"}


@router.get("/token-test")
def token_test():
    return test_connection()


# @router.post("/upload")
# async def upload(files: list[UploadFile]):
#     filenames = [f.filename for f in files]
#     return {"received": filenames, "count": len(files)}

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/version")
def version():
    return {"version": "0.1.0"}
