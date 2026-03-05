from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from models import UserProfile, ProfileWithMetrics
from utils.data import calculate_user_metrics
from utils.storage import save_user_profile, get_user_history, load_users
from dependencies import get_current_active_user

router = APIRouter(prefix="/api/user", tags=["User"])

@router.get("/profile", response_model=Dict)
def get_current_profile(current_user: Dict = Depends(get_current_active_user)):
    users = load_users()
    user_data = users[current_user["username"]]
    if user_data["profile_history"]:
        return user_data["profile_history"][-1]
    return {"message": "No profile saved yet"}

@router.post("/profile", response_model=ProfileWithMetrics)
def save_profile(profile: UserProfile, current_user: Dict = Depends(get_current_active_user)):
    bmi, tdee = calculate_user_metrics(
        profile.age, profile.gender, profile.weight, profile.height,
        profile.activity_level, profile.goal
    )
    profile_with_metrics = profile.dict()
    profile_with_metrics.update({"bmi": bmi, "tdee": tdee})
    save_user_profile(current_user["username"], profile_with_metrics)
    return ProfileWithMetrics(**profile_with_metrics)

@router.get("/history", response_model=Dict[str, List])
def get_history(current_user: Dict = Depends(get_current_active_user)):
    profiles, meal_plans = get_user_history(current_user["username"])
    return {
        "profile_history": profiles,
        "meal_plan_history": meal_plans
    }