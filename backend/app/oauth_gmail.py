import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from app.auth import get_current_user
from app.models import User

router = APIRouter()

GOOGLE_CLIENT_SECRETS = os.getenv("GOOGLE_CLIENT_SECRETS", "app/credentials.json")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

@router.get("/auth/google")
async def initiate_google_auth(current_user=Depends(get_current_user)):
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"auth_url": auth_url, "state": state}

@router.get("/auth/google/callback")
async def google_auth_callback(request: Request, current_user=Depends(get_current_user)):
    state = request.query_params.get("state")
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=400, detail="No code returned from Google")

    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state,
    )

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google token exchange failed: {str(e)}")

    credentials = flow.credentials
    user = await User.find_one(User.id == current_user.id)
    user.gmail_credentials = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    await user.save()

    return RedirectResponse(url=f"{FRONTEND_URL}?gmail_connected=1")