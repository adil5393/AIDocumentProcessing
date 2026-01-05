def get_amtech_masters_internal():
    import time
    from fastapi import HTTPException
    from app.integrations.amtech_auth import load_token, is_token_valid, authenticate
    from app.integrations.amtech_client import amtech_get
    from app.integrations.build_admission_payload import build_dummy_admission_payload
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    AMTECH_BASE_URL_EXTENSION=os.getenv("AMTECH_BASE_URL_EXTENSION")
    CLASSES_ENDPOINT = os.getenv("CLASSES_ENDPOINT")
    SECTION_ENDPOINT = os.getenv("SECTION_ENDPOINT")
    CLASSSECTION_ENDPOINT = os.getenv("CLASSSECTION_ENDPOINT")
    SESSION_ENDPOINT = os.getenv("SESSION_ENDPOINT")
    
    # 1. Ensure token
    token, expiry, user_id, branches = load_token()

    valid, fetched_branches = is_token_valid(token, user_id)
    if not token or not valid or not expiry or expiry <= time.time():
        authenticate()
        token, expiry, user_id, branches = load_token()
        valid, fetched_branches = is_token_valid(token, user_id)

        if not valid:
            raise HTTPException(401, "Amtech authentication failed")

    branches = fetched_branches or branches
    if not branches:
        raise HTTPException(400, "No branches available")

    # 2. Lock branch
    branch = branches[0]
    branch_id = branch["branch"]["master_id"]
    branch_name = branch["branch"]["branch_name"]
    school = branch["school"]

    # 3. Fetch masters
    sessions = amtech_get(
        f"{AMTECH_BASE_URL_EXTENSION}{SESSION_ENDPOINT}",
        token,
        params={"branch": branch_id}
    )

    classes = amtech_get(
        f"{AMTECH_BASE_URL_EXTENSION}{CLASSES_ENDPOINT}",
        token,
        params={"branch": branch_id}
    )

    sections = amtech_get(
        f"{AMTECH_BASE_URL_EXTENSION}{SECTION_ENDPOINT}",
        token,
        params={"branch": branch_id}
    )

    class_sections = amtech_get(
        f"{AMTECH_BASE_URL_EXTENSION}{CLASSSECTION_ENDPOINT}",
        token,
        params={
            "branch": branch_id,
            "model": "class-class_name,section-section_name",
            "fields": "class_section_id"
        }
    )

    # 4. Normalize
    payload = {
        "branch": {
            "id": branch_id,
            "name": branch_name
        },
        "school": {
            "id": school["master_id"],
            "name": school["school_name"]
        },
        "posting_session": {
            "id": 4,
            "label": "2026-2027",
            "locked": True
        },
        "masters": {
            "classes": [
                {"id": c["class_id"], "label": c["class_name"]}
                for c in classes["data"]
                if c["class_name"] != "NULL"
            ],
            "sections": [
                {"id": s["section_id"], "label": s["section_name"]}
                for s in sections["data"]
            ],
            "class_sections": [
                {
                    "id": cs["class_section_id"],
                    "class": cs["class"]["class_name"],
                    "section": cs["section"]["section_name"]
                }
                for cs in class_sections["data"]
                if cs["class"]["class_name"] != "NULL"
            ]
        },
        "defaults": {
            "city": "Pratapgarh",
            "state": "Uttar Pradesh",
            "country": "India",
            "is_rte": False,
            "is_new": True,
            "class_category": "OTHER"
        },
        "meta": {
            "fetched_at": time.time(),
            "source": "amtech"
        }
    }
    return payload