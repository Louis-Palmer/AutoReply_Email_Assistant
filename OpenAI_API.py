import openai
from config import OPENAI_API_KEY, OPENAI_ASSISTANT_KEY, OPENAI_ASSISTANT_CATEGORISE_KEY
import time
import json


# Set the API key
openai.api_key = OPENAI_API_KEY

def generate_response(prompt: str, system_message: str = "You are a helpful email assistant. You can Sign off with Louis Palmers AI Assistant") -> str:
    """
    Generate a response from the OpenAI Chat API using the provided prompt.
    
    Args:
        prompt (str): The user input or email content to respond to.
        system_message (str): (Optional) Controls assistant behavior.
    
    Returns:
        str: The generated assistant response.
    """

    client = openai(api_key= OPENAI_API_KEY)
    try:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        response = client.chat.completions.create(
            model="gpt-4.1-nano",  # or "gpt-3.5-turbo" if you prefer
            store=True,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"[OpenAI API Error]: {e}")
        return "Sorry, I couldn't generate a response due to an internal error."


def generate_email_reply(email_subject: str, email_body: str, sender_name: str = "the sender") -> str:
    """
    Generate a polite reply to an incoming email using subject and body.
    
    Args:
        email_subject (str): The subject of the email.
        email_body (str): The body of the email.
        sender_name (str): Name of the person who sent the email.
    
    Returns:
        str: A polite and helpful email reply.
    """
    prompt = (
        f"You received an email from {sender_name}.\n\n"
        f"Subject: {email_subject}\n\n"
        f"Body:\n{email_body}\n\n"
        f"Write a clear, concise, and professional reply."
    )

    #return generate_response(prompt)
    return UseAssistant(prompt)




### Function Schema for the assistant to respond too
function_schema = [
    {
        "name": "categorize_and_label_email",
        "description": "Categorizes an email by importance and applies the appropriate label",
        "parameters": {
            "type": "object",
            "properties": {
                "importance": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                }
            },
            "required": ["importance"]
        }
    }
]

def Categorise_Email_Importance_From_Schema(email_subject: str, email_body: str, sender_name: str = "the sender") -> str:
    prompt = (
        f"You received an email from {sender_name}.\n\n"
        f"Subject: {email_subject}\n\n"
        f"Body:\n{email_body}\n\n"
        f"Decide if this email is high, medium, or low importance. "
        f"Call the function categorize_and_label_email with the appropriate label."

    )

    thread = openai.beta.threads.create()

    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=OPENAI_ASSISTANT_KEY,
        tools=[{"type": "function", "function": function_schema[0]}]
    )

    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "requires_action":
            for call in run_status.required_action.submit_tool_outputs.tool_calls:
                if call.function.name == "categorize_and_label_email":
                    args = json.loads(call.function.arguments)
                    result = categorize_and_label_email(**args)

                    openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": call.id,
                            "output": json.dumps(result)
                        }]
                    )
            time.sleep(1)

        elif run_status.status == "completed":
            break

        elif run_status.status in ["failed", "cancelled", "expired"]:
            raise RuntimeError(f"Run failed with status: {run_status.status}")

        else:
            time.sleep(1)
    return result["label"]

def Categorise_Email_Importance(email_subject: str, email_body: str, sender_name: str = "the sender") -> str:
    
    prompt = (
        f"You received an email from {sender_name}.\n\n"
        f"Subject: {email_subject}\n\n"
        f"Body:\n{email_body}\n\n"
    )
    # 1. Create a new thread
    thread = openai.beta.threads.create()

    # 2. Add the user message to the thread
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    # 3. Run the assistant with no tools
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=OPENAI_ASSISTANT_CATEGORISE_KEY  # <- your new assistant ID here
    )

    # 4. Wait for it to finish
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled", "expired"]:
            raise RuntimeError(f"Run failed: {run_status.status}")
        time.sleep(1)

    # 5. Get the assistant's message
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    for msg in messages.data:
        if msg.role == "assistant" and msg.content[0].type == "text":
            return msg.content[0].text.value


def UseAssistant(email_subject: str, email_body: str, sender_name: str = "the sender") -> str:
    prompt = (
        f"You received an email from {sender_name}.\n\n"
        f"Subject: {email_subject}\n\n"
        f"Body:\n{email_body}\n\n"
        f"Write a clear, concise, and professional reply."
    )
    # Create a new thread
    thread = openai.beta.threads.create()

    # Add a message to the thread
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    # Run the Assistant (no tools/functions)
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=OPENAI_ASSISTANT_KEY,
        metadata={"source": "auto-reply-script"}
    )

    # Wait for the run to complete
    while True:
        run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled", "expired"]:
            raise RuntimeError(f"Run failed with status: {run_status.status}")
        else:
            time.sleep(1)

    # Get the Assistant's reply
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    for msg in messages.data:
        if msg.role == "assistant" and msg.content[0].type == "text":
            return msg.content[0].text.value

def categorize_and_label_email(importance: str):
    print()
    print(f"[Action] Labeling as Importance {importance.upper()}")
    # Here you'd call the Gmail API or simulate it
    return {
        "status": "success",
        "label": importance
    }

if __name__ == "__main__":
    #print(generate_email_reply("Job offer from OpenAI", "Hi, we’d love to offer you a role...", "OpenAI HR"))
    #print(Categorise_Email_Importance_From_Schema("Job offer from OpenAI", "Hi, we’d love to offer you a role...", "OpenAI HR"))
    #print(generate_email_reply("Test Subject", "Hi GPT this is a test subject so i want you to respond with the colours that make up a penguin", "Louis Palmer"))
    print(Categorise_Email_Importance("Job offer from OpenAI", "Hi, we’d love to offer you a role...", "OpenAI HR"))