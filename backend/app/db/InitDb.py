# app/db/init_db.py
from App.Db.Base import Base
from App.Db.Session import engine
import backend.app.db.models

def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created")

if __name__ == "__main__":
    main()
