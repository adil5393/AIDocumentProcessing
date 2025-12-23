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