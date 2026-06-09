import os
from datetime import datetime
from pathlib import Path

import anthropic
import stripe
from auth import (
    GOOGLE_CLIENT_ID,
    GOOGLE_REDIRECT_URI,
    create_access_token,
    decode_token,
    get_google_user_info,
    hash_password,
    verify_password,
)
from database import User, USDTPayment, create_tables, get_db
from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from payments import (
    FREE_USES,
    create_stripe_checkout,
    get_subscription_end,
    verify_stripe_session,
)
from prompts import build_prompt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

load_dotenv()
create_tables()

app = FastAPI(title="CryptoWrite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

USDT_ADDRESS = os.getenv("USDT_ADDRESS_TRC20", "")


# ── helpers ──────────────────────────────────────────────────────────────────

def get_current_user(
    auth_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    if not auth_token:
        return None
    user_id = decode_token(auth_token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_user(user: User | None = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def user_can_generate(user: User) -> bool:
    if user.is_subscribed and user.subscription_end and user.subscription_end > datetime.utcnow():
        return True
    return user.free_uses_remaining > 0


def set_auth_cookie(response, token: str):
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        samesite="lax",
        secure=False,  # set True in production with HTTPS
    )


# ── static / pages ────────────────────────────────────────────────────────────

@app.get("/")
async def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "CryptoWrite API"}


@app.get("/payment/success")
async def payment_success_page():
    index = FRONTEND_DIR / "index.html"
    return FileResponse(str(index))


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        name=req.name or req.email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    resp = JSONResponse({"ok": True, "user": _user_dict(user)})
    set_auth_cookie(resp, token)
    return resp


@app.post("/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = create_access_token(user.id)
    resp = JSONResponse({"ok": True, "user": _user_dict(user)})
    set_auth_cookie(resp, token)
    return resp


@app.post("/auth/logout")
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("auth_token")
    return resp


@app.get("/auth/me")
async def me(user: User | None = Depends(get_current_user)):
    if not user:
        return JSONResponse({"logged_in": False})
    return {"logged_in": True, "user": _user_dict(user)}


@app.get("/auth/google")
async def google_login():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google 登录未配置")
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url)


@app.get("/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    info = await get_google_user_info(code)
    if not info:
        return RedirectResponse("/?error=google_failed")
    user = db.query(User).filter(User.google_id == info["id"]).first()
    if not user:
        user = db.query(User).filter(User.email == info["email"]).first()
        if user:
            user.google_id = info["id"]
        else:
            user = User(
                email=info["email"],
                google_id=info["id"],
                name=info.get("name"),
            )
            db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    resp = RedirectResponse("/")
    set_auth_cookie(resp, token)
    return resp


# ── generate ──────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    raw_material: str
    content_types: list[str] = ["wechat", "twitter"]
    styles: list[str] = ["kol"]
    language: str = "zh"
    wechat_length: str = "1000-1500"
    twitter_length: str = "5"


@app.post("/api/generate")
async def generate(req: GenerateRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    if not user_can_generate(user):
        raise HTTPException(
            status_code=402,
            detail={
                "code": "subscription_required",
                "message": "免费次数已用完，请订阅后继续使用",
                "free_uses": 0,
            },
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    if not req.raw_material.strip():
        raise HTTPException(status_code=400, detail="raw_material is required")

    system_prompt, user_prompt = build_prompt(
        raw_material=req.raw_material,
        content_types=req.content_types,
        styles=req.styles,
        language=req.language,
        wechat_length=req.wechat_length,
        twitter_length=req.twitter_length,
    )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # deduct free use if not subscribed
    is_subscribed = user.is_subscribed and user.subscription_end and user.subscription_end > datetime.utcnow()
    if not is_subscribed:
        user.free_uses_remaining = max(0, user.free_uses_remaining - 1)
        db.commit()
        db.refresh(user)

    return {
        "content": message.content[0].text,
        "free_uses_remaining": user.free_uses_remaining,
        "is_subscribed": bool(is_subscribed),
    }


# ── payments ──────────────────────────────────────────────────────────────────

@app.post("/payments/stripe/checkout")
async def stripe_checkout(request: Request, user: User = Depends(require_user)):
    base_url = str(request.base_url).rstrip("/")
    try:
        url = create_stripe_checkout(user.id, user.email, base_url)
        return {"url": url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/payments/stripe/verify")
async def stripe_verify(session_id: str, user_id: int, db: Session = Depends(get_db)):
    data = verify_stripe_session(session_id)
    if not data or data["user_id"] != user_id:
        return RedirectResponse("/?payment=failed")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse("/?payment=failed")
    user.is_subscribed = True
    user.stripe_customer_id = data["customer_id"]
    user.stripe_subscription_id = data["subscription_id"]
    if data["subscription_id"]:
        user.subscription_end = get_subscription_end(data["subscription_id"])
    db.commit()
    return RedirectResponse("/?payment=success")


@app.post("/payments/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
        else:
            event = stripe.Event.construct_from({"type": "unknown"}, stripe.api_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook")

    if event["type"] == "customer.subscription.deleted":
        sub_id = event["data"]["object"]["id"]
        user = db.query(User).filter(User.stripe_subscription_id == sub_id).first()
        if user:
            user.is_subscribed = False
            db.commit()
    elif event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        user = db.query(User).filter(User.stripe_subscription_id == sub["id"]).first()
        if user:
            user.subscription_end = datetime.utcfromtimestamp(sub["current_period_end"])
            user.is_subscribed = sub["status"] == "active"
            db.commit()

    return {"ok": True}


class USDTRequest(BaseModel):
    tx_hash: str


@app.post("/payments/usdt/submit")
async def usdt_submit(req: USDTRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    payment = USDTPayment(user_id=user.id, tx_hash=req.tx_hash.strip())
    db.add(payment)
    db.commit()
    return {"ok": True, "message": "已提交，人工审核通常在 24 小时内完成"}


@app.get("/payments/usdt/address")
async def usdt_address():
    return {"address": USDT_ADDRESS, "network": "TRC20"}


# ── utils ─────────────────────────────────────────────────────────────────────

def _user_dict(user: User) -> dict:
    is_subscribed = (
        user.is_subscribed
        and user.subscription_end is not None
        and user.subscription_end > datetime.utcnow()
    )
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "free_uses_remaining": user.free_uses_remaining,
        "is_subscribed": is_subscribed,
        "subscription_end": user.subscription_end.isoformat() if user.subscription_end else None,
        "has_google": bool(user.google_id),
    }
