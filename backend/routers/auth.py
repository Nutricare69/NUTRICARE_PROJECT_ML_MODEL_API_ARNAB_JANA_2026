from fastapi import APIRouter, HTTPException, status, Depends                      # added Depends
from fastapi.security import OAuth2PasswordRequestForm                              # new import
from datetime import timedelta
from models import UserRegister, UserLogin, TokenResponse
from utils.storage import register_user, authenticate_user
from dependencies import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(user: UserRegister):
    success, message = register_user(user.username, user.password, user.email, user.name)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    access_token = create_access_token(
        data={"sub": user.username, "user_type": "user"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "user"}

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    success, message = authenticate_user(user.username, user.password, is_admin=False)
    if not success:
        raise HTTPException(status_code=401, detail=message)
    access_token = create_access_token(
        data={"sub": user.username, "user_type": "user"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "user"}

@router.post("/admin/login", response_model=TokenResponse)
def admin_login(user: UserLogin):
    success, message = authenticate_user(user.username, user.password, is_admin=True)
    if not success:
        raise HTTPException(status_code=401, detail=message)
    access_token = create_access_token(
        data={"sub": user.username, "user_type": "admin"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "admin"}

# NEW ENDPOINT – for Swagger OAuth2 form login
@router.post("/token", response_model=TokenResponse)
def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint (uses form data for Swagger UI)"""
    success, message = authenticate_user(form_data.username, form_data.password, is_admin=False)
    if not success:
        raise HTTPException(status_code=401, detail=message)
    access_token = create_access_token(
        data={"sub": form_data.username, "user_type": "user"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "user_type": "user"}