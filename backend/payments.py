import os
from datetime import datetime, timedelta

import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

SUBSCRIPTION_PRICE_USD_CENTS = 888  # $8.88
FREE_USES = 5


def create_stripe_checkout(user_id: int, user_email: str, base_url: str) -> str:
    session = stripe.checkout.Session.create(
        customer_email=user_email,
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "CryptoWrite 订阅",
                        "description": "AI 驱动的加密内容工厂 · 无限生成",
                    },
                    "recurring": {"interval": "month"},
                    "unit_amount": SUBSCRIPTION_PRICE_USD_CENTS,
                },
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url=f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&user_id={user_id}",
        cancel_url=f"{base_url}/?payment=cancelled",
        metadata={"user_id": str(user_id)},
    )
    return session.url


def verify_stripe_session(session_id: str) -> dict | None:
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid" or session.status == "complete":
            return {
                "user_id": int(session.metadata.get("user_id", 0)),
                "customer_id": session.customer,
                "subscription_id": session.subscription,
            }
    except stripe.error.StripeError:
        pass
    return None


def get_subscription_end(subscription_id: str) -> datetime | None:
    try:
        sub = stripe.Subscription.retrieve(subscription_id)
        return datetime.utcfromtimestamp(sub.current_period_end)
    except stripe.error.StripeError:
        return datetime.utcnow() + timedelta(days=30)
