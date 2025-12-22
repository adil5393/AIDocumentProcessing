import json
import re
from sqlalchemy import text
from datetime import date

# -------------------------
# NORMALIZATION
# -------------------------

STOPWORDS = {"mr", "mrs", "ms", "miss", "sh", "smt", "kum", "dr"}

def normalize_name(name: str) -> list[str]:
    if not name:
        return []
    name = name.lower()
    name = re.sub(r"[^a-z\s]", " ", name)
    tokens = name.split()
    return [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]

def approx_match_score(t1: str, t2: str) -> float:
    if t1 == t2:
        return 1.0

    if len(t1) >= 5 and len(t2) >= 5 and t1[:5] == t2[:5]:
        return 0.9

    if t1[:4] == t2[:4]:
        return 0.6

    if abs(len(t1) - len(t2)) <= 1:
        mismatches = sum(c1 != c2 for c1, c2 in zip(t1, t2))
        mismatches += abs(len(t1) - len(t2))
        if mismatches <= 1:
            return 0.7

    return 0.0

def name_similarity(tokens1, tokens2) -> float:
    if not tokens1 or not tokens2:
        return 0.0

    matched = 0.0
    used = set()

    for t1 in tokens1:
        best = 0.0
        best_t2 = None
        for t2 in tokens2:
            if t2 in used:
                continue
            s = approx_match_score(t1, t2)
            if s > best:
                best = s
                best_t2 = t2

        if best > 0:
            matched += best
            if best_t2:
                used.add(best_t2)

    return matched / max(len(tokens1), len(tokens2))

def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )

# -------------------------
# SCORING (NO DECISIONS)
# -------------------------

def build_candidate(sr, role, signals):
    score = 0.0

    score += 1.0 if signals.get("aadhaar_exact") else 0.0
    score += 0.4 * signals.get("student_name_score", 0.0)
    score += 0.3 * signals.get("parent_name_score", 0.0)
    score += 0.2 * signals.get("related_name_score", 0.0)
    score += 0.2 if signals.get("age_match") else 0.0
    score += 0.2 if signals.get("relation_match") else 0.0

    return {
        "sr": sr,
        "role": role,
        "total_score": round(score, 3),
        "signals": signals
    }

# -------------------------
# MAIN LOOKUP
# -------------------------

def run_aadhaar_lookup(db, doc_id: int):

    row = db.execute(
        text("""
            SELECT aadhaar_number, name, relation_type, related_name, date_of_birth
            FROM aadhaar_documents
            WHERE doc_id = :doc_id
        """),
        {"doc_id": doc_id}
    ).fetchone()

    if not row:
        return {"status": "error"}

    aadhaar_no = (row.aadhaar_number or "").strip()
    aadhaar_name = row.name or ""
    relation_type = (row.relation_type or "").upper()
    related_name = row.related_name or ""
    aadhaar_age = calculate_age(row.date_of_birth)

    # clear old
    db.execute(
        text("DELETE FROM aadhaar_lookup_candidates WHERE doc_id = :d"),
        {"d": doc_id}
    )

    candidates = {}

    # -------------------------
    # EXACT AADHAAR (HARD SIGNAL)
    # -------------------------
    if aadhaar_no:
        rows = db.execute(
            text("""
                SELECT sr,
                       CASE
                         WHEN student_aadhaar_number = :a THEN 'student'
                         WHEN father_aadhaar = :a THEN 'father'
                         WHEN mother_aadhaar = :a THEN 'mother'
                       END AS role
                FROM admission_forms
                WHERE student_aadhaar_number = :a
                   OR father_aadhaar = :a
                   OR mother_aadhaar = :a
            """),
            {"a": aadhaar_no}
        ).fetchall()

        for r in rows:
            candidates[(r.sr, r.role)] = build_candidate(
                r.sr,
                r.role,
                {"aadhaar_exact": True}
            )

    # -------------------------
    # CARTESIAN SCORING
    # -------------------------
    if not candidates:
        rows = db.execute(
            text("""
                SELECT sr, student_name, father_name, mother_name
                FROM admission_forms
            """)
        ).fetchall()

        for r in rows:
            sr = r.sr

            student_tokens = normalize_name(r.student_name)
            father_tokens = normalize_name(r.father_name)
            mother_tokens = normalize_name(r.mother_name)

            aadhaar_tokens = normalize_name(aadhaar_name)
            related_tokens = normalize_name(related_name)

            # ---- STUDENT ----
            if aadhaar_age is None or aadhaar_age < 18:
                signals = {
                    "relation_match": relation_type in ("S/O", "D/O"),
                    "age_match": aadhaar_age is not None and aadhaar_age < 18,
                    "student_name_score": name_similarity(aadhaar_tokens, student_tokens),
                    "related_name_score": name_similarity(related_tokens, father_tokens),
                }
                candidates[(sr, "student")] = build_candidate(sr, "student", signals)

            # ---- FATHER ----
            if aadhaar_age is None or aadhaar_age >= 18:
                signals = {
                    "age_match": aadhaar_age is not None and aadhaar_age >= 18,
                    "parent_name_score": name_similarity(aadhaar_tokens, father_tokens),
                }
                candidates[(sr, "father")] = build_candidate(sr, "father", signals)

            # ---- MOTHER ----
            if aadhaar_age is None or aadhaar_age >= 18:
                signals = {
                    "relation_match": relation_type in ("W/O", "D/O"),
                    "age_match": aadhaar_age is not None and aadhaar_age >= 18,
                    "parent_name_score": name_similarity(aadhaar_tokens, mother_tokens),
                }
                candidates[(sr, "mother")] = build_candidate(sr, "mother", signals)

    # -------------------------
    # INSERT
    # -------------------------
    if not candidates:
        status = "no_match"
    elif len(candidates) == 1:
        status = "single_match"
    else:
        status = "multiple_match"
    for c in candidates.values():
        db.execute(
            text("""
                INSERT INTO aadhaar_lookup_candidates
                (doc_id, sr, role, total_score, signals)
                VALUES (:d, :s, :r, :t, :sig)
                ON CONFLICT DO NOTHING
            """),
            {
                "d": doc_id,
                "s": c["sr"],
                "r": c["role"],
                "t": c["total_score"],
                "sig": json.dumps(c["signals"])
            }
        )

    db.execute(
        text("""
            UPDATE aadhaar_documents
            SET lookup_status = :st,
                lookup_checked_at = now()
            WHERE doc_id = :d
        """),
        {
            "st": status,
            "d": doc_id
        }
    )

    db.commit()
    return {"candidates": len(candidates)}
