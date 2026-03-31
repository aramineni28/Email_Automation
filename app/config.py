import os
from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DATABASE_URL = "postgresql://postgres:postgres@recruiter_db:5432/recruiters"