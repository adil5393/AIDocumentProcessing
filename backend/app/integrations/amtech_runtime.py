
import time
from app.integrations.amtech_auth import load_token, is_token_valid, authenticate

def ensure_amtech_connection():
    token, expiry, user_id, branches = load_token()

    if not token or not user_id or not expiry or expiry <= time.time():
        authenticate()
        token, expiry, user_id, branches = load_token()

    valid, fetched_branches = is_token_valid(token, user_id)

    if not valid:
        authenticate()
        token, expiry, user_id, branches = load_token()
        valid, fetched_branches = is_token_valid(token, user_id)

    return {
        "token": token,
        "user_id": user_id,
        "branches": fetched_branches or branches,
        "expiry": expiry,
        "connected": True
    }