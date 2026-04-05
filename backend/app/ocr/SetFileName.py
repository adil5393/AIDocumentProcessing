import re

def clean(s: str) -> str:
    if not s:
        return "UNKNOWN"
    s = s.strip().upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    return s.strip("_")

def admission_display_name(structured):
    name = clean(structured.get("student_name"))
    sr = clean(structured.get("sr"))
    cls = clean(structured.get("class"))
    return f"AF_{sr}_{name}_{cls}"

def tc_display_name(structured):
    name = clean(structured.get("student_name"))
    cls = clean(structured.get("last_class_studied"))
    return f"TC_{name}_{cls}"

def aadhaar_display_name(structured):
    name = clean(structured.get("name"))
    aadhaar = structured.get("aadhaar_number", "")
    last4 = aadhaar[-4:] if len(aadhaar) >= 4 else "XXXX"
    return f"AD_{name}_{last4}"

def birth_certificate_display_name(structured):
    name = clean(structured.get("student_name"))
    dob = clean(structured.get("date_of_birth"))
    father_name = clean(structured.get("father_name"))
    return f"BC_{name}_{father_name}_{dob}"

def highschool_marksheet_display_name(structured):
    name = clean(structured.get("student_name"))
    father_name = clean(structured.get("father_name"))
    mother_name = clean(structured.get("mother_name"))
    date_of_birth = clean(structured.get("date_of_birth"))
    result_status = clean(structured.get("result_status"))
    return f"HM_{name}_{date_of_birth}_{father_name}_{result_status}"
