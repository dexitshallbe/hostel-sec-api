import os
from dotenv import load_dotenv

load_dotenv()

def database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and set it.")
    return url