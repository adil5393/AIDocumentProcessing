from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Student AI Processing System",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,  # optional but recommended
)


app.include_router(router)

@app.get("/")
def root():
    return {"message": "Backend running"}
#CORS 

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "http://192.168.1.10:3000",   # backend PC
    "http://192.168.1.35:3000",   # phone
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
