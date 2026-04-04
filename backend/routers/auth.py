# ==================================================================================================
# MODULE: auth.py
# ==================================================================================================
# PURPOSE: Handle user authentication (registration, login) for both regular users and admin users.
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# 
# BACKEND (FastAPI):
#   - Place this file in your 'routers' or 'api' directory.
#   - In your main 'main.py' or 'app.py', include the router:
#        from routers import auth
#        app.include_router(auth.router)
#   - Ensure the utility functions (register_user, authenticate_user) are implemented in 'utils/storage.py'
#     and that they handle password hashing, JWT token generation (if used), and user data persistence.
#   - The endpoints return simple JSON messages. For production, you would also return a JWT token
#     upon successful login (the current code returns only a message and user_type).
#
# FRONTEND (Example with JavaScript fetch):
#   - Register a new user:
#        POST /api/auth/register
#        Body: {"username": "raj_kumar", "password": "SecurePass123", "email": "raj@example.com", "name": "Raj Kumar"}
#   - Login as regular user:
#        POST /api/auth/login
#        Body: {"username": "raj_kumar", "password": "SecurePass123"}
#   - Login as admin:
#        POST /api/auth/admin/login
#        Body: {"username": "admin", "password": "admin123"}
#
# EXAMPLE INDIAN USER INPUTS:
#   - Username: "priya_sharma", "amit_patel", "sneha_reddy"
#   - Password: should be strong (e.g., "P@ssw0rd!23")
#   - Email: "priya@gmail.com", "amit@yahoo.co.in", "sneha@outlook.com"
#   - Name: "Priya Sharma", "Amit Patel", "Sneha Reddy"
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import APIRouter from FastAPI to create a route group for authentication endpoints.
# APIRouter allows us to define endpoints with a common prefix and tags for API documentation.
from fastapi import APIRouter, HTTPException

# Import Pydantic models (UserRegister, UserLogin) from local 'models' module.
# These models define the expected shape of request bodies:
#   - UserRegister: {username, password, email, name}
#   - UserLogin: {username, password}
# Ensure 'models.py' exists and contains these classes.
from models import UserRegister, UserLogin

# Import utility functions from 'utils.storage' module:
#   - register_user: handles user creation, validation, and password hashing.
#   - authenticate_user: verifies credentials and optionally checks admin status.
# These functions return (success: bool, message: str) tuples.
from utils.storage import register_user, authenticate_user

# --------------------------------------------------------------------------------------------------
# ROUTER INITIALIZATION
# --------------------------------------------------------------------------------------------------
# Create an APIRouter instance with URL prefix '/api/auth' and tag 'Authentication' for OpenAPI docs.
# All endpoints defined below will be mounted under /api/auth.
# Example full URL: http://yourdomain.com/api/auth/register
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# --------------------------------------------------------------------------------------------------
# ENDPOINT 1: POST /api/auth/register
# --------------------------------------------------------------------------------------------------
# Purpose: Register a new regular user account (not admin by default).
# Request body: JSON matching UserRegister model.
# Response: JSON with success message and user_type ("user").
# Error: 400 Bad Request if username already exists or validation fails.
# Example Indian user registration request:
#   POST /api/auth/register
#   Content-Type: application/json
#   Body: {
#       "username": "priya_sharma",
#       "password": "Priya@2025",
#       "email": "priya.sharma@gmail.com",
#       "name": "Priya Sharma"
#   }
# Example response (success):
#   {"message": "User registered successfully", "user_type": "user"}
# Example response (failure, duplicate username):
#   {"detail": "Username already exists"}
# --------------------------------------------------------------------------------------------------

@router.post("/register")
def register(user: UserRegister):
    # Call register_user from storage module.
    # It will:
    #   1. Check if username already exists.
    #   2. Hash the password (using bcrypt or similar).
    #   3. Store user data in JSON file or database.
    #   4. Return (success, message) tuple.
    success, message = register_user(user.username, user.password, user.email, user.name)
    
    # If registration failed (e.g., duplicate username or invalid data), raise HTTP 400 error.
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # On success, return a JSON response with the message and explicitly set user_type to "user".
    # (Admins are created via separate admin-only endpoint, not through this public registration.)
    return {"message": message, "user_type": "user"}

# --------------------------------------------------------------------------------------------------
# ENDPOINT 2: POST /api/auth/login
# --------------------------------------------------------------------------------------------------
# Purpose: Authenticate a regular user (non-admin) and return success message.
# Request body: JSON matching UserLogin model.
# Response: JSON with success message and user_type ("user").
# Error: 401 Unauthorized if credentials are invalid or user is an admin (if is_admin=False check fails).
# Example Indian user login request:
#   POST /api/auth/login
#   Body: {
#       "username": "priya_sharma",
#       "password": "Priya@2025"
#   }
# Example response (success):
#   {"message": "Login successful", "user_type": "user"}
# Example response (failure, wrong password):
#   {"detail": "Invalid credentials"}
# --------------------------------------------------------------------------------------------------

@router.post("/login")
def login(user: UserLogin):
    # Call authenticate_user with is_admin=False to ensure that admin accounts cannot log in via this endpoint.
    # authenticate_user will:
    #   1. Look up the user by username.
    #   2. Verify the password (compare hash).
    #   3. Check user_type against is_admin flag.
    #   4. Return (success, message) tuple.
    # Note: In a real implementation, authenticate_user would also generate and return a JWT token.
    success, message = authenticate_user(user.username, user.password, is_admin=False)
    
    # If authentication fails, raise HTTP 401 (Unauthorized) with the error message.
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    # On success, return message and user_type.
    # The frontend can store this information (e.g., in localStorage) to determine user role.
    return {"message": message, "user_type": "user"}

# --------------------------------------------------------------------------------------------------
# ENDPOINT 3: POST /api/auth/admin/login
# --------------------------------------------------------------------------------------------------
# Purpose: Authenticate an admin user. Only users with user_type="admin" can log in here.
# Request body: JSON matching UserLogin model.
# Response: JSON with success message and user_type ("admin").
# Error: 401 Unauthorized if credentials are invalid or user is not an admin.
# Example admin login request:
#   POST /api/auth/admin/login
#   Body: {
#       "username": "superadmin",
#       "password": "Admin@123"
#   }
# Example response (success):
#   {"message": "Admin login successful", "user_type": "admin"}
# Example response (failure, user is regular user):
#   {"detail": "Admin access required"}
# --------------------------------------------------------------------------------------------------

@router.post("/admin/login")
def admin_login(user: UserLogin):
    # Call authenticate_user with is_admin=True to enforce that only admin users can log in.
    # If a regular user tries to log in here, authenticate_user will return success=False
    # with a message like "Admin access required".
    success, message = authenticate_user(user.username, user.password, is_admin=True)
    
    # If authentication fails (invalid credentials or not an admin), raise 401.
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    # On success, return message and indicate user_type as "admin".
    return {"message": message, "user_type": "admin"}


























# from fastapi import APIRouter, HTTPException, status, Depends                      # added Depends
# from fastapi.security import OAuth2PasswordRequestForm                              # new import
# from datetime import timedelta
# from models import UserRegister, UserLogin, TokenResponse
# from utils.storage import register_user, authenticate_user
# from dependencies import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# @router.post("/register", response_model=TokenResponse)
# def register(user: UserRegister):
#     success, message = register_user(user.username, user.password, user.email, user.name)
#     if not success:
#         raise HTTPException(status_code=400, detail=message)
#     access_token = create_access_token(
#         data={"sub": user.username, "user_type": "user"},
#         expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     return {"access_token": access_token, "token_type": "bearer", "user_type": "user"}

# @router.post("/login", response_model=TokenResponse)
# def login(user: UserLogin):
#     success, message = authenticate_user(user.username, user.password, is_admin=False)
#     if not success:
#         raise HTTPException(status_code=401, detail=message)
#     access_token = create_access_token(
#         data={"sub": user.username, "user_type": "user"},
#         expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     return {"access_token": access_token, "token_type": "bearer", "user_type": "user"}

# @router.post("/admin/login", response_model=TokenResponse)
# def admin_login(user: UserLogin):
#     success, message = authenticate_user(user.username, user.password, is_admin=True)
#     if not success:
#         raise HTTPException(status_code=401, detail=message)
#     access_token = create_access_token(
#         data={"sub": user.username, "user_type": "admin"},
#         expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     return {"access_token": access_token, "token_type": "bearer", "user_type": "admin"}

# # # NEW ENDPOINT – for Swagger OAuth2 form login
# # @router.post("/token", response_model=TokenResponse)
# # def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
# #     """OAuth2 compatible token endpoint (uses form data for Swagger UI)"""
# #     success, message = authenticate_user(form_data.username, form_data.password, is_admin=False)
# #     if not success:
# #         raise HTTPException(status_code=401, detail=message)
# #     access_token = create_access_token(
# #         data={"sub": form_data.username, "user_type": "user"},
# #         expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
# #     )
# #     return {"access_token": access_token, "token_type": "bearer", "user_type": "user"}