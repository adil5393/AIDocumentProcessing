def is_real_tc(t: str) -> bool:
    required = [
        "transfer certificate",
        "certified that",
        "last class",
        "date of leaving"
    ]

    score = sum(1 for r in required if r in t)

    # Must assert at least 2 strong facts
    return score >= 2

def is_tc_reference_only(t: str) -> bool:
    return any(p in t for p in [
        "whether the transfer certificate is attached",
        "tc attached",
        "date of tc",
        "yes/no"
    ])

import re

def detect_document_type(text: str) -> str:
    t = text.lower()

    # ---------- AADHAAR (hard) ----------
    if "unique identification authority of india" in t:
        return "aadhaar"

    # ---------- BIRTH CERT ----------
    if "birth certificate" in t and (
        "municipal" in t
        or "registrar of births" in t
        or "registration no" in t
    ):
        return "birth_certificate"

    # ---------- STRONG SIGNAL COUNTS ----------
    form_signals = 0
    marksheet_signals = 0
    aadhaar_signals = 0
    tc_assert_signals = 0

    # ---------- ADMISSION FORM ----------
    if "admission form" in t or "application for admission" in t:
        form_signals += 4
    if "admission" in t:
        form_signals += 2
    if "class" in t:
        form_signals += 1
    if "student name" in t:
        form_signals += 1
    if "father name" in t or "mother name" in t:
        form_signals += 1
    if "declaration by the parents" in t:
        form_signals += 2

    # ---------- MARKSHEET ----------
    if "statement of marks" in t or "marks statement" in t:
        marksheet_signals += 3
    if "roll no" in t:
        marksheet_signals += 1
    if "subject" in t and "marks" in t:
        marksheet_signals += 1

    # ---------- AADHAAR ----------
    if re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", t):
        aadhaar_signals += 2
    if "government of india" in t:
        aadhaar_signals += 1
    if "male" in t or "female" in t:
        aadhaar_signals += 1

    # ---------- REAL TC ASSERTION ----------
    if "transfer certificate" in t:
        if "certified that" in t:
            tc_assert_signals += 2
        if "date of leaving" in t:
            tc_assert_signals += 2
        if "last class" in t:
            tc_assert_signals += 1

    # ---------- DECISION ----------
    if form_signals >= 4:
        return "admission_form"

    if tc_assert_signals >= 3:
        return "transfer_certificate"

    if marksheet_signals >= 3:
        return "marksheet"

    if aadhaar_signals >= 4:
        return "aadhaar"

    return "unknown"
