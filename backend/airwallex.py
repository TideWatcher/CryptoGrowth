import hashlib
import hmac
import os
import time

import httpx

AIRWALLEX_CLIENT_ID = os.getenv("AIRWALLEX_CLIENT_ID", "")
AIRWALLEX_API_KEY = os.getenv("AIRWALLEX_API_KEY", "")
AIRWALLEX_WEBHOOK_SECRET = os.getenv("AIRWALLEX_WEBHOOK_SECRET", "")
AIRWALLEX_ENV = os.getenv("AIRWALLEX_ENV", "demo")  # "prod" or "demo" (sandbox)

BASE_URL = "https://api.airwallex.com" if AIRWALLEX_ENV == "prod" else "https://api-demo.airwallex.com"

_token_cache = {"token": None, "expires_at": 0.0}


def _get_token() -> str:
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 30:
        return _token_cache["token"]

    resp = httpx.post(
        f"{BASE_URL}/api/v1/authentication/login",
        headers={
            "x-client-id": AIRWALLEX_CLIENT_ID,
            "x-api-key": AIRWALLEX_API_KEY,
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["token"]
    _token_cache["expires_at"] = now + 25 * 60
    return _token_cache["token"]


def create_payment_link(user_id: int, base_url: str) -> str:
    from payments import SUBSCRIPTION_PRICE_USD_CENTS

    token = _get_token()
    amount = SUBSCRIPTION_PRICE_USD_CENTS / 100

    resp = httpx.post(
        f"{BASE_URL}/api/v1/pa/payment_links/create",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "amount": amount,
            "currency": "USD",
            "title": "CryptoWrite 订阅（1个月）",
            "description": "AI 驱动的加密内容工厂 · 30 天无限生成",
            "reusable": False,
            "reference": f"user_{user_id}",
            "metadata": {"user_id": str(user_id)},
            "return_url": f"{base_url}/payment/success?provider=airwallex&user_id={user_id}",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["url"]


def verify_webhook_signature(raw_body: bytes, timestamp: str, signature: str) -> bool:
    if not AIRWALLEX_WEBHOOK_SECRET:
        return True
    if not timestamp or not signature:
        return False
    payload = timestamp.encode() + raw_body
    expected = hmac.new(AIRWALLEX_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
