import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_subscribed = Column(Boolean, default=False)
    subscription_end = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    free_uses_remaining = Column(Integer, default=5)


class USDTPayment(Base):
    __tablename__ = "usdt_payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    tx_hash = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / verified / rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, nullable=True)


def create_tables():
    os.makedirs("./data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
