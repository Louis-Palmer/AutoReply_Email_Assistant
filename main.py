import pickle
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource


#This is what permissions are requested when going through google Auth (Currently only email read permissions)
PERMISSION_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

### Authenitcate_Gmail Handles the checking for already existing credientials and requersting a login if no valid credentials are found
def Authenticate_Gmail():
    user_credentials: Optional[Credentials] = None #this is type hinting which for this case i imported optional
    
    #Checks if the Token.Pickle which is the "last save" of the credientials is present
    if Path("token.pickle").exists():
        with open("token.pickle","rb") as token:
            user_credentials = pickle.load(token)
            print("Credentials found")

    #checks if credentials are not valid
    if not user_credentials or not user_credentials.valid:

        #Refreshes the Token
        if user_credentials and user_credentials.expired and user_credentials.refresh_token:
            user_credentials.refresh(Request())
            print("Credentials Refreshed")
        #Opens the browser to request user to Login to create new token/credentials
        else:
            app_flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file('credentials.json', PERMISSION_SCOPES)
            user_credentials = app_flow.run_local_server(port=0)
            print("No credentials Open Browser to log in")

        #Opens the token file and writes new token to it
        with open("token.pickle","wb") as token:
            pickle.dump(user_credentials,token)
    #Creates a service which is a resource to use the GMail API and returns it
    service = build("gmail","v1",credentials = user_credentials)
    return service
    
#Function to list off unread emails gathered from the API
def List_Unread_Emails(service):
    # Gets the raw API response which is a lot of ramble
    unread_emails =service.users().messages().list(
        userId='me', 
        labelIds=['INBOX'], 
        q='is:unread'
        ).execute()
    #gets the messages metadata
    unread_messages = unread_emails.get("messages",[])

    if not unread_messages:
        print("No Unread Message Found")
    else:
        print(f"Found {len(unread_messages)} unread messages.")
        for msg in unread_messages:
            print(f"Message ID: {msg['id']}")

            #Gets the Content of the indivdual email and prints who its from and the subject 
            #TODO FINISHE
            email_content = service.users().messages().get(userId='me', id = msg['id']).execute()
            email_headers = email_content["payload"]["headers"]
            email_from = next((h["value"] for h in email_headers if h["name"] == "From"), None)
            email_subject =next((h["value"] for h in email_headers if h["name"] == "Subject"), None)
            print(f"Subject: {email_from}")
            print(f"Subject: {email_subject}")

#Runs at launch if file is being ran directly
if __name__ == "__main__":
    gmail_service = Authenticate_Gmail()
    List_Unread_Emails(gmail_service)
    