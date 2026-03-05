from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Dict, Any
import os

# Secret key for JWT (should be stored in environment variable)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")   # was /api/auth/login  # used for Swagger UI

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    payload = decode_token(token)
    username = payload.get("sub")
    user_type = payload.get("user_type")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"username": username, "user_type": user_type}

async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    # Optionally check if user exists and is active (call storage)
    from utils.storage import load_users
    users = load_users()
    if current_user["username"] not in users:
        raise HTTPException(status_code=401, detail="User not found")
    if not users[current_user["username"]].get("is_active", True):
        raise HTTPException(status_code=403, detail="User is deactivated")
    return current_user

async def get_current_admin(current_user: Dict = Depends(get_current_active_user)) -> Dict:
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user