# ==================================================================================================
# MODULE: dependencies.py
# ==================================================================================================
# PURPOSE: Provide dependency injection functions for FastAPI endpoints to obtain the current user
#          and enforce authentication/authorization (active user, admin role).
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# 
# BACKEND (FastAPI):
#   - Place this file in your project root or 'utils' directory.
#   - Import these functions in any router that needs user authentication:
#        from dependencies import get_current_active_user, get_current_admin
#   - Use them as Depends() in endpoint parameters:
#        def my_endpoint(current_user: Dict = Depends(get_current_active_user)):
#   - **IMPORTANT**: This current implementation uses a hardcoded DEFAULT_USER for development/demo.
#     In a real production application, replace get_current_user() with actual JWT token extraction
#     and validation. Example with python-jose:
#        from jose import JWTError, jwt
#        async def get_current_user(token: str = Depends(oauth2_scheme)):
#            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#            username = payload.get("sub")
#            user = get_user_from_db(username)
#            return user
#
# FRONTEND (React/Angular/Vue):
#   - For endpoints protected by these dependencies, the frontend must include an
#     Authorization header with a Bearer token (JWT) after login.
#   - Example using fetch in JavaScript:
#        const token = localStorage.getItem('access_token');
#        fetch('/api/user/profile', {
#            headers: { 'Authorization': `Bearer ${token}` }
#        })
#   - The token is typically obtained from a login endpoint (e.g., POST /api/auth/login)
#     which returns a JWT upon successful authentication.
#
# EXAMPLE INDIAN USER FLOW (with real auth):
#   1. User "priya_sharma" logs in via POST /api/auth/login with credentials.
#   2. Backend validates, generates a JWT containing {"sub": "priya_sharma", "user_type": "user"}
#   3. Frontend stores token in localStorage.
#   4. Frontend calls GET /api/user/profile with header "Authorization: Bearer <token>".
#   5. FastAPI's get_current_user() decodes token, loads user data, returns user dict.
#   6. get_current_active_user() ensures account is active (is_active=True).
#   7. If endpoint requires admin, get_current_admin() checks user_type == "admin".
#
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import Depends from FastAPI to allow dependency injection chaining.
# Depends is used to declare that a function depends on another dependency.
from fastapi import Depends
# Import Dict and Any from typing for type hints.
from typing import Dict, Any

# --------------------------------------------------------------------------------------------------
# HARDCODED DEFAULT USER (FOR DEVELOPMENT/TESTING ONLY)
# --------------------------------------------------------------------------------------------------
# This is a placeholder user that bypasses real authentication.
# In production, you MUST replace get_current_user() with proper JWT validation.
# The DEFAULT_USER is an admin with premium subscription, allowing full access to all endpoints.
DEFAULT_USER = {
    "username": "default_user",      # Unique identifier for the user
    "user_type": "admin",            # Role: 'admin' or 'user' – admin has elevated privileges
    "subscription_tier": "premium"   # Subscription level: 'free' (max 7-day plans) or 'premium' (max 14-day plans)
}

# ==================================================================================================
# DEPENDENCY: get_current_user() -> Dict[str, Any]
# ==================================================================================================
# Purpose: Extract and return the current authenticated user.
# In a real app, this would decode a JWT from the Authorization header,
# fetch the user from the database, and return the user dict.
# Current implementation returns the hardcoded DEFAULT_USER for demo purposes.
# ==================================================================================================

async def get_current_user() -> Dict[str, Any]:
    # Return the default user. In production, this would be replaced with:
    #   token = await oauth2_scheme(request)
    #   payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #   username = payload.get("sub")
    #   user = get_user_from_db(username)
    #   return user
    return DEFAULT_USER

# ==================================================================================================
# DEPENDENCY: get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict
# ==================================================================================================
# Purpose: Ensure the current user is active (is_active == True).
# It depends on get_current_user() to first obtain the user object,
# then checks the 'is_active' flag (in a real implementation).
# If the account is deactivated, it should raise an HTTPException(403).
# Current version simply returns the user without checking (since DEFAULT_USER is active).
# ==================================================================================================

async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    # In a real implementation, you would add:
    #   if not current_user.get("is_active", True):
    #       raise HTTPException(status_code=403, detail="Inactive user")
    return current_user

# ==================================================================================================
# DEPENDENCY: get_current_admin(current_user: Dict = Depends(get_current_active_user)) -> Dict
# ==================================================================================================
# Purpose: Enforce that the current user has admin privileges.
# It first gets the active user via get_current_active_user, then checks user_type.
# If user_type is not 'admin', it should raise HTTPException(403).
# This is used to protect admin-only endpoints (e.g., /api/admin/*).
# Current version returns the user without checking because DEFAULT_USER is admin.
# ==================================================================================================

async def get_current_admin(current_user: Dict = Depends(get_current_active_user)) -> Dict:
    # In production, add:
    #   if current_user.get("user_type") != "admin":
    #       raise HTTPException(status_code=403, detail="Admin privileges required")
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