from beanie import Document
from datetime import datetime
from typing import Optional, Dict

class User(Document):
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str
    gmail_credentials: Optional[Dict] = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"


class Email(Document):
    user_id: str
    subject: Optional[str] = None
    sender: Optional[str] = None
    snippet: Optional[str] = None
    score: float = 0.0
    label: int = 0  # 0 = safe, 1 = phishing
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "emails"