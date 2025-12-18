def detect_document_type(text: str) -> str:
    t = text.lower()

    if "admission form" in t or "application for admission" in t:
        return "admission_form"

    if "transfer certificate" in t:
        return "transfer_certificate"

    if "birth certificate" in t:
        return "birth_certificate"

    if (
        "central board of secondary education" in t
        or "secondary school examination" in t
        or "marks statement" in t
    ):
        return "marksheet"

    # Aadhaar heuristic
    digits = [c for c in t if c.isdigit()]
    if len(digits) >= 12 and "government of india" in t:
        return "aadhaar"

    return "unknown"
