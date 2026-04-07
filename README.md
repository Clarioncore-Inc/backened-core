# CerebroLearn — FastAPI Backend

# SET UP

1. Create a virtual environment (python3.12+)
2. `$ pip install -r requirements.txt`
3. `$ pre-commit install`
4. create .env file
5. copy .env.example to .env and update the values
6. `$ alembic upgrade head`
7. `$ fastapi dev` or `$ fastapi dev --port port_number`

# Init Alembic

```
alembic init migrations
```

# Creating migration

```bash
$ alembic revision --autogenerate -m "first migrations"
$ alembic upgrade head

# To downgrade
$ alembic downgrade -1

```

# RUN TEST

```
pytest -v app or pytest -v app/module
```

## Deploying to Production

1. Set all `.env` values to production credentials
2. Change `ADMIN_PASSWORD` and `ADMIN_SECRET_KEY` to strong, random values
3. Set `FRONTEND_ORIGINS` to your production frontend URL
4. Run with a production ASGI server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
5. Put behind a reverse proxy (nginx, Caddy) with HTTPS
