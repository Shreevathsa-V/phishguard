import os, json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.db import get_session
from app.models import User
from sqlmodel import select

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]

def get_user_creds(user: User):
    info = user.gmail_credentials
    if not info:
        raise FileNotFoundError("User has not connected Gmail account")
    creds = Credentials(
        token=info.get("token"),
        refresh_token=info.get("refresh_token"),
        token_uri=info.get("token_uri"),
        client_id=info.get("client_id"),
        client_secret=info.get("client_secret"),
        scopes=info.get("scopes", SCOPES)
    )
    # refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # after refresh, update DB
        with get_session() as session:
            db_user = session.exec(select(User).where(User.email == user.email)).first()
            db_user.gmail_credentials = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes
            }
            session.add(db_user)
            session.commit()
    return creds

def build_gmail_service_for_user(user: User):
    creds = get_user_creds(user)
    service = build("gmail", "v1", credentials=creds)
    return service

def fetch_messages_for_user(user: User, max_messages=20, query="in:inbox newer_than:7d"):
    svc = build_gmail_service_for_user(user)
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_messages).execute()
    messages = resp.get("messages", [])
    out = []
    for m in messages:
        mid = m["id"]
        msg = svc.users().messages().get(userId="me", id=mid, format="full").execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "(unknown)")
        snippet = msg.get("snippet", "")
        out.append({"id": mid, "subject": subject, "sender": sender, "snippet": snippet})
    return out

def send_message_for_user(user: User, raw_message):
    svc = build_gmail_service_for_user(user)
    return svc.users().messages().send(userId="me", body=raw_message).execute()
