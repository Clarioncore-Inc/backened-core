from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import add_pagination

from app.settings import APP_NAME, FRONTEND_ORIGINS, ADMIN_SECRET_KEY
from app.admin_ui import create_admin

# ── Router imports ────────────────────────────────────────────────────────────
from app.authentication.routes import router as auth_router
from app.accounts.routes import router as accounts_router
from app.courses.routes import router as courses_router
from app.lessons.routes import router as lessons_router, bookmarks_router, comments_router, sections_router
from app.enrollments.routes import router as enrollments_router
from app.progress.routes import router as progress_router
from app.payments.routes import router as payments_router, payouts_router
from app.reviews.routes import router as reviews_router, course_reviews_router
from app.psychologist.routes import router as psychologist_router
from app.admin_panel.routes import router as admin_router
from app.creator.routes import router as creator_router
from app.gamification.routes import router as leaderboard_router

app = FastAPI(
    title=APP_NAME,
    description="CerebroLearn REST API — FastAPI/PostgreSQL backend",
    version="1.0.0",
)

# ── Middleware ────────────────────────────────────────────────────────────────
# SessionMiddleware must be added BEFORE CORSMiddleware (outermost layer first)
app.add_middleware(SessionMiddleware, secret_key=ADMIN_SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(accounts_router, prefix=API_PREFIX)
app.include_router(courses_router, prefix=API_PREFIX)
app.include_router(lessons_router, prefix=API_PREFIX)
app.include_router(sections_router, prefix=API_PREFIX)
app.include_router(bookmarks_router, prefix=API_PREFIX)
app.include_router(comments_router, prefix=API_PREFIX)
app.include_router(enrollments_router, prefix=API_PREFIX)
app.include_router(progress_router, prefix=API_PREFIX)
app.include_router(payments_router, prefix=API_PREFIX)
app.include_router(payouts_router, prefix=API_PREFIX)
app.include_router(reviews_router, prefix=API_PREFIX)
app.include_router(course_reviews_router, prefix=API_PREFIX)
app.include_router(psychologist_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(creator_router, prefix=API_PREFIX)
app.include_router(leaderboard_router, prefix=API_PREFIX)

# ── Pagination ────────────────────────────────────────────────────────────────
add_pagination(app)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": APP_NAME}


# ── Admin UI ──────────────────────────────────────────────────────────────────
# Mounted at /admin — must be called AFTER all routers are registered
create_admin(app)
