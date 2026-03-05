import json
from sqlalchemy import text
from app.helper.matching import normalize_name, name_similarity


def run_bc_lookup(db, doc_id: int, preloaded=None, top_n: int = 50):
    """
    preloaded (optional): dict with "forms" — list of pre-tokenised admission form dicts.
    """
    row = db.execute(
        text("""
            SELECT student_name, father_name, mother_name, date_of_birth
            FROM birth_certificates
            WHERE doc_id = :t
        """),
        {"t": doc_id}
    ).fetchone()

    if not row:
        return {"status": "error"}

    bc_student_tokens = normalize_name(row.student_name)
    bc_father_tokens  = normalize_name(row.father_name)
    bc_mother_tokens  = normalize_name(row.mother_name)
    bc_dob            = row.date_of_birth

    db.execute(
        text("DELETE FROM birth_certificate_candidates WHERE doc_id = :t"),
        {"t": doc_id}
    )

    candidates = {}

    if preloaded is not None:
        rows = preloaded["forms"]
    else:
        raw = db.execute(
            text("""
                SELECT sr, student_name, father_name, mother_name, date_of_birth
                FROM admission_forms
            """)
        ).fetchall()
        rows = [
            {
                "sr":             r.sr,
                "student_name":   r.student_name,
                "father_name":    r.father_name,
                "mother_name":    r.mother_name,
                "date_of_birth":  r.date_of_birth,
                "student_tokens": normalize_name(r.student_name),
                "father_tokens":  normalize_name(r.father_name),
                "mother_tokens":  normalize_name(r.mother_name),
            }
            for r in raw
        ]

    for r in rows:
        signals = {}

        signals["student_name_score"] = name_similarity(bc_student_tokens, r["student_tokens"])
        signals["father_name_score"]  = name_similarity(bc_father_tokens,  r["father_tokens"])
        signals["mother_name_score"]  = name_similarity(bc_mother_tokens,  r["mother_tokens"])
        signals["dob_match"]          = bool(bc_dob and r["date_of_birth"] and bc_dob == r["date_of_birth"])

        total_score = (
            0.6 * signals["student_name_score"]
            + 0.2 * signals["father_name_score"]
            + 0.1 * signals["mother_name_score"]
            + 0.1 * (1.0 if signals["dob_match"] else 0.0)
        )

        if total_score >= 0.2:
            candidates[r["sr"]] = {
                "sr":          r["sr"],
                "total_score": round(total_score, 3),
                "signals":     signals,
            }

    status = (
        "no_match"       if not candidates else
        "single_match"   if len(candidates) == 1 else
        "multiple_match"
    )

    if candidates:
        top = sorted(candidates.values(), key=lambda c: c["total_score"], reverse=True)[:top_n]
        db.execute(
            text("""
                INSERT INTO birth_certificate_candidates (doc_id, sr, total_score, signals)
                VALUES (:t, :s, :sc, :sig)
                ON CONFLICT DO NOTHING
            """),
            [
                {"t": doc_id, "s": c["sr"], "sc": c["total_score"], "sig": json.dumps(c["signals"])}
                for c in top
            ],
        )

    db.execute(
        text("""
            UPDATE birth_certificates
            SET lookup_status = :st, last_checked_at = now()
            WHERE doc_id = :t
        """),
        {"st": status, "t": doc_id}
    )

    db.commit()
    return {"candidates": len(candidates), "status": status}


def run_bc_batch(doc_ids: list):
    """Batch version: loads admission forms once, runs in background."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        raw_forms = db.execute(
            text("""
                SELECT sr, student_name, father_name, mother_name, date_of_birth
                FROM admission_forms
            """)
        ).fetchall()

        preloaded_forms = [
            {
                "sr":             r.sr,
                "student_name":   r.student_name,
                "father_name":    r.father_name,
                "mother_name":    r.mother_name,
                "date_of_birth":  r.date_of_birth,
                "student_tokens": normalize_name(r.student_name),
                "father_tokens":  normalize_name(r.father_name),
                "mother_tokens":  normalize_name(r.mother_name),
            }
            for r in raw_forms
        ]

        preloaded = {"forms": preloaded_forms}

        for doc_id in doc_ids:
            try:
                run_bc_lookup(db, doc_id, preloaded=preloaded)
            except Exception as e:
                print(f"[bc_batch] doc_id={doc_id} error: {e}")
                continue

    finally:
        db.close()
