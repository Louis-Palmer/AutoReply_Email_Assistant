# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Keys and settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_KEY = os.getenv("OpenAI_Assistants_Key")
OPENAI_ASSISTANT_CATEGORISE_KEY = os.getenv("OpenAI_Assistant_Categorise_Key")
