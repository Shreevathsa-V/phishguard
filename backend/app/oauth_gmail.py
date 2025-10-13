import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlmodel import Session

# MODIFIED: Import the new authentication function
from app.auth import get_current_user, create_access_token, get_current_user_from_token
from app.db import get_session
from app.models import User

router = APIRouter()

GOOGLE_CLIENT_SECRETS = os.getenv("GOOGLE_CLIENT_SECRETS", "app/credentials.json")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")

# Gmail scopes (read + send)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Make sure this EXACT URI exists in your Google Cloud Console
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback")


# STEP 1: Start OAuth flow
@router.get("/auth/google")
def initiate_google_auth(current_user=Depends(get_current_user)):
    # FIX: Use the user's token as the state parameter for re-authentication on callback
    temp_token = create_access_token({"sub": current_user.email})

    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=temp_token # Pass the short-lived access token as state
    )
    return {"auth_url": auth_url, "state": state}

# STEP 2: Callback from Google
@router.get("/auth/google/callback")
def google_auth_callback(
    request: Request,
    session: Session = Depends(get_session),
    # REMOVED: current_user=Depends(get_current_user), 
):
    state_token = request.query_params.get("state")
    code = request.query_params.get("code")

    if not code or not state_token:
        raise HTTPException(status_code=400, detail="Missing code or authentication state from Google")
    
    # FIX: Authenticate the user using the token retrieved from the 'state' query parameter
    try:
        current_user = get_current_user_from_token(state_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Could not validate credentials from callback state token")

    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state_token, # Pass original state back to the flow
    )

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        import traceback
        print("⚠️ Google OAuth token exchange failed:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Google token exchange failed: {str(e)}")


    # Save credentials into DB
    credentials = flow.credentials
    # Use current_user.id to fetch the database user
    db_user = session.get(User, current_user.id)
    db_user.gmail_credentials = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    session.add(db_user)
    session.commit()

    return RedirectResponse(url=f"{FRONTEND_URL}?gmail_connected=1")