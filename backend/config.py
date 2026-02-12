import sys
import os
from dotenv import load_dotenv
import logging


class Config:
    def __init__(self):
        load_dotenv()
        self.ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
        self.YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")
        self.APP_ID = os.getenv("APP_ID")
        self.APP_SECRET = os.getenv("APP_SECRET")
        self.RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
        self.VERSION = os.getenv("VERSION")
        self.PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
        self.VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


# Global config instance
config = Config()


def load_configurations(app):
    # For FastAPI, we'll use the global config instance
    pass


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
