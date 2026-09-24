import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


config = Config()
