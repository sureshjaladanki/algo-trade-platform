import os
import sys
from dotenv import load_dotenv
from growwapi import GrowwAPI
from pathlib import Path

# Load existing environment variables from .env
# .parents[2] goes up 3 levels (0 is parent, 1 is grandparent, 2 is great-grandparent)
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


def init_groww_token():
    if os.getenv("GROWW_ACCESS_TOKEN"):
        return os.getenv("GROWW_ACCESS_TOKEN")
    else:
        return get_groww_token()


def get_groww_token():
    """
    Reads Groww API Key and Secret from .env, authenticates,
    and returns the computed ACCESS_TOKEN.
    """
    api_key = os.getenv("GROWW_API_KEY")
    api_secret = os.getenv("GROWW_API_SECRET")

    if not api_key or not api_secret or api_key == "your_api_key_here":
        print(
            "Error: Please set valid GROWW_API_KEY and GROWW_API_SECRET in the .env file."
        )
        sys.exit(1)

    print("Authenticating with Groww API...")

    try:
        # Get access token from growwapi
        access_token = GrowwAPI.get_access_token(api_key=api_key, secret=api_secret)

        print("Authentication successful.")

        # Set it in the current environment for immediate use in the running process
        os.environ["GROWW_ACCESS_TOKEN"] = access_token
        return access_token

    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token = init_groww_token()
    print(f"Computed Token: {token}")
