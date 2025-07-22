# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Keys and settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
