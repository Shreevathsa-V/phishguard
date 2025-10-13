# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class GmailScanRequest(BaseModel):
    max_messages: int = 20
    query: str = "in:inbox newer_than:7d"
    
class TrainConfig(BaseModel):
    enron_path: str
    sa_path: str
    max_vocab: int
    max_len: int
    batch_size: int
    epochs: int
    lr: float
    val_split: float
    test_split: float
    random_state: int
    model_out: str
    tokenizer_out: str