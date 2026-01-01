import json
import re
from sqlalchemy import text
from app.helper.matching import normalize_name,name_similarity,calculate_age

def run_bc_lookup(db, doc_id: int):

    row = db.execute(
        text("""
            SELECT student_name, father_name, mother_name,
                   date_of_birth
            FROM birth_certificates
            WHERE doc_id = :t
        """),
        {"t": doc_id}
    ).fetchone()

    if not row:
        return {"status": "error"}

    bc_student_tokens = normalize_name(row.student_name)
    bc_father_tokens = normalize_name(row.father_name)
    bc_mother_tokens = normalize_name(row.mother_name)
    bc_dob = row.date_of_birth
    # ms_class = row.class_name

    # Clear old candidates
    db.execute(
        text("DELETE FROM birth_certificate_candidates WHERE doc_id = :t"),
        {"t": doc_id}
    )

    candidates = {}

    rows = db.execute(
        text("""
            SELECT sr, student_name, father_name, mother_name,
                   date_of_birth 
            FROM admission_forms
        """)
    ).fetchall()

    for r in rows:
        signals = {}

        adm_student_tokens = normalize_name(r.student_name)
        adm_father_tokens = normalize_name(r.father_name)
        adm_mother_tokens = normalize_name(r.mother_name)

        signals["student_name_score"] = name_similarity(
            bc_student_tokens, adm_student_tokens
        )

        signals["father_name_score"] = name_similarity(
            bc_father_tokens, adm_father_tokens
        )

        signals["mother_name_score"] = name_similarity(
            bc_mother_tokens, adm_mother_tokens
        )

        signals["dob_match"] = (
            bc_dob and r.date_of_birth and bc_dob == r.date_of_birth
        )

        # signals["class_match"] = (
        #     ms_class and r.class_name and int(ms_class)+1 == int(r.class_name)
        # )

        total_score = (
            0.6 * signals["student_name_score"]
            + 0.2 * signals["father_name_score"]
            + 0.1 * signals["mother_name_score"]
            + 0.1 * (1.0 if signals["dob_match"] else 0.0)
            # + 0.1 * (1.0 if signals["class_match"] else 0.0)
        )

        if total_score >= 0.45:  # guardrail
            candidates[r.sr] = {
                "sr": r.sr,
                "total_score": round(total_score, 3),
                "signals": signals
            }

    # Insert candidates
    for c in candidates.values():
        db.execute(
            text("""
                INSERT INTO birth_certificate_candidates
                (doc_id, sr, total_score, signals)
                VALUES (:t, :s, :sc, :sig)
                ON CONFLICT DO NOTHING
            """),
            {
                "t": doc_id,
                "s": c["sr"],
                "sc": c["total_score"],
                "sig": json.dumps(c["signals"])
            }
        )

    # Status update
    if not candidates:
        status = "no_match"
    elif len(candidates) == 1:
        status = "single_match"
    else:
        status = "multiple_match"

    db.execute(
        text("""
            UPDATE birth_certificates
            SET lookup_status = :st,
                created_at = now()
            WHERE doc_id = :t
        """),
        {"st": status, "t": doc_id}
    )

    db.commit()
    return {"candidates": len(candidates), "status": status}
