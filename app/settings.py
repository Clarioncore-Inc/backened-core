import os
from dotenv import dotenv_values

config = {
    **dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env")),
    **os.environ,
}

FRONTEND_URL = config.get("FRONTEND_URL", "http://localhost:3000")
API_BASE_URL = config.get(
    "API_BASE_URL", "https://backened-core.onrender.com/health")


# DATABASE
APP_NAME = config.get("APP_NAME", "CerebroLearn")
DATABASE_NAME = config.get("DATABASE_NAME", "Cerebrolearn")
DATABASE_USER = config.get("DATABASE_USER", "postgres")
DATABASE_PASSWORD = config.get("DATABASE_PASSWORD", "")
DATABASE_PORT = config.get("DATABASE_PORT", "5432")
DATABASE_HOST = config.get("DATABASE_HOST", "localhost")
DATABASE_SSL = config.get("DATABASE_SSL", "")

FRONTEND_ORIGINS = config.get(
    "FRONTEND_ORIGINS", "http://localhost:3000").split(",")
SECRET_KEY = config.get("SECRET_KEY", "changeme")
ALGORITHM = config.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    config.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))


_ssl_suffix = "?sslmode=require" if DATABASE_SSL == "require" else ""
DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}{_ssl_suffix}"
)

# ── Admin UI ──────────────────────────────────────────────────────────────────
ADMIN_USERNAME = config.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = config.get("ADMIN_PASSWORD", "changeme")
ADMIN_SECRET_KEY = config.get("ADMIN_SECRET_KEY", "changeme-admin-secret")


SLACK_ACCESS_TOKEN = config.get("SLACK_ACCESS_TOKEN", "")
SLACK_REFRESH_TOKEN = config.get("SLACK_REFRESH_TOKEN", "")
SLACK_CHANNEL_ID = config.get("SLACK_CHANNEL_ID", "")


AWS_ACCESS_KEY_ID = config.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = config.get("AWS_SECRET_ACCESS_KEY", "")
AWS_SES_REGION_NAME = config.get("AWS_SES_REGION_NAME", "")
AWS_STORAGE_BUCKET_NAME = config.get("AWS_STORAGE_BUCKET_NAME", "")
FILE_UPLOAD_MAX_MEMORY_SIZE = int(config.get(
    "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024))  # 10 MB
AWS_S3_CLIENT_BUCKET_REGION = config.get("AWS_S3_CLIENT_BUCKET_REGION")
