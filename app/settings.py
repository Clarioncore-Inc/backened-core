import os
from dotenv import dotenv_values

config = {
    **dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env")),
    **os.environ,
}

APP_NAME = config.get("APP_NAME", "CerebroLearn")
DATABASE_NAME = config.get("DATABASE_NAME", "Cerebrolearn")
DATABASE_USER = config.get("DATABASE_USER", "postgres")
DATABASE_PASSWORD = config.get("DATABASE_PASSWORD", "")
DATABASE_PORT = config.get("DATABASE_PORT", "5432")
DATABASE_HOST = config.get("DATABASE_HOST", "localhost")
FRONTEND_ORIGINS = config.get(
    "FRONTEND_ORIGINS", "http://localhost:3000").split(",")
SECRET_KEY = config.get("SECRET_KEY", "changeme")
ALGORITHM = config.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    config.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

# ── Admin UI ──────────────────────────────────────────────────────────────────
ADMIN_USERNAME = config.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = config.get("ADMIN_PASSWORD", "changeme")
ADMIN_SECRET_KEY = config.get("ADMIN_SECRET_KEY", "changeme-admin-secret")
