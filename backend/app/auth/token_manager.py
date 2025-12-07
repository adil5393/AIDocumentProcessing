import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
USERNAME = os.getenv("AMTECH_USERNAME")
PASSWORD = os.getenv("AMTECH_PASSWORD")

TOKEN_FILE = "token_cache.json"
EXPIRY_FILE= "token_expiry.json"


def load_cached_token():
    if not os.path.exists(TOKEN_FILE):
        return None, 0
    try:
        with open(TOKEN_FILE, "r") as f:
            token, expiry = f.read().split("|")
            return token, float(expiry)
    except:
        return None, 0


def save_token(token, expiry):
    with open(TOKEN_FILE, "w") as f:
        f.write(f"{token}")
    with open(EXPIRY_FILE, "w") as f:
        f.write(f"{expiry}")


def request_new_token():
    url = f"{BASE_URL}/auth/login"
    response = requests.post(url, json={"username": USERNAME, "password": PASSWORD})

    if response.status_code not in (200, 201):
        raise Exception(f"Login failed: {response.status_code} {response.text}")

    data = response.json()

    token = data["token"] if "token" in data else data.get("accessToken")
    expiry = time.time() + (24 * 60 * 60)  # safe default: token valid for 24h

    save_token(token, expiry)
    return token


def get_token():
    token, expiry = load_cached_token()

    if not token or time.time() > expiry:
        # expired or missing → renew
        return request_new_token()

    return token
