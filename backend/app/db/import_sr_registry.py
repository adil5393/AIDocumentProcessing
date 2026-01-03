import csv
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import os
# =========================
# CONFIG
# =========================
load_dotenv()
CSV_PATH = os.getenv("OLD_DATA")  # path to your CSV
BRANCH_ID = 1               # change if needed
RESERVED_BY = 0             # system user
STATUS = "reserved"             # free | reserved | confirmed

DB_HOST=os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT")
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_PASSWORD")
DB_NAME=os.getenv("DB_NAME")

DB_CONFIG = {
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "host": DB_HOST,
    "port": DB_PORT,
}
# print(DB_CONFIG)

# =========================
# SCRIPT
# =========================

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    rows = []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)

        for i, row in enumerate(reader, start=1):
            if not row:
                continue

            sr = row[0].strip()

            if not sr or sr.lower() in ("sr", "sr_number"):
                continue  # skip header / blanks

            rows.append((
                sr,
                BRANCH_ID,
                RESERVED_BY,
                STATUS
            ))

    if not rows:
        print("No SRs found in CSV")
        return

    sql = """
        INSERT INTO sr_registry (sr_number, branch_id, reserved_by, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (sr_number) DO NOTHING
    """

    execute_batch(cur, sql, rows, page_size=500)

    conn.commit()
    cur.close()
    conn.close()

    print(f"Inserted {len(rows)} SRs into sr_registry")

if __name__ == "__main__":
    main()
