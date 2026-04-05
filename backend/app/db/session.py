from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import importlib

load_dotenv()

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5432")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME",     "nasss_ocr")
DB_URL      = os.getenv("DB_URL")

if DEV_MODE:
    DATABASE_URL = DB_URL or "sqlite:///./NASSS_DEV.db"
else:
    DATABASE_URL = DB_URL or f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

if DEV_MODE:
    from App.Db.Base import Base
    try:
        importlib.import_module("App.Db.Models")
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print("Failed to initialize dev database schema:", e)
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()