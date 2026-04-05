def get_isms_masters_internal():
    """
    Fetch school masters from the ISMS ERP (own Django backend).

    Returns a normalized dict with:
      - branch / school info
      - posting_session (active academic year)
      - masters: classes, sections, class_sections
      - defaults
    """
    import time
    from fastapi import HTTPException
    from App.Integrations.IsmsAuth import load_token, is_token_valid, authenticate
    from App.Integrations.IsmsClient import isms_get
    from dotenv import load_dotenv
    import os
    load_dotenv()

    DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

    if DEV_MODE:
        return {
            "branch": {
                "id": 1,
                "name": "Dev Branch"
            },
            "school": {
                "id": 1,
                "name": "Dummy School"
            },
            "posting_session": {
                "id": 1,
                "label": "2025-26",
                "locked": False
            },
            "masters": {
                "classes": [
                    {"id": "I",   "label": "I"},
                    {"id": "II",  "label": "II"},
                    {"id": "III", "label": "III"},
                    {"id": "IV",  "label": "IV"},
                    {"id": "V",   "label": "V"},
                    {"id": "VI",  "label": "VI"},
                    {"id": "VII", "label": "VII"},
                    {"id": "VIII","label": "VIII"},
                    {"id": "IX",  "label": "IX"},
                    {"id": "X",   "label": "X"},
                ],
                "sections": [
                    {"id": "A", "label": "A"},
                    {"id": "B", "label": "B"},
                    {"id": "C", "label": "C"},
                ],
                "class_sections": [
                    {"id": 1, "class": "I",    "section": "A"},
                    {"id": 2, "class": "II",   "section": "A"},
                    {"id": 3, "class": "III",  "section": "A"},
                    {"id": 4, "class": "IV",   "section": "A"},
                    {"id": 5, "class": "V",    "section": "A"},
                    {"id": 6, "class": "VI",   "section": "A"},
                    {"id": 7, "class": "VII",  "section": "A"},
                    {"id": 8, "class": "VIII", "section": "A"},
                    {"id": 9, "class": "IX",   "section": "A"},
                    {"id": 10, "class": "X",   "section": "A"},
                ]
            },
            "defaults": {
                "city": "",
                "state": "",
                "country": "India",
                "is_rte": False,
                "is_new": True,
                "class_category": "OTHER"
            },
            "meta": {
                "fetched_at": time.time(),
                "source": "dev"
            }
        }

    # -- Live path: fetch from ISMS ERP ---------------------------------------

    # 1. Ensure we have a valid token
    token, expiry, user_id = load_token()
    valid, _ = is_token_valid(token)

    if not token or not valid or not expiry or expiry <= time.time():
        authenticate()
        token, expiry, user_id = load_token()
        valid, _ = is_token_valid(token)
        if not valid:
            raise HTTPException(401, "ISMS ERP authentication failed - check ISMS_USERNAME / ISMS_PASSWORD")

    # 2. Academic years ? find the active one
    ay_raw = isms_get("/api/academic-years/", token)
    years = ay_raw if isinstance(ay_raw, list) else ay_raw.get("results", [])

    active_year = next((y for y in years if y.get("is_active")), None)
    if not active_year and years:
        active_year = years[0]  # fall back to most recent
    if not active_year:
        raise HTTPException(400, "No academic years configured in ISMS ERP")

    # 3. School profile
    sp_raw = isms_get("/api/school-profile/", token)
    profiles = sp_raw if isinstance(sp_raw, list) else sp_raw.get("results", [])
    school = profiles[0] if profiles else {"id": 1, "name": "School"}

    # 4. Class-sections (fetch up to 500 rows)
    cs_raw = isms_get("/api/class-sections/", token, params={"page_size": 500})
    cs_list = cs_raw if isinstance(cs_raw, list) else cs_raw.get("results", [])

    # 5. Normalise into classes/sections/class_sections
    unique_classes: dict = {}
    unique_sections: dict = {}
    class_sections: list = []

    for cs in cs_list:
        cname = str(cs["class_name"])
        sec   = str(cs["section"])
        cs_id = cs["id"]

        if cname not in unique_classes:
            unique_classes[cname] = {"id": cname, "label": cname}
        if sec not in unique_sections:
            unique_sections[sec] = {"id": sec, "label": sec}

        class_sections.append({
            "id":      cs_id,
            "class":   cname,
            "section": sec,
        })

    return {
        "branch": {
            "id":   school.get("id", 1),
            "name": school.get("name", "School"),
        },
        "school": {
            "id":   school.get("id", 1),
            "name": school.get("name", "School"),
        },
        "posting_session": {
            "id":     active_year["id"],
            "label":  active_year["name"],
            "locked": False,
        },
        "masters": {
            "classes":       list(unique_classes.values()),
            "sections":      list(unique_sections.values()),
            "class_sections": class_sections,
        },
        "defaults": {
            "city":           "",
            "state":          "",
            "country":        "India",
            "is_rte":         False,
            "is_new":         True,
            "class_category": "OTHER",
        },
        "meta": {
            "fetched_at": time.time(),
            "source":     "isms_erp",
        },
    }