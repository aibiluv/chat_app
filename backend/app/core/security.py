from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from ..db import database, models
from ..cruds import user_crud
from ..schemas import schemas
import os

# --- Configuration ---
SECRET_KEY = "a_very_secret_key_that_should_be_in_env_vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


FERNET_KEY = os.getenv("MESSAGE_ENCRYPTION_KEY", "mR8EaAKcQkYDJE8a5oX4GgxJ2RkC0z4qDIaiDpaC0HY=") #Shouldn't be here
if not FERNET_KEY:
    raise RuntimeError("Please set MESSAGE_ENCRYPTION_KEY in your environment!")
fernet = Fernet(FERNET_KEY.encode())


def encrypt_message(plaintext: str) -> str:
    """Encrypt a UTF-8 string → URL-safe base64 token."""
    token = fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_message(token: str) -> str:
    """Decrypt a URL-safe base64 token → original UTF-8 string."""
    plaintext = fernet.decrypt(token.encode("utf-8"))
    return plaintext.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)  # timezone-aware current UTC time
    expire = now + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = user_crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def get_user_from_token(db: Session, token: str) -> Optional[models.User]:
    """Helper for WebSocket auth"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
        return user_crud.get_user_by_username(db, username=username)
    except JWTError:
        return None