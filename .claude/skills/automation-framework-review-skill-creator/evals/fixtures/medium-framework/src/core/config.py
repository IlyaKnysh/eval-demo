"""Environment-driven configuration for the SubTrack admin test suite.

Almost every credential/secret is sourced from the environment (see
.env.example), loaded here via python-dotenv. This keeps real credentials out
of source control everywhere except one spot -- see the note below.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_URL = os.getenv("SUBTRACK_BASE_URL", "https://admin.subtrack.staging.example.com")
    API_BASE_URL = os.getenv("SUBTRACK_API_BASE_URL", "https://api.subtrack.staging.example.com")

    ADMIN_USERNAME = os.getenv("SUBTRACK_ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("SUBTRACK_ADMIN_PASSWORD")

    API_TOKEN = os.getenv("SUBTRACK_API_TOKEN")

    # Hardcoded plaintext-looking fake credential committed directly here
    # instead of going through the .env / os.getenv mechanism used by every
    # other credential in this class. Inconsistent with the rest of the file.
    INVOICING_PROVIDER_API_KEY = "sk-fake1234567890"

    DEFAULT_TIMEOUT_MS = 10_000
