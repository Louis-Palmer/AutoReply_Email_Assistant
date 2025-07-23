from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailData:
    date: datetime
    sender: str
    subject: str
    body: str
    thread_id: str

@dataclass
class SendingEmailData:
    to: str
    subject: str
    body:str
