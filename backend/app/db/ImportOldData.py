import csv
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import os
import re


# =========================
# CONFIG
# =========================
load_dotenv()

ROMAN_CLASS_MAP = {
    "I": "1",
    "II": "2",
    "III": "3",
    "IV": "4",
    "V": "5",
    "VI": "6",
    "VII": "7",
    "VIII": "8",
    "IX": "9",
    "X": "10",
    "XI":"11",
    "XII":"12"
}

CSV_PATH = os.getenv("OLD_DATA")  # path to your CSV
BRANCH_ID = 1               # change if needed
RESERVED_BY = 0             # system user
STATUS = "confirmed"             # free | reserved | confirmed

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
from datetime import datetime
def clean_class(value):
    if not value:
        return None

    value = value.strip().upper()

    # Roman numeral → string integer
    if value in ROMAN_CLASS_MAP:
        return ROMAN_CLASS_MAP[value]

    # Already numeric → normalize to string
    if value.isdigit():
        return value

    return None

def clean_aadhaar(value):
    if not value:
        return None

    digits = re.sub(r"\D", "", value)

    if len(digits) != 12:
        return None

    return digits

def clean_spen(value):
    if not value:
        return None

    value = value.strip().upper()

    # reject obvious non-values
    if value in ("NOT ENROLLED", "NA", "N/A", "NULL"):
        return None

    digits = re.sub(r"\D", "", value)

    if len(digits) != 11:
        return None

    return digits

def parse_ddmmyyyy(value):
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    return datetime.strptime(value, "%d/%m/%Y")
def clean_name(value):
    if not value:
        return None

    value = value.strip()

    if not value:
        return None

    # Uppercase for consistency
    value = value.upper()

    # Remove dots, commas, hyphens
    value = re.sub(r"[.,\-]", " ", value)

    # Collapse multiple spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()

def create_placeholder_file(cur, sr):
    cur.execute("""
        INSERT INTO uploaded_files (
            file_path,
            display_name,
            doc_type,
            ocr_done,
            extraction_done
        )
        VALUES (%s, %s, %s, false, false)
        RETURNING file_id
    """, (
        f"PENDING://admission_form/{sr}",          # 👈 placeholder path
        f"PENDING_ADMISSION_FORM_{sr}",
        "admission_form"
    ))

    return cur.fetchone()[0]

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sr = row.get("S.R Number", "").strip().upper()           
            if not sr:
                continue

            # ---- 1. Insert into sr_registry ----
            cur.execute("""
                INSERT INTO sr_registry (sr_number, branch_id, reserved_by, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (sr_number) DO NOTHING
            """, (sr, BRANCH_ID, RESERVED_BY, STATUS))

            # ---- 2. Create placeholder file ----
            file_id = create_placeholder_file(cur, sr)

            # ---- 3. Insert admission form ----
            cur.execute("""
                INSERT INTO admission_forms (
                    sr,
                    class,
                    student_name,
                    gender,
                    date_of_birth,
                    father_name,
                    mother_name,
                    address,
                    phone1,
                    student_aadhaar_number,
                    father_aadhaar,
                    mother_aadhaar,
                    spen,
                    file_id,
                    created_at
                )
                VALUES (
                    %(sr)s,
                    %(class)s,
                    %(student_name)s,
                    %(gender)s,
                    %(date_of_birth)s,
                    %(father_name)s,
                    %(mother_name)s,
                    %(address)s,
                    %(phone1)s,
                    %(student_aadhaar_number)s,
                    %(father_aadhaar)s,
                    %(mother_aadhaar)s,
                    %(spen)s,
                    %(file_id)s,
                    %(created_at)s
                )
            """, {
                "sr": sr,
                "class": clean_class(row.get("Class")),
                "student_name": clean_name(row.get("Student Name")),
                "gender": row.get("Gender"),
                "date_of_birth": parse_ddmmyyyy(row.get("Date Of Birth")),
                "father_name": clean_name(row.get("Father Name")),
                "mother_name": clean_name(row.get("Mother Name")),
                "address": row.get("Address"),
                "phone1": row.get("Contact Number"),
                "student_aadhaar_number": clean_aadhaar(row.get("Adharcard Number")),
                "father_aadhaar": clean_aadhaar(row.get("Father Adharcard Number")),
                "mother_aadhaar": clean_aadhaar(row.get("Mother Adharcard Number")),
                "spen": clean_spen(row.get("SPEN Number")),
                "file_id": file_id,
                "created_at": parse_ddmmyyyy(row.get("Date Of Admission")),
            })

    conn.commit()
    cur.close()
    conn.close()

    print("CSV import completed")

if __name__ == "__main__":
    main()
