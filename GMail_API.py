import pickle
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource
from dataclasses import dataclass
from datetime import datetime
import base64
import sys


#Creating a data class to make it easier to manage the emails
@dataclass
class EmailData:
    date: datetime
    sender: str
    subject: str
    body: str
    thread_id: str


#This is what permissions are requested when going through google Auth (Currently only email read permissions)
PERMISSION_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

### Authenitcate_Gmail Handles the checking for already existing credientials and requersting a login if no valid credentials are found
def Authenticate_Gmail():
    user_credentials: Optional[Credentials] = None #this is type hinting which for this case i imported optional
    
    #Checks if the Token.Pickle which is the "last save" of the credientials is present
    if Path("token.pickle").exists():
        with open("token.pickle","rb") as token:
            user_credentials = pickle.load(token)
            print("Token found")

    #checks if credentials are not valid
    if not user_credentials or not user_credentials.valid:

        #Refreshes the Token
        if user_credentials and user_credentials.expired and user_credentials.refresh_token:
            user_credentials.refresh(Request())
            print("Token Refreshed")
        #Opens the browser to request user to Login to create new token/credentials
        else:
            app_flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file('credentials.json', PERMISSION_SCOPES)
            user_credentials = app_flow.run_local_server(port=0)
            print("No Login Open Browser to log in")

        #Opens the token file and writes new token to it
        with open("token.pickle","wb") as token:
            pickle.dump(user_credentials,token)
    #Creates a service which is a resource to use the GMail API and returns it
    service = build("gmail","v1",credentials = user_credentials)
    return service
    
###Function to list off unread emails gathered from the API
def List_Unread_Emails(service):
    #Gets metadata for unread emails, including message and thread ID, and additional data
    unread_response =service.users().messages().list(
        userId='me', 
        labelIds=['INBOX'], 
        q='is:unread'
        ).execute()
    #Extracts only the unread emails summaries(ID and thread ID)
    unread_summaries = unread_response.get("messages",[])

    if not unread_summaries:
        print("No Unread Message Found")
    else:
        return unread_summaries

###Function that extracts the important details from the Email
def Sort_Unread_Summaries(unread_summaries, service):
    Emails_Store = []
    for i in range(len(unread_summaries)):
            email_content = service.users().messages().get(userId='me', id = unread_summaries[i]['id']).execute()
            email_headers = email_content["payload"]["headers"]
            email_from = next((h["value"] for h in email_headers if h["name"] == "From"), None)
            email_subject =next((h["value"] for h in email_headers if h["name"] == "Subject"), None)
            email_internal_date = datetime.fromtimestamp(int(email_content['internalDate']) / 1000)
            email_thread_id = email_content.get('threadId', '')
            email_body = Extract_Body(email_content)
            #email_body = None


            Emails_Store.append(EmailData(
                date=email_internal_date,
                sender=email_from,
                subject=email_subject,
                body=email_body,
                thread_id=email_thread_id
            ))
    return Emails_Store


def Extract_Body(email_content):
    def Decode_Base64(data): #Helper Function
        return base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8",errors="replace")
    Email_Payload = email_content.get("payload",{})

    #cover plain text emails that have no alternative formats or attachments
    if "body" in Email_Payload and "data" in Email_Payload["body"]:
        return Decode_Base64(Email_Payload["body"]["data"])
    
    for part in Email_Payload.get("parts",[]):
        if part.get("mimeType") == "text/plain" and "data" in part.get("body",{}):
            return Decode_Base64(part["body"]["data"])
        
        if part.get("mimeType") == "text/html" and "data" in part.get("body",{}):
            return Decode_Base64(part["body"]["data"])
        
    return email_content.get("snippet","")


def GetEmails(gmail_service):
    if not gmail_service:
        Startup_GetService()
    else:
        summaries = List_Unread_Emails(gmail_service)
        SortedData = Sort_Unread_Summaries(summaries,gmail_service)

        email :EmailData
        for email in SortedData:
            print(email.sender)
            print(email.subject)
            print(email.date)
            print(email.body)








def Startup_GetService():
    #gmail_service = Authenticate_Gmail()
    return Authenticate_Gmail()

        



#Runs at launch if file is being ran directly
if __name__ == "__main__":
    gmail_service = Startup_GetService()
    GetEmails(gmail_service)
    #gmail_service = Authenticate_Gmail()
    #summaries = List_Unread_Emails(gmail_service)



