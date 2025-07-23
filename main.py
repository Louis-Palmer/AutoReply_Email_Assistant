from GMail_API import RunEmailChecker, Send_Email_Reply, Apply_Label_To_Thread
from OpenAI_API import generate_email_reply, Categorise_Email_Importance
from SQLite_Database import is_thread_processed, mark_thread_processed, clear_all_processed
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
        if not is_thread_processed(email.thread_id):
            Catogory = Categorise_Email_Importance(email.subject,email.body,email.sender)
            Apply_Label_To_Thread(email.thread_id, Catogory)
            email.category = Catogory
            mark_thread_processed(email.thread_id)
            print("Marked Thread:  "+ email.thread_id)
        else:
            print("Thread Already Active:  " + email.thread_id)
        


    

if __name__ == "__main__":
    #run_autoreply()
    run_Catogrisation()
