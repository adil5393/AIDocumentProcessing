import time
from datetime import datetime, date


def safe(val):
    """Convert None / 'null' to empty string. ISMS ERP uses empty string, not None."""
    if val in (None, "null"):
        return ""
    return str(val).strip()


def split_name(full_name: str):
    """Splits full name into (firstname, lastname, middle_initial)."""
    if not full_name:
        return "", "", ""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], "", ""
    return parts[0], " ".join(parts[1:]), ""


def build_full_name(full_name: str) -> str:
    """Return the full name stripped cleanly."""
    return (full_name or "").strip()


def to_iso_date(value) -> str | None:
    """
    Convert any reasonable date representation to YYYY-MM-DD (ISO).
    Returns None if conversion fails — Django DateField accepts None.
    """
    if not value:
        return None

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

    return None


def normalize_gender(gender):
    if not gender:
        return ""
    g = gender.lower()
    if g.startswith("m"):
        return "Male"
    if g.startswith("f"):
        return "Female"
    return ""


def normalize_phone(phone: str) -> str:
    """Strip spaces/dashes; keep digits only (max 15 chars)."""
    if not phone:
        return ""
    cleaned = "".join(ch for ch in phone if ch.isdigit())
    return cleaned[:15]


def normalize_aadhaar(value: str) -> str:
    """Keep only 12 digits; return '' if invalid."""
    if not value:
        return ""
    cleaned = "".join(ch for ch in value if ch.isdigit())
    return cleaned if len(cleaned) == 12 else ""


def build_isms_admission_payload(admission: dict, masters: dict) -> dict:
    """
    Build a ISMS ERP Student API payload (JSON) from OCR admission data.

    Maps OCR admission_forms fields → Student model fields accepted by
    POST /api/students/ (Django REST Framework).

    Returns a plain dict — pass directly to isms_post() as payload.
    """
    full_name = build_full_name(admission.get("student_name") or "")
    class_label = safe(admission.get("class")) or ""
    section_label = "A"    # default; OCR rarely captures section

    return {
        # ── Identity ──────────────────────────────────────────────────────────
        "name":          full_name,
        "admission_no":  safe(admission.get("sr")),
        "spen_number":   safe(admission.get("spen")),
        "admission_date": to_iso_date(admission.get("created_at")),

        # ── Class / Section ───────────────────────────────────────────────────
        "class_field":   class_label,     # serializer field name (maps to class_name)
        "section":       section_label,
        "academic_year": masters["posting_session"]["id"],

        # ── Personal ──────────────────────────────────────────────────────────
        "dob":           to_iso_date(admission.get("date_of_birth")),
        "gender":        normalize_gender(admission.get("gender")),
        "aadhar_number": normalize_aadhaar(safe(admission.get("student_aadhaar_number"))),
        "address":       safe(admission.get("address")),

        # ── Father ────────────────────────────────────────────────────────────
        "father_name":         safe(admission.get("father_name")),
        "phone":               normalize_phone(safe(admission.get("phone1"))),
        "father_phone":        normalize_phone(safe(admission.get("phone1"))),
        "father_aadhar_number": normalize_aadhaar(safe(admission.get("father_aadhaar"))),
        "father_occupation":   safe(admission.get("father_occupation")),

        # ── Mother ────────────────────────────────────────────────────────────
        "mother_name":         safe(admission.get("mother_name")),
        "mother_phone":        normalize_phone(safe(admission.get("phone2"))),
        "mother_aadhar_number": normalize_aadhaar(safe(admission.get("mother_aadhaar"))),
        "mother_occupation":   safe(admission.get("mother_occupation")),

        # ── Previous school ───────────────────────────────────────────────────
        "previous_school": safe(admission.get("last_school_attended")),

        # ── Status flags ──────────────────────────────────────────────────────
        "status": "active",
        "ews":    masters["defaults"]["is_rte"],
    }


def build_dummy_admission_payload(masters: dict) -> dict:
    """
    Build a valid test payload WITHOUT posting it.
    Useful for dry-run/debug of the POST /api/students/ endpoint.
    """
    return {
        "name":          "Test Student",
        "admission_no":  "TEST-SR-001",
        "spen_number":   "SP001",
        "admission_date": "2026-04-01",
        "class_field":   masters["masters"]["classes"][0]["label"] if masters["masters"]["classes"] else "V",
        "section":       "A",
        "academic_year": masters["posting_session"]["id"],
        "dob":           "2015-06-15",
        "gender":        "Male",
        "aadhar_number": "",
        "address":       "123 Test Street",
        "father_name":   "Test Father",
        "phone":         "9999999999",
        "father_phone":  "9999999999",
        "father_aadhar_number": "",
        "father_occupation": "Service",
        "mother_name":   "Test Mother",
        "mother_phone":  "8888888888",
        "mother_aadhar_number": "",
        "mother_occupation": "Homemaker",
        "previous_school": "Previous School Name",
        "status": "active",
        "ews": False,
    }

