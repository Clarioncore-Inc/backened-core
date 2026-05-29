import os
import asyncio
from alembic import command
from alembic.config import Config
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from app.core.dependency_injection import service_locator
from app.database import SessionLocal
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
    await asyncio.get_event_loop().run_in_executor(None, seed_app_settings)
    yield
    logging.info("🛑 LIFESPAN ENDED: Stopping scheduler")
    scheduler.shutdown()


def run_migrations():
    if os.getenv("RUN_MIGRATIONS", "false").lower() != "true":
        return
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def seed_app_settings():
    db = SessionLocal()
    try:
        settings = service_locator.general_service.seed_app_settings(db=db)
        if settings is None:
            logging.warning(
                "⚠️ Skipping AppSettings seed because the app_settings table does not exist yet"
            )
            return
        logging.info("✅ App settings seeded")
    finally:
        db.close()
