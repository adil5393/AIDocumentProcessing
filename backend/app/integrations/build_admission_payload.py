import time

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
