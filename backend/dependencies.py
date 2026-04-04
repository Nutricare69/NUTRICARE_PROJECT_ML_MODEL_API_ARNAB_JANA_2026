# dependencies.py – final version
from fastapi import Depends
from typing import Dict, Any

DEFAULT_USER = {
    "username": "default_user",
    "user_type": "admin",
    "subscription_tier": "premium"
}

async def get_current_user() -> Dict[str, Any]:
    return DEFAULT_USER

async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    return current_user

async def get_current_admin(current_user: Dict = Depends(get_current_active_user)) -> Dict:
    return current_user



























# from fastapi import Depends, HTTPException, status
# from datetime import datetime, timedelta
# from typing import Dict, Any
# import os
# from jose import jwt

# # Secret key for JWT (kept for token creation in auth.py)
# SECRET_KEY = os.getenv("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# # -------------------------------------------------------------------
# # AUTHENTICATION DISABLED – always use a default user
# # -------------------------------------------------------------------
# DEFAULT_USER = {
#     "username": "default_user",
#     "user_type": "admin",          # Allows both user and admin endpoints
#     "subscription_tier": "premium"
# }

# def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
#     """Still needed for /api/auth/login and /api/auth/register to return tokens."""
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# async def get_current_user() -> Dict[str, Any]:
#     """No token validation – always returns the default user."""
#     return DEFAULT_USER

# async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
#     """No active/inactive check – simply returns the default user."""
#     return current_user

# async def get_current_admin(current_user: Dict = Depends(get_current_active_user)) -> Dict:
#     """No admin privilege check – returns the default user (which is 'admin')."""
#     return current_user