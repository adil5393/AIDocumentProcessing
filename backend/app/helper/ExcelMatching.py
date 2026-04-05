from datetime import date, datetime

def compare(adm, doc):
    if doc is None:
        return "-"

    # Exact match (works for dates, strings, numbers)
    if adm == doc:
        return "MATCH"

    # Case-only difference (strings only)
    if isinstance(adm, str) and isinstance(doc, str):
        if adm.strip().lower() == doc.strip().lower():
            return "MATCH"

    return "MISMATCH"