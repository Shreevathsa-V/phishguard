import base64
from email.mime.text import MIMEText
from app.gmail_service import send_message_for_user

def make_raw_message(to_email: str, from_email: str, subject: str, body_text: str):
    msg = MIMEText(body_text, "plain")
    msg["to"] = to_email
    msg["from"] = from_email
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}

def send_alert(user, suspicious_subject: str, sender_address: str, snippet: str, score: float):
    from_email = user.email
    subj = "⚠️ PhishGuard Alert — Suspicious email detected"
    body = f"""PhishGuard detected a suspicious email in your inbox.

Sender: {sender_address}
Subject: {suspicious_subject}
Snippet: {snippet}
Score: {score:.4f}

Please review this message in your inbox.
"""
    raw = make_raw_message(to_email=user.email, from_email=from_email, subject=subj, body_text=body)
    return send_message_for_user(user, raw)
