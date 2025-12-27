import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN_FILE = "token_cache.json"
TOKEN_EXPIRY_FILE = "token_expiry.json"

BASE_URL = os.getenv("BASE_URL")
LOGIN_URL = f"{BASE_URL}/sms/auth/login"

TOKEN_VALIDATION_URL = f"{BASE_URL}/sms/userschool/"

AMTECH_USERNAME = os.getenv("AMTECH_USERNAME")
AMTECH_PASSWORD = os.getenv("AMTECH_PASSWORD")

print(AMTECH_USERNAME)


def save_token(token, expires_in_seconds, user_id, branches=None):
    expiry = time.time() + expires_in_seconds

    with open(TOKEN_FILE, "w") as f:
        json.dump({
            "token": token,
            "user_id": user_id,
            "branches": branches or []
        }, f)

    with open(TOKEN_EXPIRY_FILE, "w") as f:
        json.dump({"expiry": expiry}, f)

def load_token():
    if not os.path.exists(TOKEN_FILE) or not os.path.exists(TOKEN_EXPIRY_FILE):
        return None, None, None, None

    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
        token = data["token"]
        user_id = data["user_id"]
        branches = data.get("branches", [])

    with open(TOKEN_EXPIRY_FILE, "r") as f:
        expiry = json.load(f)["expiry"]

    return token, expiry, user_id, branches

def is_token_valid(token, user_id):
    if not token or not user_id:
        return False, None

    url = f"{TOKEN_VALIDATION_URL}{user_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://amtech-school.com",
        "Referer": "https://amtech-school.com/",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    print("VALIDATION STATUS:", response.status_code, response.text)

    if response.status_code != 200:
        return False, None

    data = response.json()
    branches = data["data"]["userSchool"]

    return True, branches


def authenticate():
    token, expiry, user_id, branches = load_token()

    valid, fetched_branches = is_token_valid(token, user_id)
    print(valid)

    if token and expiry > time.time() and valid:
        # Save branches if missing
        if not branches and fetched_branches:
            save_token(token, expiry - time.time(), user_id, fetched_branches)
        return token

    # 🔐 Login again
    login_payload = {
        "username": AMTECH_USERNAME,
        "password": AMTECH_PASSWORD
    }

    response = requests.post(LOGIN_URL, json=login_payload)

    if response.status_code in (200, 201):
        data = response.json()
        token = data["token"]
        user_id = data["user"]["user_id"]

        # fetch branches immediately
        valid, branches = is_token_valid(token, user_id)

        expires = 60 * 60 * 24 * 30
        save_token(token, expires, user_id, branches)

        return token

    raise Exception(f"Auth failed: {response.text}")
