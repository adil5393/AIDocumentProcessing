import re

def detect_document_type(text: str) -> str:
    t = text.lower()

    scores = {
        "admission_form": 0,
        "transfer_certificate": 0,
        "birth_certificate": 0,
        "marksheet": 0,
        "aadhaar": 0,
    }

    # ---------- Admission Form ----------
    if "admission form" in t:
        scores["admission_form"] += 3
    if "application for admission" in t:
        scores["admission_form"] += 3
    if "student name" in t and "father name" in t:
        scores["admission_form"] += 1

    # ---------- Transfer Certificate ----------
    if "transfer certificate" in t:
        scores["transfer_certificate"] += 4
    if "tc no" in t or "leaving certificate" in t:
        scores["transfer_certificate"] += 2
    if "date of leaving" in t:
        scores["transfer_certificate"] += 2

    # ---------- Birth Certificate ----------
    if "birth certificate" in t:
        scores["birth_certificate"] += 4
    if "date of birth" in t and "place of birth" in t:
        scores["birth_certificate"] += 2

    # ---------- Marksheet ----------
    if "central board of secondary education" in t:
        scores["marksheet"] += 3
    if "secondary school examination" in t:
        scores["marksheet"] += 3
    if "marks statement" in t or "statement of marks" in t:
        scores["marksheet"] += 2
    if "roll no" in t and "subject" in t:
        scores["marksheet"] += 1

    # ---------- Aadhaar (STRICT) ----------
    aadhaar_number = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", t)
    if aadhaar_number:
        scores["aadhaar"] += 4

    if "government of india" in t:
        scores["aadhaar"] += 1
    if "unique identification authority of india" in t:
        scores["aadhaar"] += 3
    if "dob" in t and ("male" in t or "female" in t):
        scores["aadhaar"] += 1

    # ---------- Negative signals ----------
    if "transfer certificate" in t:
        scores["aadhaar"] -= 3
    if "school" in t and "principal" in t:
        scores["aadhaar"] -= 2

    # ---------- Decide ----------
    best_doc, best_score = max(scores.items(), key=lambda x: x[1])

    if best_score >= 3:
        return best_doc

    return "unknown"
