import re

def detect_document_type(text: str) -> str:
    t = text.lower()

    # ---------- HARD MATCHES (early return) ----------
    if "transfer certificate" in t or "school leaving certificate" in t:
        return "transfer_certificate"

    if "birth certificate" in t and (
        "municipal" in t
        or "registrar of births" in t
        or "registration no" in t
    ):
        return "birth_certificate"

    if "unique identification authority of india" in t:
        return "aadhaar"

    if "central board of secondary education" in t:
        return "marksheet"

    # ---------- STRONG SIGNAL COUNTS ----------
    form_signals = 0
    marksheet_signals = 0
    aadhaar_signals = 0

    # Admission form signals
    if "admission" in t or "application for admission" in t:
        form_signals += 3
    if "class" in t:
        form_signals += 1
    if "student name" in t:
        form_signals += 1
    if "father name" in t or "mother name" in t:
        form_signals += 1
    if "address" in t:
        form_signals += 1

    # Marksheet signals
    if "marks statement" in t or "statement of marks" in t:
        marksheet_signals += 3
    if "roll no" in t:
        marksheet_signals += 1
    if "subject" in t and "marks" in t:
        marksheet_signals += 1

    # Aadhaar signals (STRICT)
    if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", t):
        aadhaar_signals += 2
    if "government of india" in t:
        aadhaar_signals += 1
    if "male" in t or "female" in t:
        aadhaar_signals += 1

    # ---------- DECISION ----------
    # Admission beats everything unless explicitly overridden
    if form_signals >= 3:
        return "admission_form"

    if marksheet_signals >= 3:
        return "marksheet"

    if aadhaar_signals >= 4:
        return "aadhaar"

    return "unknown"
