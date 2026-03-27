import httpx
from app.settings import SLACK_ACCESS_TOKEN, SLACK_CHANNEL_ID
import threading
import logging

logger = logging.getLogger(__name__)


class CoreService:

    def __init__(self):
        pass

    def send_email(self, email: str, message: str) -> None:
        print(f"[EMAIL] To: {email}\n{message}")

    def send_slack_message(self, message: str):
        def _post():
            response = httpx.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {SLACK_ACCESS_TOKEN}"},
                json={"channel": SLACK_CHANNEL_ID, "text": message},
            )
            logger.info(
                f"[SLACK] status={response.status_code} body={response.json()}")
        threading.Thread(target=_post, daemon=True).start()
