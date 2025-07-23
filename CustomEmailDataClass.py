from dataclasses import dataclass
from datetime import datetime

#Dataclass That we sort the raw data from the GMAILAPI into for ease of use
@dataclass
class EmailData:
    date: datetime
    sender: str
    subject: str
    body: str
    thread_id: str
    category: str

#Dataclass that we use to send off emails
@dataclass  
class SendingEmailData:
    to: str
    subject: str
    body:str
