import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Correct import: Need func for SQL aggregation
from sqlmodel import select, Session, func 

from app.db import init_db, get_session
# Ensure get_current_user is imported (its definition is in auth.py, which was also corrected)
from app.auth import register_user, authenticate_user, create_token_for_user, get_current_user
from app.schemas import UserCreate, LoginRequest, TokenResponse, GmailScanRequest
from app.oauth_gmail import router as oauth_router
from app.gmail_service import fetch_messages_for_user
from app.ml_utils import predict_texts, load_model, load_tokenizer
from app.email_alert import send_alert
from app.models import Email, User

# Load model/tokenizer globals
MODEL_PATH = os.getenv("MODEL_PATH", "saved/model.keras")
TOKENIZER_PATH = os.getenv("TOKENIZER_PATH", "saved/tokenizer.json")
MAX_LEN = int(os.getenv("MAX_LEN", "200"))

model = None
tokenizer = None

app = FastAPI(title="PhishGuard Pro", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    global model, tokenizer
    init_db()
    # NOTE: Uncomment these two lines once you have successfully trained your ML model 
    # using the corrected train.py script and saved the files.
    model = load_model(MODEL_PATH)
    tokenizer = load_tokenizer(TOKENIZER_PATH)

# include OAuth router
app.include_router(oauth_router)

# ---------- AUTH ----------
@app.post("/auth/register", response_model=dict)
def api_register(req: UserCreate):
    user = register_user(req)
    return {"email": user.email, "id": user.id}

@app.post("/auth/login", response_model=TokenResponse)
def api_login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token_for_user(user)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me")
def api_me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "gmail_connected": bool(current_user.gmail_credentials),
    }

# ---------- PREDICT ----------
@app.post("/predict")
def predict_email(payload: dict, current_user=Depends(get_current_user)):
    if not model or not tokenizer:
        # Prevents crash if model is not loaded (commented out in startup)
        raise HTTPException(status_code=503, detail="ML model not loaded.")
        
    text = payload.get("text", "")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
        
    preds = predict_texts(model, tokenizer, [text], max_len=MAX_LEN)
    score = float(preds[0])
    label = int(score >= 0.5)
    return {"score": score, "label": label}

# ---------- EMAIL SCAN / STATS (FIXED) ----------

@app.get("/emails/stats")
def get_email_stats(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # FIX: Use func.count(Email.id) and the compatible .scalar() method 
    # to retrieve the single count value.

    # Total emails scanned by the user
    total_scanned = session.exec(
        select(func.count(Email.id)) 
        .where(Email.user_id == current_user.id)
    ).scalar() # Fixed SQLModel method

    # Total phishing emails detected for the user
    total_phishing = session.exec(
        select(func.count(Email.id)) 
        .where(Email.user_id == current_user.id)
        .where(Email.label == 1)
    ).scalar() # Fixed SQLModel method

    return {"total_scanned": total_scanned, "total_phishing": total_phishing}

@app.post("/emails/scan")
def scan_emails(
    req: GmailScanRequest,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not current_user.gmail_credentials:
        raise HTTPException(status_code=400, detail="Gmail not connected. Please connect Gmail first")
    if not model or not tokenizer:
        # Prevents crash if model is not loaded (commented out in startup)
        raise HTTPException(status_code=503, detail="ML model not loaded.")

    messages = fetch_messages_for_user(current_user, max_messages=req.max_messages, query=req.query)
    results, phishing_count = [], 0

    for m in messages:
        preds = predict_texts(model, tokenizer, [m.get("snippet", "")], max_len=MAX_LEN)
        score = float(preds[0])
        label = int(score >= 0.5)

        email = Email(
            user_id=current_user.id,
            subject=m["subject"],
            sender=m["sender"],
            snippet=m["snippet"],
            score=score,
            label=label,
        )
        session.add(email)
        results.append(email)

        if label == 1:
            phishing_count += 1
            try:
                send_alert(
                    current_user,
                    suspicious_subject=m["subject"],
                    sender_address=m["sender"],
                    snippet=m["snippet"],
                    score=score,
                )
            except Exception as e:
                print("⚠️ Alert send failed:", e)

    session.commit()
    return {"scanned": len(results), "phishing_detected": phishing_count, "emails": results}

@app.get("/emails/latest")
def get_latest_emails(
    limit: int = 20,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    emails = session.exec(
        select(Email)
        .where(Email.user_id == current_user.id)
        .order_by(Email.created_at.desc())
        .limit(limit)
    ).all()
    return emails
