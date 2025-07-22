from GMail_API import RunEmailChecker, Send_Email_Reply
from OpenAI_API import generate_email_reply
from CustomEmailDataClass import SendingEmailData

def run_autoreply():
    """
    Cordinates the flow: fetch unread emails, Generates replies, and sends them
    """
    SortedData = RunEmailChecker()
    
    for email in SortedData:
        AIResponseEmail = SendingEmailData(
            to=None,
            destinationEmail=email.sender,
            subject="RE: "+ email.subject,
            body= generate_email_reply(email.subject, email.body, email.sender)
        )
        Send_Email_Reply(AIResponseEmail.destinationEmail, AIResponseEmail.subject,AIResponseEmail.body, email.thread_id)
        
    

if __name__ == "__main__":
    run_autoreply()
