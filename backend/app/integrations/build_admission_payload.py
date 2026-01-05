import time
from datetime import datetime, date
def safe(val):
    """
    Convert None / 'null' to empty string.
    Amtech hates None.
    """
    return "" if val in (None, "null") else str(val)
def split_name(full_name: str):
    """
    Splits full name into firstname, lastname, middle initial.
    """
    if not full_name:
        return "", "", ""

    parts = full_name.strip().split()

    if len(parts) == 1:
        return parts[0], "", ""

    return parts[0], " ".join(parts[1:]), ""
def iso_to_ddmmyyyy(value):
    """
    Accepts:
    - datetime
    - date
    - ISO string (YYYY-MM-DD or full ISO)
    Returns DD/MM/YYYY or empty string
    """
    if not value:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")

    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.strip()).strftime("%d/%m/%Y")
        except ValueError:
            return ""

    return ""
def class_to_amtech_label(cls):
    """
    Converts numeric class to Amtech Roman label.
    """
    cls = str(cls)

    if cls.isdigit():
        romans = [
            "I", "II", "III", "IV", "V", "VI",
            "VII", "VIII", "IX", "X", "XI", "XII"
        ]
        idx = int(cls) - 1
        if 0 <= idx < len(romans):
            return romans[idx]

    return cls
def resolve_class_ids(masters, class_label, section_label="A"):
    """
    Resolves class_id, section_id, class_section_id
    from masters safely.
    """

    classes = masters["masters"]["classes"]
    sections = masters["masters"]["sections"]
    class_sections = masters["masters"]["class_sections"]

    class_id = next(
        (c["id"] for c in classes if c["label"] == class_label),
        ""
    )

    section_id = next(
        (s["id"] for s in sections if s["label"] == section_label),
        ""
    )

    class_section_id = next(
        (
            cs["id"]
            for cs in class_sections
            if cs["class"] == class_label and cs["section"] == section_label
        ),
        ""
    )

    return class_id, section_id, class_section_id
def normalize_gender(gender):
    if not gender:
        return ""

    g = gender.lower()
    if g.startswith("m"):
        return "Male"
    if g.startswith("f"):
        return "Female"
    return ""
def bool_to_str(val):
    return "true" if val else "false"

def build_amtech_admission_payload(admission, masters):
    fn, ln, mi = split_name(admission.get("student_name"))

    class_label = class_to_amtech_label(admission.get("class"))
    section_label = "A"

    class_id, section_id, class_section_id = resolve_class_ids(
        masters, class_label, section_label
    )
    
    return [{
        "ser_number": admission["sr"],
        "spen_number": safe(admission.get("spen")),
        "form_number": "",

        "date_of_admission": iso_to_ddmmyyyy(admission.get("created_at")),
        "academic_session_id": masters["posting_session"]["id"],

        "student_firstname": fn,
        "student_lastname": ln,
        "student_mi": mi,
        "student_dob": iso_to_ddmmyyyy(admission.get("date_of_birth")),
        "student_gender": normalize_gender(admission.get("gender")),
        "student_religion": "",
        "student_caste": "",

        "class_category_id": masters["defaults"]["class_category"],
        "class_id": class_id,
        "section_id": section_id,
        "class_section_id": class_section_id,

        "students_adharcard_number": safe(admission.get("student_aadhaar_number")),
        "student_smsnumber": safe(admission.get("phone1")),
        "house_id": "1",

        "high_school_registration": "",
        "student_board": "",
        "student_year": "",
        "subject1": "",
        "subject2": "",

        "previous_school_name": safe(admission.get("last_school_attended")),
        "previous_school_board": "",

        "annual_income": "",

        "student_address": safe(admission.get("address")),
        "student_city": masters["defaults"]["city"],
        "student_state": masters["defaults"]["state"],
        "student_country": masters["defaults"]["country"],
        "student_zip": "230001",

        "is_rte": bool_to_str(masters["defaults"]["is_rte"]),
        "is_new": bool_to_str(masters["defaults"]["is_new"]),
        "old_tc_submitted": "false",

        "father_name": safe(admission.get("father_name")),
        "father_education": "",
        "father_occupation": safe(admission.get("father_occupation")),
        "father_adharcard_number": safe(admission.get("father_aadhaar")),
        "father_phone_number": safe(admission.get("phone1")),

        "mother_name": safe(admission.get("mother_name")),
        "mother_education": "",
        "mother_occupation": safe(admission.get("mother_occupation")),
        "mother_adharcard_number": safe(admission.get("mother_aadhaar")),
        "mother_phone_number": safe(admission.get("phone2")),
    },
    masters["branch"]["id"]]



def build_dummy_admission_payload(masters):
    """
    Builds a fully valid Amtech admission payload
    WITHOUT sending it.
    """
    
    return [{
    # --- identifiers ---
    "ser_number": "x3012312312123",
    "spen_number": "1",
    "form_number": "1",

    "date_of_admission": "01/01/2026",
    "academic_session_id": "4",

    # --- student core ---
    "student_firstname": "Test",
    "student_lastname": "Student",
    "student_mi": ".",                # 🔴 REQUIRED
    "student_dob": "01/01/2015",
    "student_gender": "Male",
    "student_religion": "Hindu",
    "student_caste": "1",              # 🔴 REQUIRED

    # --- class mapping ---
    "class_category_id": "OTHER",
    "class_id": masters["masters"]["classes"][3]["id"],
    "section_id": masters["masters"]["sections"][0]["id"],
    "class_section_id": masters["masters"]["class_sections"][0]["id"],

    # --- IDs / contact ---
    "students_adharcard_number": "111122223333",
    "student_smsnumber": "9999999999",
    "house_id": "1",                   # 🔴 REQUIRED

    # --- academic extras ---
    "high_school_registration": ".",
    "student_board": "CBSE Board",
    "student_year": ".",
    "subject1": ".",
    "subject2": ".",

    # --- previous school ---
    "previous_school_name": ".",        # 🔴 NOT Dummy School
    "previous_school_board": ".",

    # --- finance ---
    "annual_income": ".",

    # --- address ---
    "student_address": "Dummy Address",
    "student_city": masters["defaults"]["city"],
    "student_state": masters["defaults"]["state"],
    "student_country": masters["defaults"]["country"],
    "student_zip": "230001",

    # --- flags ---
    "is_rte": "false",
    "is_new": "true",
    "old_tc_submitted": "false",

    # --- father ---
    "father_name": "Dummy Father",
    "father_education": ".",
    "father_occupation": ".",
    "father_adharcard_number": ".",
    "father_phone_number": "9999999999",

    # --- mother ---
    "mother_name": "Dummy Mother",
    "mother_education": ".",
    "mother_occupation": ".",
    "mother_adharcard_number": ".",
    "mother_phone_number": ".",

}, masters["branch"]["id"]]

