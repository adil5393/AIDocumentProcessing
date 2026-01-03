# app/db/create_database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

ADMIN_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/postgres"
)

def main():
    engine = create_engine(
        ADMIN_DATABASE_URL,
        isolation_level="AUTOCOMMIT"
    )

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": DB_NAME},
        ).fetchone()

        if exists:
            print(f"Database '{DB_NAME}' already exists")
        else:
            conn.execute(text(f'CREATE DATABASE "{DB_NAME}"'))
            print(f"Database '{DB_NAME}' created")

if __name__ == "__main__":
    main()
