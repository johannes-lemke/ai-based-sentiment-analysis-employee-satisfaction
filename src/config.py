import logging
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ["MODEL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
SECRET_KEY = os.environ["SECRET_KEY"]
BASE_URL = os.environ["BASE_URL"]
API_KEY = os.environ["API_KEY"]

STATIC = Path(__file__).parent / "static"
BERLIN = ZoneInfo("Europe/Berlin")


class ColorFormatter(logging.Formatter):
    GREEN = "\033[32m"
    RESET = "\033[0m"

    def format(self, record):
        text = super().format(record)
        return f"{self.GREEN}{text}{self.RESET}"


def setup_logger():
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(asctime)s %(levelname)s %(message)s"))
    log = logging.getLogger("feedback")
    log.setLevel(logging.INFO)
    log.addHandler(handler)
    log.propagate = False
    return log


logger = setup_logger()
