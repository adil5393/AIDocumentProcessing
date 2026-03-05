import json
from sqlalchemy import text
from app.helper.matching import normalize_name, name_similarity


def run_tc_lookup(db, doc_id: int, preloaded=None, top_n: int = 50):
    """
    preloaded (optional): dict with "forms" — list of pre-tokenised admission form dicts.
    """
    row = db.execute(
        text("""
            SELECT student_name, father_name, mother_name,
                   date_of_birth, last_class_studied AS class_name
            FROM transfer_certificates
            WHERE doc_id = :t
        """),
        {"t": doc_id}
    ).fetchone()

    if not row:
        return {"status": "error"}

    # Guard: never re-process a confirmed document
    current_status = db.execute(
        text("SELECT lookup_status FROM transfer_certificates WHERE doc_id = :t"),
        {"t": doc_id}
    ).scalar()
    if current_status == "Confirmed":
        return {"status": "skipped"}

    tc_student_tokens = normalize_name(row.student_name)
    tc_father_tokens  = normalize_name(row.father_name)
    tc_mother_tokens  = normalize_name(row.mother_name)
    tc_dob            = row.date_of_birth
    tc_class          = row.class_name

    db.execute(
        text("DELETE FROM transfer_certificate_candidates WHERE doc_id = :t"),
        {"t": doc_id}
    )

    candidates = {}

    if preloaded is not None:
        rows = preloaded["forms"]
    else:
        raw = db.execute(
            text("""
                SELECT sr, student_name, father_name, mother_name,
                       date_of_birth, class AS class_name
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
                "class_name":     r.class_name,
                "student_tokens": normalize_name(r.student_name),
                "father_tokens":  normalize_name(r.father_name),
                "mother_tokens":  normalize_name(r.mother_name),
            }
            for r in raw
        ]

    for r in rows:
        signals = {}

        signals["student_name_score"] = name_similarity(tc_student_tokens, r["student_tokens"])
        signals["father_name_score"]  = name_similarity(tc_father_tokens,  r["father_tokens"])
        signals["mother_name_score"]  = name_similarity(tc_mother_tokens,  r["mother_tokens"])
        signals["dob_match"]          = bool(tc_dob and r["date_of_birth"] and tc_dob == r["date_of_birth"])

        try:
            signals["class_match"] = bool(
                tc_class and r["class_name"]
                and int(tc_class) + 1 == int(r["class_name"])
            )
        except (ValueError, TypeError):
            signals["class_match"] = False

        total_score = (
            0.6 * signals["student_name_score"]
            + 0.2 * signals["father_name_score"]
            + 0.1 * signals["mother_name_score"]
            + 0.1 * (1.0 if signals["dob_match"] else 0.0)
            + 0.1 * (1.0 if signals["class_match"] else 0.0)
        )

        if total_score >= 0.3:
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
                INSERT INTO transfer_certificate_candidates (doc_id, sr, total_score, signals)
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
            UPDATE transfer_certificates
            SET lookup_status = :st, lookup_checked_at = now()
            WHERE doc_id = :t AND lookup_status != 'Confirmed'
        """),
        {"st": status, "t": doc_id}
    )

    db.commit()
    return {"candidates": len(candidates), "status": status}


def run_tc_batch(doc_ids: list):
    """Batch version: loads admission forms once, runs in background."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        raw_forms = db.execute(
            text("""
                SELECT sr, student_name, father_name, mother_name,
                       date_of_birth, class AS class_name
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
                "class_name":     r.class_name,
                "student_tokens": normalize_name(r.student_name),
                "father_tokens":  normalize_name(r.father_name),
                "mother_tokens":  normalize_name(r.mother_name),
            }
            for r in raw_forms
        ]

        preloaded = {"forms": preloaded_forms}

        for doc_id in doc_ids:
            try:
                run_tc_lookup(db, doc_id, preloaded=preloaded)
            except Exception as e:
                print(f"[tc_batch] doc_id={doc_id} error: {e}")
                continue

    finally:
        db.close()
