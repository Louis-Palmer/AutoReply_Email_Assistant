from openai import OpenAI
from config import OPENAI_API_KEY

# Set the API key
OpenAI.api_key = OPENAI_API_KEY

def generate_response(prompt: str, system_message: str = "You are a helpful email assistant. You can Sign off with Louis Palmers AI Assistant") -> str:
    """
    Generate a response from the OpenAI Chat API using the provided prompt.
    
    Args:
        prompt (str): The user input or email content to respond to.
        system_message (str): (Optional) Controls assistant behavior.
    
    Returns:
        str: The generated assistant response.
    """

    client = OpenAI(api_key= OPENAI_API_KEY)
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

    return generate_response(prompt)


if __name__ == "__main__":
    print(generate_email_reply("Test Subject", "Hi GPT this is a test subject so i want you to respond with the colours that make up a penguin", "Louis Palmer"))
