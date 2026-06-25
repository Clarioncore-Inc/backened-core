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


def check_pending_bookings_reminder():
    db = SessionLocal()
    try:
        reminder_count = service_locator.psychologist_service.check_pending_bookings_reminder(
            db=db
        )
        if reminder_count:
            logging.info(
                "✅ Sent pending booking reminder for %s overdue booking(s)",
                reminder_count,
            )
    except Exception:
        logging.exception("❌ Failed to process pending booking reminders")
    finally:
        db.close()


scheduler.add_job(ping_render, 'interval', minutes=14)
scheduler.add_job(check_pending_bookings_reminder, 'interval', minutes=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 LIFESPAN STARTED: Starting scheduler")
    scheduler.start()
    await asyncio.get_event_loop().run_in_executor(None, run_migrations)
    await asyncio.get_event_loop().run_in_executor(None, seed_app_settings)
    await asyncio.get_event_loop().run_in_executor(None, seed_genius_profiles)
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


def seed_genius_profiles():
    from app.admin_panel.models import GeniusProfile, _iq_label, _iq_note
    from app.admin_panel.genius_seed_data import GENIUS_SEEDS

    db = SessionLocal()
    try:
        existing = db.query(GeniusProfile).count()
        if existing > 0:
            return
        for seed in GENIUS_SEEDS:
            data = {
                **seed,
                "slug": seed["id"],
                "iq_score_label": _iq_label(seed.get("iq_score"), seed.get("profile_type", "historical")),
                "iq_score_note": _iq_note(seed.get("iq_score")),
            }
            service_locator.general_service.create(db=db, data=data, model=GeniusProfile)
        logging.info("✅ Seeded %d genius profiles", len(GENIUS_SEEDS))
    except Exception:
        logging.exception("❌ Failed to seed genius profiles")
    finally:
        db.close()
