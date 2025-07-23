from GMail_API import RunEmailChecker, Send_Email_Reply, Apply_Label_To_Thread
from OpenAI_API import generate_email_reply, Categorise_Email_Importance
from CustomEmailDataClass import SendingEmailData

def run_autoreply():
    """
    Cordinates the flow: fetch unread emails, Generates replies, and sends them
    """
    SortedData = RunEmailChecker()
    
    for email in SortedData:
        AIResponseEmail = SendingEmailData(
            to=email.sender,
            subject="RE: "+ email.subject,
            body= generate_email_reply(email.subject, email.body, email.sender)
        )
        #Send_Email_Reply(AIResponseEmail.to, AIResponseEmail.subject,AIResponseEmail.body, email.thread_id)

def run_Catogrisation():
    SortedData = RunEmailChecker() 
    for email in SortedData:
        Catogory = Categorise_Email_Importance(email.subject,email.body,email.sender)
        Apply_Label_To_Thread(email.thread_id, Catogory)


    

if __name__ == "__main__":
    #run_autoreply()
    run_Catogrisation()
