# app/db/init_db.py
from backend.app.db.base import Base
from backend.app.db.session import engine
import backend.app.db.models

def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created")

if __name__ == "__main__":
    main()
