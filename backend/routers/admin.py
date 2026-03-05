from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from models import UserInfo, SystemStats, UserRegister
from utils.storage import (
    get_all_users, update_user_status, delete_user, register_user,
    get_system_stats, load_users, save_users, hash_password
)
from dependencies import get_current_admin
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/stats", response_model=SystemStats)
def stats(_: Dict = Depends(get_current_admin)):
    return get_system_stats()

@router.get("/users", response_model=List[UserInfo])
def list_users(_: Dict = Depends(get_current_admin)):
    users = get_all_users()
    result = []
    for username, data in users.items():
        result.append(UserInfo(
            username=username,
            name=data.get('name', 'N/A'),
            email=data.get('email', 'N/A'),
            user_type=data.get('user_type', 'user'),
            is_active=data.get('is_active', True),
            registration_date=data.get('registration_date', ''),
            last_login=data.get('last_login'),
            login_count=data.get('login_count', 0),
            plans_created=len(data.get('meal_plan_history', [])),
            profiles_created=len(data.get('profile_history', []))
        ))
    return result

@router.post("/users/{username}/status")
def set_user_status(username: str, is_active: bool, _: Dict = Depends(get_current_admin)):
    success = update_user_status(username, is_active)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {username} status updated to {'active' if is_active else 'inactive'}"}

@router.delete("/users/{username}")
def delete_user_endpoint(username: str, _: Dict = Depends(get_current_admin)):
    success, message = delete_user(username)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.post("/users", response_model=Dict)
def create_admin(user: UserRegister, _: Dict = Depends(get_current_admin)):
    users = load_users()
    if user.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")
    users[user.username] = {
        'password': hash_password(user.password),
        'email': user.email,
        'name': user.name,
        'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'profile_history': [],
        'meal_plan_history': [],
        'last_login': None,
        'user_type': 'admin',
        'is_active': True,
        'login_count': 0
    }
    save_users(users)
    return {"message": f"Admin {user.username} created successfully"}