from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Depends, Header
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import APIRouter
from app.ocr.run import run
from fastapi import UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from app.jobs.run_aadhaar_lookup import run_aadhaar_lookup
from typing import Dict, Any
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from io import BytesIO
from fastapi import BackgroundTasks
from typing import List
import threading, json
import mimetypes, time
import os
import uuid
from app.utils.pdftopng import generate_preview_image
from pathlib import Path


DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

router = APIRouter(prefix="/api")

class ReassessPayload(BaseModel):
    extracted_raw: Dict[str, Any]

class LoginRequest(BaseModel):
    username: str
    password: str

class SRDeclareRequest(BaseModel):
    sr_number: str

def require_token(authorization: str = Header(None)):

    if DEV_MODE:
        return

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
            extraction_error,
            extracted_raw,
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
            "extraction_error":r.extraction_error,
            "extracted_raw":r.extracted_raw,
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

UPLOAD_DIR = "uploads"
PREVIEW_DIR = Path(os.getenv("PREVIEW_DIR", "uploads/preview"))

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/ocr/run")
def run_pipeline():
    threading.Thread(target=run, daemon=True).start()
    return {"status": "started"}

@router.post("/upload")
def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),     
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    saved_files = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # 1️⃣ Save original PDF
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        # 2️⃣ Insert DB record
        result = db.execute(
            text("""
                INSERT INTO uploaded_files (file_path, doc_type)
                VALUES (:file_path, :doc_type)
                RETURNING file_id
            """),
            {
                "file_path": filename,
                "doc_type": "unknown"
            }
        )

        file_id = result.scalar_one()

        # 3️⃣ Schedule preview generation (🔥 key part)
        background_tasks.add_task(
            generate_preview_image,
            file_path  # full path to PDF
        )

        saved_files.append({
            "file_id": file_id,
            "original_name": file.filename,
            "saved_as": filename,
            "content_type": file.content_type
        })

    db.commit()

    return {
        "uploaded": len(saved_files),
        "files": saved_files
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

    file_path = os.path.join(UPLOAD_DIR, row.file_path)
    p = Path(row.file_path)
    preview_path = os.path.join(PREVIEW_DIR, f"{p.stem}.jpg")
    print(preview_path)
    
    try:
        # delete file from disk
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(preview_path):
            os.remove(preview_path)

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
            father_aadhaar,
            mother_name,
            mother_aadhaar,
            father_occupation,
            mother_occupation,
            address,
            phone1,
            phone2,
            student_aadhaar_number,
            last_school_attended,
            created_at,
            file_id
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
        "father_aadhaar":r.father_aadhaar,
        "mother_name": r.mother_name,
        "mother_aadhaar":r.mother_aadhaar,
        "father_occupation": r.father_occupation,
        "mother_occupation": r.mother_occupation,
        "address": r.address,
        "phone1": r.phone1,
        "phone2": r.phone2,
        "aadhaar_number": r.student_aadhaar_number,
        "last_school_attended": r.last_school_attended,
        "created_at": r.created_at,
        "file_id": r.file_id
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
            file_id,
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
            "file_id": r.file_id,
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
            file_id,
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
            "file_id":r.file_id,
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

@router.get("/marksheets")
def list_marksheets(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT
            doc_id,
            file_id,
            student_name,
            father_name,
            mother_name,
            date_of_birth,
            lookup_status,
            last_checked_at
        FROM marksheets 
        ORDER BY last_checked_at DESC
    """)).fetchall()

    return [
        {
            "doc_id": r.doc_id,
            "file_id": r.file_id,
            "student_name": r.student_name,
            "father_name": r.father_name,
            "mother_name": r.mother_name,
            "dob": r.date_of_birth,
            "lookup_status": r.lookup_status,
            "last_checked_at": r.last_checked_at,
        }
        for r in rows
    ]

@router.get("/birth-certificates")
def list_marksheets(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT
            doc_id,
            file_id,
            student_name,
            father_name,
            mother_name,
            date_of_birth,
            lookup_status,
            last_checked_at
        FROM birth_certificates 
        ORDER BY last_checked_at DESC
    """)).fetchall()

    return [
        {
            "doc_id": r.doc_id,
            "file_id": r.file_id,
            "student_name": r.student_name,
            "father_name": r.father_name,
            "mother_name": r.mother_name,
            "dob": r.date_of_birth,
            "lookup_status": r.lookup_status,
            "last_checked_at": r.last_checked_at,
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
                tcc.sr,
                af.student_name,
                tcc.total_score,
                tcc.signals
            FROM transfer_certificate_candidates tcc
            JOIN admission_forms af
            ON af.sr = tcc.sr
            WHERE tcc.doc_id = :d
            ORDER BY tcc.total_score DESC
        """),
        {"d": doc_id}
    ).fetchall()

    return [
        {
            "sr": r.sr,
            "student_name":r.student_name,
            "total_score": float(r.total_score),
            "signals": r.signals if isinstance(r.signals, dict)
                       else json.loads(r.signals)
        }
        for r in rows
    ]

@router.get("/marksheets/{doc_id}/candidates")
def get_ms_candidates(
    doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                ms.sr,
                af.student_name,
                ms.total_score,
                ms.signals
            FROM marksheet_candidates ms
            JOIN admission_forms af
            ON af.sr = ms.sr
            WHERE ms.doc_id = :d
            ORDER BY ms.total_score DESC
        """),
        {"d": doc_id}
    ).fetchall()

    return [
        {
            "sr": r.sr,
            "student_name":r.student_name,
            "total_score": float(r.total_score),
            "signals": r.signals if isinstance(r.signals, dict)
                       else json.loads(r.signals)
        }
        for r in rows
    ]

@router.get("/birth-certificates/{doc_id}/candidates")
def get_bc_candidates(
    doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                bc.sr,
                af.student_name,
                bc.total_score,
                bc.signals
            FROM birth_certificate_candidates bc
            JOIN admission_forms af
            ON af.sr = bc.sr
            WHERE bc.doc_id = :d
            ORDER BY bc.total_score DESC
        """),
        {"d": doc_id}
    ).fetchall()

    return [
        {
            "sr": r.sr,
            "student_name":r.student_name,
            "total_score": float(r.total_score),
            "signals": r.signals if isinstance(r.signals, dict)
                       else json.loads(r.signals)
        }
        for r in rows
    ]

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

@router.post("/tc/{doc_id}/lookup")
def rerun_tc_lookup(
    doc_id: int,
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    # 🔒 block if confirmed
    status = db.execute(
        text("""
            SELECT lookup_status
            FROM transfer_certificates
            WHERE doc_id = :d
        """),
        {"d": doc_id}
    ).scalar()
    print(status)
    if status == "Confirmed":
        raise HTTPException(
            status_code=409,
            detail="Lookup already confirmed. Unconfirm before re-running."
        )
    
    from app.jobs.run_transfer_certificate_lookup import run_tc_lookup
    run_tc_lookup(db, doc_id)

    return {"status": "ok"}

@router.post("/tc/lookup/pending")
def run_pending_tc_lookups(
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    from app.jobs.run_transfer_certificate_lookup import run_tc_lookup

    rows = db.execute(
        text("""
            SELECT doc_id
            FROM transfer_certificates
            WHERE lookup_status IS DISTINCT FROM 'Confirmed'
        """)
    ).fetchall()

    for r in rows:
        run_tc_lookup(db, r.doc_id)

    return {"processed_count": len(rows)}

@router.post("/marksheets/{doc_id}/lookup")
def rerun_marksheet_lookup(
    doc_id: int,
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    # 🔒 block if confirmed
    status = db.execute(
        text("""
            SELECT lookup_status
            FROM marksheets
            WHERE doc_id = :d
        """),
        {"d": doc_id}
    ).scalar()
    print(status)
    if status == "Confirmed":
        raise HTTPException(
            status_code=409,
            detail="Lookup already confirmed. Unconfirm before re-running."
        )
    
    from app.jobs.run_marksheet_lookup import run_marksheet_lookup
    run_marksheet_lookup(db, doc_id)

    return {"status": "ok"}

@router.post("/marksheet/lookup/pending")
def run_pending_marksheet_lookups(
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    from app.jobs.run_marksheet_lookup import run_marksheet_lookup

    rows = db.execute(
        text("""
            SELECT doc_id
            FROM marksheets
            WHERE lookup_status IS DISTINCT FROM 'Confirmed'
        """)
    ).fetchall()

    for r in rows:
        run_marksheet_lookup(db, r.doc_id)

    return {"processed_count": len(rows)}

@router.post("/bc/{doc_id}/lookup")
def rerun_bc_lookup(
    doc_id: int,
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    # 🔒 block if confirmed
    status = db.execute(
        text("""
            SELECT lookup_status
            FROM birth_certificates
            WHERE doc_id = :d
        """),
        {"d": doc_id}
    ).scalar()
    print(status)
    if status == "Confirmed":
        raise HTTPException(
            status_code=409,
            detail="Lookup already confirmed. Unconfirm before re-running."
        )
    
    from app.jobs.run_bc_lookup import run_bc_lookup
    run_bc_lookup(db, doc_id)
    return {1:1}
    
@router.post("/bc/lookup/pending")
def run_pending_bc_lookups(
    db = Depends(get_db),
    _: str = Depends(require_token),
):
    from app.jobs.run_bc_lookup import run_bc_lookup

    rows = db.execute(
        text("""
            SELECT doc_id
            FROM birth_certificates
            WHERE lookup_status IS DISTINCT FROM 'Confirmed'
        """)
    ).fetchall()

    for r in rows:
        run_bc_lookup(db, r.doc_id)

    return {"processed_count": len(rows)}

@router.post("/aadhaar/{doc_id}/{sr}/confirm")
def confirm_aadhaar_match(
    doc_id: int,
    payload: dict,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    ROLE_UPDATE_SQL = {
    "student": """
        UPDATE admission_forms af
        SET student_aadhaar_number = ad.aadhaar_number
        FROM aadhaar_documents ad
        WHERE af.sr = :sr
          AND ad.doc_id = :doc_id
          AND af.student_aadhaar_number IS NULL
    """,
    "father": """
        UPDATE admission_forms af
        SET father_aadhaar = ad.aadhaar_number
        FROM aadhaar_documents ad
        WHERE af.sr = :sr
          AND ad.doc_id = :doc_id
          AND af.father_aadhaar IS NULL
    """,
    "mother": """
        UPDATE admission_forms af
        SET mother_aadhaar = ad.aadhaar_number
        FROM aadhaar_documents ad
        WHERE af.sr = :sr
          AND ad.doc_id = :doc_id
          AND af.mother_aadhaar IS NULL
    """,
}
    sr = payload["sr"]
    role = payload["role"]
    score = payload.get("score", 0)
    method = payload.get("method", "manual")

    # 1️⃣ Insert final match
    if role=="student":
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
    elif role in ("mother","father"):
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
                ON CONFLICT (sr_number, aadhaar_doc_id)
                DO UPDATE SET
                    is_confirmed = true,
                    confirmed_on = now()
            """),
            {
                "sr": sr,
                "doc_id": doc_id,
                "role": role,
                "score": int(score * 100),
                "method": method,
            }
        )
        db.execute(
            text("""
                DELETE FROM aadhaar_lookup_candidates
                WHERE doc_id = :doc_id
                AND sr = :sr
            """),
            {
                "doc_id": doc_id,
                "sr": sr,
            }
        )

    # update_sql = ROLE_UPDATE_SQL.get(role)
    # if update_sql:
    #     db.execute(
    #         text(update_sql),
    #         {
    #             "sr": sr,
    #             "doc_id": doc_id,
    #         }
    #     )
    db.commit()
    return {"status": "confirmed"}
    
@router.post("/tc/{doc_id}/confirm")
def confirm_tc_match(
    doc_id: int,
    payload: dict,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    sr = payload["sr"]
    score = payload.get("score", 0)
    method = payload.get("method", "manual_confirm")

    # 1️⃣ Get file_id for cascade safety
    row = db.execute(
        text("""
            SELECT file_id
            FROM transfer_certificates
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    ).fetchone()

    if not row:
        raise HTTPException(404, "Transfer Certificate not found")

    file_id = row.file_id

    # 2️⃣ Insert final TC match
    db.execute(
        text("""
            INSERT INTO tc_matches (
                sr_number,
                tc_doc_id,
                file_id,
                match_score,
                match_method,
                is_confirmed,
                confirmed_on
            )
            VALUES (
                :sr, :doc_id, :file_id, :score, :method, true, now()
            )
        """),
        {
            "sr": sr,
            "doc_id": doc_id,
            "file_id": file_id,
            "score": int(score * 100),
            "method": method,
        }
    )

    # 3️⃣ Delete all TC candidates
    db.execute(
        text("""
            DELETE FROM transfer_certificate_candidates
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    # 4️⃣ Mark TC as confirmed
    db.execute(
        text("""
            UPDATE transfer_certificates
            SET lookup_status = 'Confirmed',
                lookup_checked_at = now()
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    db.commit()
    return {"status": "Confirmed"}

@router.post("/marksheets/{doc_id}/confirm")
def confirm_marksheet_match(
    doc_id: int,
    payload: dict,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    sr = payload["sr"]
    score = payload.get("score", 0)
    method = payload.get("method", "manual_confirm")

    # 1️⃣ Get file_id for cascade safety
    row = db.execute(
        text("""
            SELECT file_id
            FROM marksheets
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    ).fetchone()

    if not row:
        raise HTTPException(404, "Marksheet not found")

    file_id = row.file_id

    # 2️⃣ Insert final marksheet match
    db.execute(
        text("""
            INSERT INTO marksheet_matches (
                sr_number,
                marksheet_doc_id,
                file_id,
                match_score,
                match_method,
                is_confirmed,
                confirmed_on
            )
            VALUES (
                :sr, :doc_id, :file_id, :score, :method, true, now()
            )
        """),
        {
            "sr": sr,
            "doc_id": doc_id,
            "file_id": file_id,
            "score": int(score * 100),
            "method": method,
        }
    )

    # 3️⃣ Delete all marksheet candidates
    db.execute(
        text("""
            DELETE FROM marksheet_candidates
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    # 4️⃣ Mark marksheet as confirmed
    db.execute(
        text("""
            UPDATE marksheets
            SET lookup_status = 'Confirmed',
                lookup_checked_at = now()
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    db.commit()
    return {"status": "Confirmed"}

@router.post("/birth-certificates/{doc_id}/confirm")
def confirm_birth_certificate_match(
    doc_id: int,
    payload: dict,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    sr = payload["sr"]
    score = payload.get("score", 0)
    method = payload.get("method", "manual_confirm")

    # 1️⃣ Get file_id for cascade safety
    row = db.execute(
        text("""
            SELECT file_id
            FROM birth_certificates
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    ).fetchone()

    if not row:
        raise HTTPException(404, "Birth Certificate not found")

    file_id = row.file_id

    # 2️⃣ Insert final birth certificate match
    db.execute(
        text("""
            INSERT INTO birth_certificate_matches (
                sr_number,
                bc_doc_id,
                file_id,
                match_score,
                match_method,
                is_confirmed,
                confirmed_on
            )
            VALUES (
                :sr, :doc_id, :file_id, :score, :method, true, now()
            )
        """),
        {
            "sr": sr,
            "doc_id": doc_id,
            "file_id": file_id,
            "score": int(score * 100),
            "method": method,
        }
    )

    # 3️⃣ Delete all birth certificate candidates
    db.execute(
        text("""
            DELETE FROM birth_certificate_candidates
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    # 4️⃣ Mark birth certificate as confirmed
    db.execute(
        text("""
            UPDATE birth_certificates
            SET lookup_status = 'Confirmed',
                last_checked_at = now()
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    )

    db.commit()
    return {"status": "Confirmed"}

@router.patch("/admission-forms/{sr:path}")
def patch_admission_form(
    sr: str,
    payload: Dict[str, Any],
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    ALLOWED_FIELDS = {
        "sr",
        "student_name",
        "student_aadhaar_number",
        "date_of_birth",
        "father_name",
        "mother_name",
        "phone1",
        "phone2",
        "father_aadhaar",
        "class",
    }

    if not payload:
        raise HTTPException(status_code=400, detail="Empty payload")

    updates = []
    params = {"old_sr": sr}
    
    if "sr" in payload:
        exists = db.execute(
            text("SELECT 1 FROM admission_forms WHERE sr = :sr"),
            {"sr": payload["sr"]}
        ).fetchone()

        if exists:
            raise HTTPException(
                status_code=409,
                detail="SR already exists"
            )

    for field, value in payload.items():
        if field not in ALLOWED_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' cannot be edited"
            )

        if isinstance(value, str):
            value = value.strip()

        if field == "sr":
            updates.append("sr = :new_sr")
            params["new_sr"] = value
        else:
            updates.append(f"{field} = :{field}")
            params[field] = value

    query = f"""
        UPDATE admission_forms
        SET {", ".join(updates)}
        WHERE sr = :old_sr
    """

    result = db.execute(text(query), params)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="SR not found")

    db.commit()

    return {
        "status": "ok",
        "old_sr": sr,
        "new_sr": payload.get("sr", sr),
        "updated_fields": list(payload.keys()),
    }

@router.patch("/transfer-certificates/{doc_id}")
def patch_tc(
    doc_id: int,
    payload: Dict[str, Any],
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    print (payload)
    ALLOWED_FIELDS = {
    "student_name",
    "date_of_birth",
    "father_name",
    "mother_name",
    "last_class_studied",
    "last_school_name"
}
    if not payload:
        raise HTTPException(status_code=400, detail="Empty payload")

    updates = []
    params = {"doc_id": doc_id}

    for field, value in payload.items():
        if field not in ALLOWED_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' cannot be edited"
            )

        # Normalize OCR junk
        if isinstance(value, str):
            value = value.strip()

        updates.append(f"{field} = :{field}")
        params[field] = value

    query = f"""
        UPDATE transfer_certificates
        SET {", ".join(updates)}
        WHERE doc_id = :doc_id
    """

    result = db.execute(text(query), params)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="SR not found")

    db.commit()

    return {
        "status": "ok",
        "doc_id": doc_id,
        "updated_fields": list(payload.keys())
    }

@router.get("/export/student-documents.xlsx")
def export_student_documents(
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    wb = Workbook()
    ws = wb.active
    ws.title = "Student Document Comparison"

    # ---- Header ----
    headers = [
        "SR",
        "Source",
        "Student Name",
        "Father Name",
        "Mother Name",
        "Date of Birth",
        "Aadhaar Number",
    ]
    ws.append(headers)

    # ---- Fetch base SRs ----
    admission_rows = db.execute(text("""
        SELECT
            sr,
            student_name,
            father_name,
            mother_name,
            date_of_birth,
            student_aadhaar_number
        FROM admission_forms
        ORDER BY sr
    """)).fetchall()

    for adm in admission_rows:
        sr = adm.sr

        # =========================
        # 1️⃣ Admission Form row
        # =========================
        ws.append([
            sr,
            "Admission Form",
            adm.student_name,
            adm.father_name,
            adm.mother_name,
            adm.date_of_birth,
            adm.student_aadhaar_number,
        ])

        # =========================
        # 2️⃣ Aadhaar row (always present)
        # =========================
        aadhaar = db.execute(text("""
            SELECT
                d.name,
                d.date_of_birth,
                d.aadhaar_number
            FROM aadhaar_matches m
            JOIN aadhaar_documents d
              ON d.doc_id = m.aadhaar_doc_id
            WHERE m.sr_number = :sr
              AND m.match_role = 'student'
              AND m.is_confirmed = true
            LIMIT 1
        """), {"sr": sr}).fetchone()

        ws.append([
            sr,
            "Aadhaar",
            aadhaar.name if aadhaar else None,
            None,
            None,
            aadhaar.date_of_birth if aadhaar else None,
            aadhaar.aadhaar_number if aadhaar else None,
        ])

        # =========================
        # 3️⃣ Transfer Certificate row (always present)
        # =========================
        tc = db.execute(text("""
            SELECT
                t.student_name,
                t.father_name,
                t.mother_name,
                t.date_of_birth
            FROM tc_matches m
            JOIN transfer_certificates t
              ON t.doc_id = m.tc_doc_id
            WHERE m.sr_number = :sr
              AND m.is_confirmed = true
            LIMIT 1
        """), {"sr": sr}).fetchone()

        ws.append([
            sr,
            "Transfer Certificate",
            tc.student_name if tc else None,
            tc.father_name if tc else None,
            tc.mother_name if tc else None,
            tc.date_of_birth if tc else None,
            None,
        ])

    # ---- Stream Excel file ----
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=student_document_comparison.xlsx"
        },
    )

@router.post("/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "admin":
        return {
            "access_token": "fake-token-123",
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/version")
def version():
    return {"version": "0.1.0"}

@router.post("/files/{file_id}/reassess")
def reassess_file(
    file_id: int,
    payload: ReassessPayload,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    db.execute(text("""
        UPDATE uploaded_files
        SET
            extracted_raw = :raw,
            extraction_error = NULL,
            extraction_done = false
        WHERE file_id = :file_id
    """), {
        "raw": json.dumps(payload.extracted_raw),
        "file_id": file_id
    })

    db.commit()

    return {"status": "ok"}
    
@router.get("/files/{file_id}/preview")
def preview_file(file_id: int, db: Session = Depends(get_db)):

    result = db.execute(
        text("SELECT file_path FROM uploaded_files WHERE file_id = :id"),
        {"id": file_id}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join("uploads", result.file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing")

    def iterfile():
        with open(file_path, "rb") as f:
            yield from f

    return StreamingResponse(
        iterfile(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline"
        }
    )

@router.get("/aadhaar/{aadhaar_doc_id}/matches")
def get_aadhaar_confirmed_matches(
    aadhaar_doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                m.match_id,
                m.sr_number        AS sr,
                a.student_name,
                m.match_role       AS role,
                m.match_score,
                m.match_method,
                m.confirmed_on
            FROM aadhaar_matches m
            JOIN admission_forms a ON a.sr = m.sr_number
            WHERE m.aadhaar_doc_id = :aadhaar_doc_id
              AND m.is_confirmed = true
            ORDER BY m.confirmed_on ASC
        """),
        {"aadhaar_doc_id": aadhaar_doc_id},
    ).mappings().all()

    return rows

@router.get("/transfer-certificates/{tc_doc_id}/matches")
def get_tc_confirmed_matches(
    tc_doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                m.id                AS match_id,
                m.sr_number         AS sr,
                a.student_name,
                a.father_name,
                a.mother_name,
                a.date_of_birth,
                m.match_score,
                m.match_method,
                m.confirmed_on
            FROM tc_matches m
            LEFT JOIN admission_forms a
                   ON a.sr = m.sr_number
            WHERE m.tc_doc_id = :tc_doc_id
              AND m.is_confirmed = TRUE
            ORDER BY m.confirmed_on ASC
        """),
        {"tc_doc_id": tc_doc_id},
    ).mappings().all()

    return [
        {
            "match_id": r["match_id"],
            "sr": r["sr"],
            "student_name": r["student_name"],
            "father_name": r["father_name"],
            "mother_name": r["mother_name"],
            "date_of_birth": (
                r["date_of_birth"].isoformat()
                if r["date_of_birth"] else None
            ),
            "match_score": r["match_score"],
            "match_method": r["match_method"],
            "confirmed_on": (
                r["confirmed_on"].isoformat()
                if r["confirmed_on"] else None
            ),
        }
        for r in rows
    ]

@router.get("/marksheets/{doc_id}/matches")
def get_marksheet_confirmed_matches(
    doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                m.id                AS match_id,
                m.sr_number         AS sr,
                a.student_name,
                a.father_name,
                a.mother_name,
                a.date_of_birth,
                m.match_score,
                m.match_method,
                m.confirmed_on
            FROM marksheet_matches m
            LEFT JOIN admission_forms a
                   ON a.sr = m.sr_number
            WHERE m.marksheet_doc_id = :doc_id
              AND m.is_confirmed = TRUE
            ORDER BY m.confirmed_on ASC
        """),
        {"doc_id": doc_id},
    ).mappings().all()

    return [
        {
            "match_id": r["match_id"],
            "sr": r["sr"],
            "student_name": r["student_name"],
            "father_name": r["father_name"],
            "mother_name": r["mother_name"],
            "date_of_birth": (
                r["date_of_birth"].isoformat()
                if r["date_of_birth"] else None
            ),
            "match_score": r["match_score"],
            "match_method": r["match_method"],
            "confirmed_on": (
                r["confirmed_on"].isoformat()
                if r["confirmed_on"] else None
            ),
        }
        for r in rows
    ]

@router.get("/birth-certificates/{doc_id}/matches")
def get_marksheet_confirmed_matches(
    doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("""
            SELECT
                bc.id                AS match_id,
                bc.sr_number         AS sr,
                a.student_name,
                a.father_name,
                a.mother_name,
                a.date_of_birth,
                bc.match_score,
                bc.match_method,
                bc.confirmed_on
            FROM birth_certificate_matches bc
            LEFT JOIN admission_forms a
                   ON a.sr = bc.sr_number
            WHERE bc.bc_doc_id = :doc_id
              AND bc.is_confirmed = TRUE
            ORDER BY bc.confirmed_on ASC
        """),
        {"doc_id": doc_id},
    ).mappings().all()

    return [
        {
            "match_id": r["match_id"],
            "sr": r["sr"],
            "student_name": r["student_name"],
            "father_name": r["father_name"],
            "mother_name": r["mother_name"],
            "date_of_birth": (
                r["date_of_birth"].isoformat()
                if r["date_of_birth"] else None
            ),
            "match_score": r["match_score"],
            "match_method": r["match_method"],
            "confirmed_on": (
                r["confirmed_on"].isoformat()
                if r["confirmed_on"] else None
            ),
        }
        for r in rows
    ]

@router.delete("/aadhaar/{sr:path}/{aadhaar_doc_id}/delete-match")
def delete_aadhaar_match(
    sr: str,
    aadhaar_doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    # 1️⃣ Verify match exists
    row = db.execute(
        text("""
            SELECT match_id
            FROM aadhaar_matches
            WHERE sr_number = :sr
              AND aadhaar_doc_id = :aadhaar_doc_id
              AND is_confirmed = TRUE
        """),
        {
            "sr": sr,
            "aadhaar_doc_id": aadhaar_doc_id,
        },
    ).first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Confirmed Aadhaar match not found"
        )

    # 2️⃣ Delete ONLY this match
    db.execute(
        text("""
            DELETE FROM aadhaar_matches
            WHERE sr_number = :sr
              AND aadhaar_doc_id = :aadhaar_doc_id
        """),
        {
            "sr": sr,
            "aadhaar_doc_id": aadhaar_doc_id,
        },
    )

    # 3️⃣ Reset lookup status for this Aadhaar doc
    db.execute(
        text("""
            UPDATE aadhaar_documents
            SET lookup_status = 'no_match'
            WHERE doc_id = :aadhaar_doc_id
        """),
        {"aadhaar_doc_id": aadhaar_doc_id},
    )

    db.commit()

    return {
        "status": "ok",
        "sr": sr,
        "aadhaar_doc_id": aadhaar_doc_id,
        "new_status": "no_match",
    }

@router.delete("/transfer-certificates/{sr:path}/{tc_doc_id}/delete-match")
def delete_tc_match(
    sr: str,
    tc_doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    print(sr, tc_doc_id)

    # 1️⃣ Verify confirmed match exists
    row = db.execute(
        text("""
            SELECT id
            FROM tc_matches
            WHERE sr_number = :sr
              AND tc_doc_id = :tc_doc_id
              AND is_confirmed = TRUE
        """),
        {"sr": sr, "tc_doc_id": tc_doc_id},
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="TC match not found")

    # 2️⃣ Delete ONLY this match
    db.execute(
        text("""
            DELETE FROM tc_matches
            WHERE sr_number = :sr
              AND tc_doc_id = :tc_doc_id
        """),
        {"sr": sr, "tc_doc_id": tc_doc_id},
    )

    # 3️⃣ Reset lookup status for this TC document
    db.execute(
        text("""
            UPDATE transfer_certificates
            SET lookup_status = 'no_match'
            WHERE doc_id = :tc_doc_id
        """),
        {"tc_doc_id": tc_doc_id},
    )

    db.commit()

    return {
        "status": "ok",
        "sr": sr,
        "tc_doc_id": tc_doc_id,
        "new_status": "no_match",
    }

@router.delete("/marksheets/{sr:path}/{doc_id}/delete-match")
def delete_marksheet_match(
    sr: str,
    doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    print(sr, doc_id)

    # 1️⃣ Verify confirmed match exists
    row = db.execute(
        text("""
            SELECT id
            FROM marksheet_matches
            WHERE sr_number = :sr
              AND marksheet_doc_id = :doc_id
              AND is_confirmed = TRUE
        """),
        {"sr": sr, "doc_id": doc_id},
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Marksheet match not found")

    # 2️⃣ Delete ONLY this match
    db.execute(
        text("""
            DELETE FROM marksheet_matches
            WHERE sr_number = :sr
              AND marksheet_doc_id = :doc_id
        """),
        {"sr": sr, "doc_id": doc_id},
    )

    # 3️⃣ Reset lookup status for this marksheet document
    db.execute(
        text("""
            UPDATE marksheets
            SET lookup_status = 'no_match',
                lookup_checked_at = now()
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id},
    )

    db.commit()

    return {
        "status": "ok",
        "sr": sr,
        "doc_id": doc_id,
        "new_status": "no_match",
    }

@router.delete("/birth-certificates/{sr:path}/{bc_doc_id}/delete-match")
def delete_bc_match(
    sr: str,
    bc_doc_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    print(sr, bc_doc_id)

    # 1️⃣ Verify confirmed match exists
    row = db.execute(
        text("""
            SELECT id
            FROM birth_certificate_matches
            WHERE sr_number = :sr
              AND bc_doc_id = :bc_doc_id
              AND is_confirmed = TRUE
        """),
        {"sr": sr, "bc_doc_id": bc_doc_id},
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="BC match not found")

    # 2️⃣ Delete ONLY this match
    db.execute(
        text("""
            DELETE FROM birth_certificate_matches
            WHERE sr_number = :sr
              AND bc_doc_id = :bc_doc_id
        """),
        {"sr": sr, "bc_doc_id": bc_doc_id},
    )

    # 3️⃣ Reset lookup status for this TC document
    db.execute(
        text("""
            UPDATE birth_certificates
            SET lookup_status = 'no_match'
            WHERE doc_id = :bc_doc_id
        """),
        {"bc_doc_id": bc_doc_id},
    )

    db.commit()

    return {
        "status": "ok",
        "sr": sr,
        "bc_doc_id": bc_doc_id,
        "new_status": "no_match",
    }

@router.get("/files/{file_id}/preview-image")
def preview_image(
    file_id: int,
    _: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    print(file_id)
    row = db.execute(
        text("""
            SELECT file_path
            FROM uploaded_files
            WHERE file_id = :id
        """),
        {"id": file_id}
    ).fetchone()

    if not row:
        raise HTTPException(404, "File not found")

    pdf_name = Path(row.file_path)
    preview_path = PREVIEW_DIR / f"{pdf_name.stem}.jpg"

    if not preview_path.exists():
        raise HTTPException(404, "Preview not generated")

    return FileResponse(preview_path, media_type="image/jpeg")

@router.get("/students/crossreview")
def students_overview(
    _: str = Depends(require_token),
    db: Session = Depends(get_db),
):
    sql = text("""
        SELECT
            a.sr,
            a.student_name                  AS admission_name,

            -- Aadhaar
            ad.name                         AS aadhaar_name,
            am.is_confirmed                 AS aadhaar_confirmed,

            -- Transfer Certificate
            tc.student_name                 AS tc_name,
            tm.is_confirmed                 AS tc_confirmed,

            -- Marksheet
            ms.student_name                 AS marksheet_name,
            mm.is_confirmed                 AS marksheet_confirmed,

            -- Birth Certificate
            bc.student_name                 AS birth_certificate_name,
            bcm.is_confirmed                AS birth_certificate_confirmed

        FROM admission_forms a

        /* Aadhaar */
        LEFT JOIN aadhaar_matches am
            ON am.sr_number = a.sr
           AND am.is_confirmed = true
           AND am.match_role = 'student'

        LEFT JOIN aadhaar_documents ad
            ON ad.doc_id = am.aadhaar_doc_id

        /* Transfer Certificate */
        LEFT JOIN tc_matches tm
            ON tm.sr_number = a.sr
           AND tm.is_confirmed = true

        LEFT JOIN transfer_certificates tc
            ON tc.doc_id = tm.tc_doc_id

        /* Marksheet */
        LEFT JOIN marksheet_matches mm
            ON mm.sr_number = a.sr
           AND mm.is_confirmed = true

        LEFT JOIN marksheets ms
            ON ms.doc_id = mm.marksheet_doc_id

        /* Birth Certificate */
        LEFT JOIN birth_certificate_matches bcm
            ON bcm.sr_number = a.sr
           AND bcm.is_confirmed = true

        LEFT JOIN birth_certificates bc
            ON bc.doc_id = bcm.bc_doc_id

        ORDER BY a.created_at DESC
    """)

    rows = db.execute(sql).mappings().all()
    return rows


@router.get("/amtech/status")
def amtech_status(_: str = Depends(require_token)):
    from app.integrations.amtech_runtime import ensure_amtech_connection

    state = ensure_amtech_connection()

    return {
        "connected": state["connected"],
        "user_id": state["user_id"],
        "branches": state["branches"],
        "expires_at": state["expiry"],
        "expires_in_seconds": int(state["expiry"] - time.time())
    }  
@router.post("/amtech/reconnect")
def reconnect(_: str = Depends(require_token)):
    from app.integrations.amtech_auth import authenticate
    authenticate()
    return {"status": "reconnected"}

@router.get("/amtech/masters")
def get_amtech_masters(_: str = Depends(require_token)):
    from app.integrations.amtech_masters import get_amtech_masters_internal
    return get_amtech_masters_internal()

from fastapi import Body
@router.post("/amtech/dummy-post")
def dummy_post(confirm: bool = False, _: str = Depends(require_token),  body: dict = Body(default={})):
    import time
    import os
    from fastapi import HTTPException
    from app.integrations.amtech_auth import load_token
    from app.integrations.amtech_client import amtech_post
    from app.integrations.amtech_masters import get_amtech_masters_internal
    from app.integrations.build_admission_payload import build_dummy_admission_payload

    # 🔐 Extra safety (recommended)
    if confirm and os.getenv("ALLOW_DUMMY_POST") != "true":
        raise HTTPException(403, "Dummy posting is disabled")

    # 1. Get masters snapshot
    masters = get_amtech_masters_internal()

    # 2. Build dummy payload
    payload = build_dummy_admission_payload(masters)

    # 3. Dry run (default)
    if not confirm:
        return {
            "mode": "dry-run",
            "payload": payload
        }

    # 4. REAL POST (only if confirm=true)
    token, _, _, _ = load_token()

    response = amtech_post(
        "/api/v1/sms/student",
        token,
        payload
    )

    return {
        "mode": "posted",
        "response": response
    }
