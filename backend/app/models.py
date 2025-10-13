from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str
    gmail_credentials: Optional[dict] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Email(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    subject: Optional[str] = None
    sender: Optional[str] = None
    snippet: Optional[str] = None
    score: float = 0.0
    label: int = 0  # 0 = safe, 1 = phishing
    created_at: datetime = Field(default_factory=datetime.utcnow)
