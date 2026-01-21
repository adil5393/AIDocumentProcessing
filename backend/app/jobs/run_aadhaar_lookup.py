import json
from sqlalchemy import text
from app.helper.matching import (
    normalize_name,
    name_similarity,
    calculate_age,
    dob_similarity,
)
def build_candidate(sr, role, student_name, signals):
    score = 0.0

    if signals.get("aadhaar_exact"):
        score += 1.0

    score += 0.5 * signals.get("name_score", 0.0)
    score += 0.4 * signals.get("dob_score", 0.0)
    score += 0.3 * signals.get("parent_name_score", 0.0)
    score += 0.2 * signals.get("related_name_score", 0.0)

    score += 0.2 if signals.get("relation_match") else 0.0
    score += 0.3 if signals.get("age_role_valid") else -0.5  # penalty matters

    return {
        "sr": sr,
        "role": role,
        "student_name": student_name,
        "total_score": round(score, 3),
        "signals": signals
    }

def run_aadhaar_lookup(db, doc_id: int):

    aadhaar = db.execute(
        text("""
            SELECT aadhaar_number, name, relation_type, related_name, date_of_birth
            FROM aadhaar_documents
            WHERE doc_id = :d
        """),
        {"d": doc_id}
    ).fetchone()

    if not aadhaar:
        return {"status": "error"}

    aadhaar_no = (aadhaar.aadhaar_number or "").strip()
    aadhaar_tokens = normalize_name(aadhaar.name or "")
    related_tokens = normalize_name(aadhaar.related_name or "")
    relation_type = (aadhaar.relation_type or "").upper()
    aadhaar_dob = aadhaar.date_of_birth
    aadhaar_age = calculate_age(aadhaar_dob)

    # clear old candidates
    db.execute(
        text("DELETE FROM aadhaar_lookup_candidates WHERE doc_id = :d"),
        {"d": doc_id}
    )

    candidates = {}

    # ==========================================================
    # 1️⃣ EXACT AADHAAR MATCH (WITH VERIFICATION)
    # ==========================================================

    if aadhaar_no:
        rows = db.execute(
            text("""
                SELECT af.sr,
                       af.student_name,
                       af.father_name,
                       af.mother_name,
                       af.date_of_birth,
                       CASE
                           WHEN af.student_aadhaar_number = :a THEN 'student'
                           WHEN af.father_aadhaar = :a THEN 'father'
                           WHEN af.mother_aadhaar = :a THEN 'mother'
                       END AS role
                FROM admission_forms af
                WHERE :a IN (
                    af.student_aadhaar_number,
                    af.father_aadhaar,
                    af.mother_aadhaar
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM aadhaar_matches am
                    WHERE am.sr_number = af.sr
                      AND am.aadhaar_doc_id = :d
                )
            """),
            {"a": aadhaar_no, "d": doc_id}
        ).fetchall()

        for r in rows:
            if r.role == "student":
                name_score = name_similarity(aadhaar_tokens, normalize_name(r.student_name))
                dob_score = dob_similarity(aadhaar_dob, r.date_of_birth)
                parent_score = 0.0
                related_score = name_similarity(related_tokens, normalize_name(r.father_name))
                age_ok = aadhaar_age is not None and aadhaar_age < 18

            elif r.role == "father":
                name_score = name_similarity(aadhaar_tokens, normalize_name(r.father_name))
                dob_score = 0.0
                parent_score = name_score
                related_score = 0.0
                age_ok = aadhaar_age is not None and aadhaar_age >= 18

            else:  # mother
                name_score = name_similarity(aadhaar_tokens, normalize_name(r.mother_name))
                dob_score = 0.0
                parent_score = name_score
                related_score = 0.0
                age_ok = aadhaar_age is not None and aadhaar_age >= 18

            signals = {
                "aadhaar_exact": True,
                "name_score": name_score,
                "dob_score": dob_score,
                "parent_name_score": parent_score,
                "related_name_score": related_score,
                "relation_match": (
                    (relation_type in ("S/O", "D/O") and r.role == "student") or
                    (relation_type == "S/O" and r.role == "father") or
                    (relation_type == "W/O" and r.role == "mother")
                ),
                "age_role_valid": age_ok
            }

            candidates[(r.sr, r.role)] = build_candidate(
                r.sr, r.role, r.student_name, signals
            )

    # ==========================================================
    # 2️⃣ SOFT / CARTESIAN MATCH (ONLY IF NO EXACT)
    # ==========================================================

    if not candidates:
        rows = db.execute(
            text("""
                SELECT sr, student_name, father_name, mother_name, date_of_birth
                FROM admission_forms
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM aadhaar_matches
                    WHERE sr_number = sr
                      AND aadhaar_doc_id = :d
                )
            """),
            {"d": doc_id}
        ).fetchall()

        for r in rows:
            student_tokens = normalize_name(r.student_name)
            father_tokens = normalize_name(r.father_name)
            mother_tokens = normalize_name(r.mother_name)

            # ---- STUDENT ----
            if aadhaar_age is None or aadhaar_age < 18:
                signals = {
                    "aadhaar_exact": False,
                    "name_score": name_similarity(aadhaar_tokens, student_tokens),
                    "dob_score": dob_similarity(aadhaar_dob, r.date_of_birth),
                    "parent_name_score": 0.0,
                    "related_name_score": name_similarity(related_tokens, father_tokens),
                    "relation_match": relation_type in ("S/O", "D/O", "C/O"),
                    "age_role_valid": aadhaar_age is not None and aadhaar_age < 18
                }
                candidates[(r.sr, "student")] = build_candidate(
                    r.sr, "student", r.student_name, signals
                )

            # ---- FATHER ----
            if aadhaar_age is None or aadhaar_age >= 18:
                signals = {
                    "aadhaar_exact": False,
                    "name_score": name_similarity(aadhaar_tokens, father_tokens),
                    "dob_score": 0.0,
                    "parent_name_score": name_similarity(aadhaar_tokens, father_tokens),
                    "related_name_score": 0.0,
                    "relation_match": relation_type == "S/O",
                    "age_role_valid": aadhaar_age is not None and aadhaar_age >= 18
                }
                candidates[(r.sr, "father")] = build_candidate(
                    r.sr, "father", r.student_name, signals
                )

            # ---- MOTHER ----
            if aadhaar_age is None or aadhaar_age >= 18:
                signals = {
                    "aadhaar_exact": False,
                    "name_score": name_similarity(aadhaar_tokens, mother_tokens),
                    "dob_score": 0.0,
                    "parent_name_score": name_similarity(aadhaar_tokens, mother_tokens),
                    "related_name_score": 0.0,
                    "relation_match": relation_type in ("W/O", "D/O"),
                    "age_role_valid": aadhaar_age is not None and aadhaar_age >= 18
                }
                candidates[(r.sr, "mother")] = build_candidate(
                    r.sr, "mother", r.student_name, signals
                )

    # ==========================================================
    # 3️⃣ INSERT + STATUS
    # ==========================================================

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
                (doc_id, sr, role, student_name, total_score, signals)
                VALUES (:d, :s, :r, :sn, :t, :sig)
                ON CONFLICT DO NOTHING
            """),
            {
                "d": doc_id,
                "s": c["sr"],
                "r": c["role"],
                "sn": c["student_name"],
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
        {"st": status, "d": doc_id}
    )

    db.commit()
    return {"candidates": len(candidates), "status": status}
