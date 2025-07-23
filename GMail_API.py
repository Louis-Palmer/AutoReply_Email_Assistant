# Imports for required libraries and modules
import pickle  # For saving/loading credentials
from pathlib import Path  # To check if token file exists
from typing import Optional  # For optional type hints
from google.auth.transport.requests import Request  # To refresh tokens
from google_auth_oauthlib.flow import InstalledAppFlow  # For OAuth2 login flow
from googleapiclient.discovery import build  # To build the Gmail API service
from google.oauth2.credentials import Credentials  # Google OAuth credentials
from datetime import datetime  # To convert timestamp to datetime
from email.mime.text import MIMEText  # To build email message content
import base64  # For encoding/decoding email content
from CustomEmailDataClass import EmailData  # Custom dataclass to store email info

# Scopes define the level of access (read, write, send, etc.) to Gmail
PERMISSION_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",   # Modify inbox (mark read, etc.)
    "https://www.googleapis.com/auth/gmail.send"      # Send emails
]

# Authenticates and returns a Gmail service object.
# Checks for existing credentials, refreshes them if expired, or triggers OAuth login if needed.
def Authenticate_Gmail_Service():
    user_credentials: Optional[Credentials] = None

    # Load credentials from token file if it exists
    if Path("token.pickle").exists():
        with open("token.pickle", "rb") as token:
            user_credentials = pickle.load(token)
            print("Token found")

    # If no valid credentials, refresh or prompt login
    if not user_credentials or not user_credentials.valid:
        if user_credentials and user_credentials.expired and user_credentials.refresh_token:
            user_credentials.refresh(Request())
            print("Token refreshed")
        else:
            app_flow = InstalledAppFlow.from_client_secrets_file("credentials.json", PERMISSION_SCOPES)
            user_credentials = app_flow.run_local_server(port=0)
            print("No valid token, browser opened for login")

        # Save the new credentials to file
        with open("token.pickle", "wb") as token:
            pickle.dump(user_credentials, token)

    # Return an authenticated Gmail service
    return build("gmail", "v1", credentials=user_credentials)


# Retrieves metadata (IDs) for unread emails in the inbox
def Fetch_Unread_Email_Summaries(service):
    unread_response = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],  # Only look in the inbox
        q='is:unread'        # Filter to only unread emails
    ).execute()

    unread_summaries = unread_response.get("messages", [])

    # If no emails found, exit program (can be changed later)
    if not unread_summaries:
        print("No unread messages found.")
        exit()
    else:
        return unread_summaries


# Parses full email content into a list of EmailData objects
def Parse_Email_Summaries(unread_summaries, service):
    Emails_Store = []

    for i in range(len(unread_summaries)):
        # Get full email data using its ID
        email_content = service.users().messages().get(userId='me', id=unread_summaries[i]['id']).execute()
        email_headers = email_content["payload"]["headers"]

        # Extract relevant fields from headers and metadata
        email_from = next((h["value"] for h in email_headers if h["name"] == "From"), None)
        email_subject = next((h["value"] for h in email_headers if h["name"] == "Subject"), None)
        email_internal_date = datetime.fromtimestamp(int(email_content['internalDate']) / 1000)
        email_thread_id = email_content.get('threadId', '')
        email_body = Extract_Email_Body(email_content)

        # Store in a custom dataclass for structured access
        Emails_Store.append(EmailData(
            date=email_internal_date,
            sender=email_from,
            subject=email_subject,
            body=email_body,
            thread_id=email_thread_id,
            category=None  # Placeholder, to be used for AI classification etc.
        ))

    return Emails_Store


# Extracts the plain text or HTML body from an email message
def Extract_Email_Body(email_content):
    def Decode_Base64(data):
        return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="replace")

    Email_Payload = email_content.get("payload", {})

    # Case 1: Simple (non-multipart) message
    if "body" in Email_Payload and "data" in Email_Payload["body"]:
        return Decode_Base64(Email_Payload["body"]["data"])

    # Case 2: Multipart email — try to extract "text/plain" or "text/html"
    for part in Email_Payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
            return Decode_Base64(part["body"]["data"])
        if part.get("mimeType") == "text/html" and "data" in part.get("body", {}):
            return Decode_Base64(part["body"]["data"])

    # Fallback if no body was found — use snippet
    return email_content.get("snippet", "")


# Builds a raw email string to be sent using Gmail API
def Create_Raw_Email(to: str, subject: str, body: str) -> str:
    """
    Creates a raw base64-encoded MIME email message
    """
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw_bytes = message.as_bytes()
    raw_base64 = base64.urlsafe_b64encode(raw_bytes).decode()
    return raw_base64


# Sends an email (reply or new) using Gmail API
def Send_Email_Reply(to: str, subject: str, body: str, thread_id: Optional[str] = None):
    """
    Sends an email reply using Gmail API. Optionally replies to an existing thread.
    """
    service = Authenticate_Gmail_Service()
    raw_message = Create_Raw_Email(to, subject, body)

    message = {
        'raw': raw_message
    }

    # Include thread ID if replying to an existing conversation
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


# Adds a custom label to a conversation thread (e.g., "High", "Low")
def Apply_Label_To_Thread(thread_id: str, importance: str):
    service = Authenticate_Gmail_Service()

    # Format label string properly (capitalized)
    label_name = importance.lower().capitalize()

    # Fetch all current labels
    label_list = service.users().labels().list(userId='me').execute()
    labels = label_list.get("labels", [])

    # Check if label already exists
    label_id = None
    for label in labels:
        if label["name"].lower() == label_name.lower():
            label_id = label["id"]
            break

    # Create label if it doesn’t exist
    if not label_id:
        label_obj = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
        created_label = service.users().labels().create(userId='me', body=label_obj).execute()
        label_id = created_label["id"]

    # Apply label to the specified thread
    service.users().threads().modify(
        userId='me',
        id=thread_id,
        body={
            "addLabelIds": [label_id],
            # Optionally remove from inbox:
            # "removeLabelIds": ["INBOX"]
        }
    ).execute()

    print(f"✅ Thread {thread_id} labeled as '{label_name}'")


# Utility to print the parsed list of unread emails
def Print_Unread_Emails(SortedData):
    email: EmailData
    for email in SortedData:
        print(email.sender)
        print(email.subject)
        print(email.date)
        print(email.body)
        print("-" * 60)


# Orchestrates fetching unread email content
def RunEmailChecker():
    gmail_service = Authenticate_Gmail_Service()
    summaries = Fetch_Unread_Email_Summaries(gmail_service)
    sortedData = Parse_Email_Summaries(summaries, gmail_service)
    return sortedData


# If run directly, fetch unread emails and print them
if __name__ == "__main__":
    gmail_service = Authenticate_Gmail_Service()
    summaries = Fetch_Unread_Email_Summaries(gmail_service)
    sortedData = Parse_Email_Summaries(summaries, gmail_service)


    Print_Unread_Emails(sortedData)
