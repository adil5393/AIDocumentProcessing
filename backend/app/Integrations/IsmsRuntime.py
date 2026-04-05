
import time
import os
from dotenv import load_dotenv

load_dotenv()


def ensure_isms_connection():
    """
    Guarantee a valid ISMS ERP token is cached and return connection state.

    Returns a dict with:
      token, user_id, expiry, connected (True)
    """
    from App.Integrations.IsmsAuth import load_token, is_token_valid, authenticate

    DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

    if DEV_MODE:
        return {
            "token":   "dev-token",
            "user_id": "dev-user",
            "expiry":  time.time() + 3600,
            "connected": True,
        }

    token, expiry, user_id = load_token()

    if not token or not user_id or not expiry or expiry <= time.time():
        authenticate()
        token, expiry, user_id = load_token()

    valid, _ = is_token_valid(token)

    if not valid:
        authenticate()
        token, expiry, user_id = load_token()

    return {
        "token":   token,
        "user_id": user_id,
        "expiry":  expiry,
        "connected": True,
    }
