from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Student AI Processing System")

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Backend running"}
#CORS 

from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",  # if using Vite/React
    "http://localhost:5173",  # if using Vite new default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
