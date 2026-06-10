"""
USDT (TRC20) payment review tool.

Run inside the app container:

    docker exec -it cryptowrite-app-1 python3 admin_review.py

For each pending USDT payment, fetches the transaction details from
TronScan's public API so you can verify the amount/recipient without
manually opening a block explorer, then lets you approve or reject it.
"""

import os
import sys
from datetime import datetime, timedelta

import httpx
from database import SessionLocal, USDTPayment, User
from payments import SUBSCRIPTION_PRICE_USD_CENTS

USDT_ADDRESS = os.getenv("USDT_ADDRESS_TRC20", "")
TRONSCAN_API = "https://apilist.tronscanapi.com/api/transaction-info"


def fetch_tx_info(tx_hash: str) -> dict | None:
    try:
        resp = httpx.get(TRONSCAN_API, params={"hash": tx_hash}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data or not data.get("hash"):
            return None
        return data
    except Exception as e:
        print(f"  ⚠️  无法从 TronScan 获取交易信息: {e}")
        return None


def print_tx_summary(tx_hash: str, info: dict | None):
    print(f"  TronScan: https://tronscan.org/#/transaction/{tx_hash}")

    if info is None:
        print("  状态: 未找到该交易（可能哈希错误，或链上还未确认）")
        return

    confirmed = info.get("confirmed")
    timestamp = info.get("timestamp")
    when = datetime.utcfromtimestamp(timestamp / 1000).isoformat() if timestamp else "未知"
    print(f"  链上确认: {'是' if confirmed else '否'}")
    print(f"  交易时间(UTC): {when}")

    transfers = info.get("trc20TransferInfo") or []
    if not transfers:
        print("  ⚠️  未在该交易中找到 TRC20 转账记录")
        return

    expected_usd = SUBSCRIPTION_PRICE_USD_CENTS / 100
    for t in transfers:
        symbol = t.get("symbol", "?")
        decimals = t.get("decimals", 6)
        raw_amount = t.get("amount_str", "0")
        try:
            amount = int(raw_amount) / (10 ** decimals)
        except ValueError:
            amount = raw_amount
        to_addr = t.get("to_address", "")
        from_addr = t.get("from_address", "")
        print(f"  转账: {amount} {symbol}")
        print(f"    从: {from_addr}")
        print(f"    到: {to_addr}")

        if USDT_ADDRESS and to_addr != USDT_ADDRESS:
            print(f"  ⚠️  收款地址与配置的 USDT_ADDRESS_TRC20 不一致！(期望: {USDT_ADDRESS})")
        if symbol == "USDT" and isinstance(amount, float) and amount < expected_usd * 0.98:
            print(f"  ⚠️  金额 {amount} 低于订阅价格 ${expected_usd}")


def review_payment(db, payment: USDTPayment):
    user = db.query(User).filter(User.id == payment.user_id).first()
    print("=" * 60)
    print(f"用户: {user.email if user else f'(id={payment.user_id}, 用户不存在)'}")
    print(f"提交时间: {payment.created_at}")
    print(f"TX Hash: {payment.tx_hash}")
    print_tx_summary(payment.tx_hash, fetch_tx_info(payment.tx_hash))

    while True:
        choice = input("\n[a]批准 / [r]拒绝 / [s]跳过 / [q]退出: ").strip().lower()
        if choice == "a":
            payment.status = "verified"
            payment.note = "approved via admin_review.py"
            if user:
                user.is_subscribed = True
                user.subscription_end = datetime.utcnow() + timedelta(days=30)
            db.commit()
            print("✅ 已批准并开通 30 天订阅")
            return "approved"
        elif choice == "r":
            reason = input("拒绝原因: ").strip() or "未说明原因"
            payment.status = "rejected"
            payment.note = f"rejected via admin_review.py: {reason}"
            db.commit()
            print("❌ 已标记为拒绝")
            return "rejected"
        elif choice == "s":
            return "skipped"
        elif choice == "q":
            return "quit"
        else:
            print("请输入 a / r / s / q")


def main():
    db = SessionLocal()
    try:
        pending = db.query(USDTPayment).filter(USDTPayment.status == "pending").order_by(USDTPayment.created_at).all()
        if not pending:
            print("没有待审核的 USDT 支付。")
            return

        print(f"共 {len(pending)} 笔待审核\n")
        for payment in pending:
            result = review_payment(db, payment)
            if result == "quit":
                break
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
