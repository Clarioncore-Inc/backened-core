# CerebroLearn — FastAPI Backend

FastAPI + PostgreSQL backend for CerebroLearn. Replaces the original Supabase/Deno Edge Function.

---

## Requirements

- Python 3.10+
- PostgreSQL 14+ (running locally or remotely)

---

## Setup

### 1. Create and activate a virtual environment (recommended)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example and fill in your values:

```bash
cp .env.example .env   # or edit .env directly
```

Open `backend/.env` and set:

```env
# Database
DATABASE_NAME=your_database_name
DATABASE_USER=your_postgres_user
DATABASE_PASSWORD=your_postgres_password
DATABASE_PORT=your_postgres_port
DATABASE_HOST=your_postgres_host

# Frontend CORS (comma-separated if multiple origins)
FRONTEND_ORIGINS=http://localhost:3000

# JWT Auth
SECRET_KEY=generate_a_long_random_string_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App
APP_NAME=CerebroLearn

# Admin UI — change these before going to production
ADMIN_USERNAME=admin-name
ADMIN_PASSWORD=admin-password
ADMIN_SECRET_KEY=admin-secret-key
```

To generate a secure `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run database migrations

Run this once to create all tables:

```bash
cd backend
PYTHONPATH=. python3 -m alembic upgrade head
```

If you change any models later, generate a new migration:

```bash
PYTHONPATH=. python3 -m alembic revision --autogenerate -m "describe your change"
PYTHONPATH=. python3 -m alembic upgrade head
```

### 5. Start the server

```bash
cd backend
PYTHONPATH=. python3 -m uvicorn app.main:app --reload --port 8000
```

The server will be available at:

- **API** → `http://localhost:8000/api/`
- **Interactive docs (Swagger)** → `http://localhost:8000/docs`
- **ReDoc docs** → `http://localhost:8000/redoc`
- **Admin UI** → `http://localhost:8000/admin`
- **Health check** → `http://localhost:8000/health`

---

## Admin UI

A full database management UI is built in using [sqladmin](https://aminalaee.dev/sqladmin/).

| Setting  | Value                               |
| -------- | ----------------------------------- |
| URL      | `http://localhost:8000/admin`       |
| Username | Value of `ADMIN_USERNAME` in `.env` |
| Password | Value of `ADMIN_PASSWORD` in `.env` |

Change the credentials in `backend/.env` before deploying to production.

---

## Project Structure

```
backend/
├── .env                        # Environment variables (never commit this)
├── requirements.txt            # Python dependencies
├── alembic.ini                 # Alembic config
├── LLM_API_GUIDE.md           # Guide for connecting the frontend to this API
├── alembic/
│   └── env.py                  # Migration environment (auto-discovers all models)
└── app/
    ├── main.py                 # App entry point — all routers registered here
    ├── settings.py             # Reads .env values
    ├── database.py             # SQLAlchemy engine + session
    ├── dependencies.py         # get_db() dependency
    ├── admin_ui.py             # sqladmin Admin UI setup
    ├── core/
    │   ├── models.py           # BaseModel (id, created_at, updated_at)
    │   ├── services.py         # GenericService (CRUD helpers)
    │   ├── schema.py           # Shared Pydantic base
    │   └── dependency_injection.py  # service_locator — access all services here
    ├── accounts/               # User profile management
    ├── authentication/         # JWT login, signup, token utilities
    ├── courses/                # Course CRUD
    ├── lessons/                # Lessons, likes, bookmarks, comments
    ├── enrollments/            # Course enrollments
    ├── progress/               # Lesson progress tracking
    ├── payments/               # Payments + payouts
    ├── reviews/                # Course reviews
    ├── psychologist/           # Psychologist profiles + session bookings
    ├── creator/                # Creator dashboard (courses, subscribers, earnings)
    ├── admin_panel/            # Admin endpoints (users, analytics, settings)
    └── gamification/           # Leaderboard
```

---

## Authentication

All protected routes require a `Bearer` token in the `Authorization` header.

**Login flow:**

```
POST /api/auth/login
{ "email": "...", "password": "..." }

→ { "access_token": "<JWT>", "token_type": "bearer", "user": {...} }
```

Store the token and send it with every request:

```
Authorization: Bearer <access_token>
```

Token lifetime is controlled by `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env` (default: 1440 = 24 hours).

---

## Key API Endpoints

| Endpoint                          | Description                     |
| --------------------------------- | ------------------------------- |
| `POST /api/auth/signup`           | Create account                  |
| `POST /api/auth/login`            | Login, returns JWT              |
| `GET /api/accounts/profile`       | Get own profile                 |
| `PUT /api/accounts/profile`       | Update own profile              |
| `GET /api/courses/`               | List public courses (paginated) |
| `POST /api/courses/`              | Create a course                 |
| `GET /api/courses/{id}`           | Get course + lessons            |
| `POST /api/enrollments/`          | Enroll in a course              |
| `POST /api/progress/`             | Save lesson progress            |
| `POST /api/lessons/{id}/like`     | Like a lesson                   |
| `POST /api/lessons/{id}/bookmark` | Bookmark a lesson               |
| `GET /api/leaderboard/`           | Top 100 users by XP             |
| `GET /api/creator/earnings`       | Creator earnings                |
| `GET /api/admin/analytics`        | Platform stats (admin only)     |

See `http://localhost:8000/docs` for the full interactive API reference.

For frontend integration instructions, see **`LLM_API_GUIDE.md`** in this folder.

---

## Running Tests

No test suite is included yet. To add tests:

```bash
pip install pytest httpx
pytest
```

---

## Deploying to Production

1. Set all `.env` values to production credentials
2. Change `ADMIN_PASSWORD` and `ADMIN_SECRET_KEY` to strong, random values
3. Set `FRONTEND_ORIGINS` to your production frontend URL
4. Run with a production ASGI server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
5. Put behind a reverse proxy (nginx, Caddy) with HTTPS
