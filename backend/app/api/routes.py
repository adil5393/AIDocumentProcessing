from fastapi import APIRouter, UploadFile, File
from app.services.amtech import test_connection

router = APIRouter(prefix="/api")


@router.get("/status")
def status():
    return {"status": "ok"}


@router.get("/token-test")
def token_test():
    return test_connection()


@router.post("/upload")
async def upload(files: list[UploadFile]):
    filenames = [f.filename for f in files]
    return {"received": filenames, "count": len(files)}
