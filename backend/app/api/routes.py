from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Depends, Header
from app.services.amtech import test_connection
from app.services.auth_service import authenticate
from pydantic import BaseModel

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


@router.post("/upload")
async def upload(files: list[UploadFile]):
    filenames = [f.filename for f in files]
    return {"received": filenames, "count": len(files)}

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/version")
def version():
    return {"version": "0.1.0"}
