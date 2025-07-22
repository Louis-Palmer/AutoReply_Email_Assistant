import pickle
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime
from email.mime.text import MIMEText
import base64
from CustomEmailDataClass import EmailData

# Gmail API scope for read-only access to the user's inbox
PERMISSION_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",   # Read/write (mark as read, etc.)
    "https://www.googleapis.com/auth/gmail.send"      # Send email permission
]

### Authenticates the user and returns a Gmail API service instance.
# Handles loading existing credentials, refreshing tokens, or prompting login.
def Authenticate_Gmail_Service():
    user_credentials: Optional[Credentials] = None

    # Load saved credentials if available
    if Path("token.pickle").exists():
        with open("token.pickle", "rb") as token:
            user_credentials = pickle.load(token)
            print("Token found")

    # If credentials are missing or invalid, refresh or prompt login
    if not user_credentials or not user_credentials.valid:
        if user_credentials and user_credentials.expired and user_credentials.refresh_token:
            user_credentials.refresh(Request())
            print("Token refreshed")
        else:
            app_flow = InstalledAppFlow.from_client_secrets_file("credentials.json", PERMISSION_SCOPES)
            user_credentials = app_flow.run_local_server(port=0)
            print("No valid token, browser opened for login")

        # Save the updated credentials
        with open("token.pickle", "wb") as token:
            pickle.dump(user_credentials, token)

    # Build and return the Gmail API service
    return build("gmail", "v1", credentials=user_credentials)


### Retrieves a list of unread emails in the inbox.
# Returns message summaries (IDs and thread IDs) from the Gmail API.
def Fetch_Unread_Email_Summaries(service):
    unread_response = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        q='is:unread'
    ).execute()

    unread_summaries = unread_response.get("messages", [])

    if not unread_summaries:
        print("No unread messages found.")
    else:
        return unread_summaries


### Fetches full message data and extracts key fields into EmailData objects.
# Returns a list of structured email data.
def Parse_Email_Summaries(unread_summaries, service):
    Emails_Store = []
    for i in range(len(unread_summaries)):
        email_content = service.users().messages().get(userId='me', id=unread_summaries[i]['id']).execute()
        email_headers = email_content["payload"]["headers"]

        email_from = next((h["value"] for h in email_headers if h["name"] == "From"), None)
        email_subject = next((h["value"] for h in email_headers if h["name"] == "Subject"), None)
        email_internal_date = datetime.fromtimestamp(int(email_content['internalDate']) / 1000)
        email_thread_id = email_content.get('threadId', '')
        email_body = Extract_Email_Body(email_content)

        Emails_Store.append(EmailData(
            date=email_internal_date,
            sender=email_from,
            subject=email_subject,
            body=email_body,
            thread_id=email_thread_id
        ))

    return Emails_Store


### Extracts and decodes the plain text or HTML body of an email message.
# Falls back to the message snippet if no content is found.
def Extract_Email_Body(email_content):
    def Decode_Base64(data):
        return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="replace")

    Email_Payload = email_content.get("payload", {})

    # Case 1: Simple body
    if "body" in Email_Payload and "data" in Email_Payload["body"]:
        return Decode_Base64(Email_Payload["body"]["data"])

    # Case 2: Multipart email (text/plain or text/html)
    for part in Email_Payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
            return Decode_Base64(part["body"]["data"])
        if part.get("mimeType") == "text/html" and "data" in part.get("body", {}):
            return Decode_Base64(part["body"]["data"])

    # Fallback: return Gmail snippet
    return email_content.get("snippet", "")




def Create_Raw_Email(to:str, subject:str, body:str)->str:
    """
    Creates a raw base64-encoded MIME email message
    """
    message = MIMEText(body)
    message["to"] = to
    message["subject"]=subject

    raw_bytes = message.as_bytes()
    raw_base64 = base64.urlsafe_b64encode(raw_bytes).decode()
    return raw_base64

def Send_Email_Reply(to: str, subject: str, body: str, thread_id: Optional[str] = None):
    """
    Sends an email reply using Gmail API. Optionally replies to an existing thread.
    """
    service = Authenticate_Gmail_Service()
    raw_message = Create_Raw_Email(to, subject, body)

    message = {
        'raw': raw_message
    }

    if thread_id:
        message['threadId'] = thread_id

    try:
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()

        print(f"Email sent to {to} | Message ID: {sent_message['id']}")
        return sent_message

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return None





### Prints the structured unread emails from the inbox.
def Print_Unread_Emails(SortedData):
    email: EmailData
    for email in SortedData:
        print(email.sender)
        print(email.subject)
        print(email.date)
        print(email.body)
        print("-" * 60)


### Initializes Gmail API service and starts the email retrieval process.
def Init_Gmail_Service():
    return Authenticate_Gmail_Service()


def RunEmailChecker():
    gmail_service = Init_Gmail_Service()
    summaries = Fetch_Unread_Email_Summaries(gmail_service)
    sortedData = Parse_Email_Summaries(summaries, gmail_service)
    return sortedData

# Entry point — runs when the file is executed directly.
if __name__ == "__main__":
    gmail_service = Init_Gmail_Service()
    summaries = Fetch_Unread_Email_Summaries(gmail_service)
    sortedData = Parse_Email_Summaries(summaries, gmail_service)
    Print_Unread_Emails(sortedData)
