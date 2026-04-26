from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.settings import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def get_current_active_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        bearer_scheme),
    db: Session = Depends(get_db),
):
    from app.accounts.models import User

    if not credentials or not hasattr(credentials, "credentials"):
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided.", headers={
                            "WWW-Authenticate": "Bearer"})

    email = decode_token(credentials.credentials)
    user = email and db.query(User).filter(User.email == email).first()

    if not user or not user.is_active or user.is_suspended:
        raise HTTPException(status_code=401, detail="Invalid token or token expired.", headers={
                            "WWW-Authenticate": "Bearer"})

    return user
