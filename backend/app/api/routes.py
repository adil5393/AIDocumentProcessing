from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Depends, Header
from app.services.amtech import test_connection
from app.services.auth_service import authenticate
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi import APIRouter
from app.ocr.pipeline import run
from fastapi import UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db
import os
import uuid

router = APIRouter(prefix="/api")

class LoginRequest(BaseModel):
    username: str
    password: str


def require_token(authorization: str = Header(None)):
    if authorization != "Bearer fake-token-123":
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/me")
def me(_: str = Depends(require_token)):
    return {"user": "admin"}


UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/ocr/run")
def run_ocr():
    processed = run()
    return {"processed_files": processed}

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
