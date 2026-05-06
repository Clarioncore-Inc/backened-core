import asyncio
from alembic import command
from alembic.config import Config
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from app.settings import API_BASE_URL

logging.basicConfig(level=logging.INFO)

scheduler = BackgroundScheduler()


def ping_render():
    if API_BASE_URL:
        try:
            response = requests.get(API_BASE_URL)
            logging.info(
                f"✅ Pinged {API_BASE_URL}, Status: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"❌ Error pinging {API_BASE_URL}: {e}")
    else:
        logging.warning("⚠️ API_BASE_URL is not set!")


scheduler.add_job(ping_render, 'interval', minutes=14)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 LIFESPAN STARTED: Starting scheduler")
    scheduler.start()
    await asyncio.get_event_loop().run_in_executor(None, run_migrations)
    yield
    logging.info("🛑 LIFESPAN ENDED: Stopping scheduler")
    scheduler.shutdown()


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
