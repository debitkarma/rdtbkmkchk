import praw
import os
from dotenv import load_dotenv
from typing import Dict, Union


def load_env() -> Union[Dict[str, str], None]:
    creds = {
        "client_id": os.getenv("CLIENT_ID"),
        "secret": os.getenv("SECRET"),
        "password": os.getenv("PASSWORD"),
        "username": os.getenv("USERNAME"),
        "user_agent": os.getenv("USER_AGENT"),
    }
    for key in creds.keys():
        if not creds[key]:
            return None
    return creds


def authenticated(creds: dict) -> bool:
    rdt = praw.Reddit(*creds)
    return rdt.user.me()


def test_loading_env():
    load_dotenv()
    creds = load_env()
    print(creds["username"])


if __name__ == "__main__":
    test_loading_env()
