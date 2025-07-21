import pickle
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


PERMISSION_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate_gmail():
    user_credentials: Optional[Credentials] = None
    if Path("token.pickle").exists():
        with open("token.pickle","rb") as token:
            user_credentials = pickle.load(token)

    if not user_credentials or not user_credentials.valid:
        if user_credentials and user_credentials.expired and user_credentials.refresh_token:
            user_credentials.refresh(Request())
        else:
            app_flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file('credentials.json', PERMISSION_SCOPES)
            user_credentials = app_flow.run_local_server(port=0)
        
        with open("token.pickle","wb") as token:
            pickle.dump(user_credentials,token)
    service = build("gmail","v1",credentials = user_credentials)
    return service
    
    
authenticate_gmail()