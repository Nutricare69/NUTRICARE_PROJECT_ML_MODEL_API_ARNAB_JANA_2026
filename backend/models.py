from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

# ---------- Auth Schemas ----------
class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr
    name: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str

# ---------- Profile Schemas ----------
class UserProfile(BaseModel):
    name: str
    age: int = Field(ge=10, le=100)
    gender: str
    weight: float = Field(ge=30, le=200)
    height: float = Field(ge=120, le=220)
    goal: str
    food_preference: str
    medical_conditions: List[str] = []
    allergies: List[str] = []
    activity_level: str

    @validator('gender')
    def validate_gender(cls, v):
        if v not in ["Male", "Female", "Other"]:
            raise ValueError('Gender must be Male, Female, or Other')
        return v

    @validator('goal')
    def validate_goal(cls, v):
        if v not in ["Weight Loss", "Muscle Gain", "Maintenance"]:
            raise ValueError('Goal must be Weight Loss, Muscle Gain, or Maintenance')
        return v

    @validator('food_preference')
    def validate_food_preference(cls, v):
        if v not in ["Vegetarian", "Eggetarian", "Non-Vegetarian", "Any"]:
            raise ValueError('Invalid food preference')
        return v

    @validator('activity_level')
    def validate_activity(cls, v):
        if v not in ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]:
            raise ValueError('Invalid activity level')
        return v

class ProfileWithMetrics(UserProfile):
    bmi: float
    tdee: int

class ProfileHistoryItem(ProfileWithMetrics):
    timestamp: str
    plan_id: int

# ---------- Meal Plan Schemas ----------
class MealPlanRequest(UserProfile):
    days: int = 7

class MealPlanResponse(BaseModel):
    user_profile: ProfileWithMetrics
    meal_plan: Dict[str, Dict[str, List[str]]]
    filtered_foods_count: int

class MealPlanHistoryItem(BaseModel):
    plan_id: int
    timestamp: str
    user_profile: ProfileWithMetrics
    plan_data: Dict[str, Dict[str, List[str]]]
    food_count: int

# ---------- Food Schemas ----------
class FoodItem(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    is_veg: bool
    score: Optional[float] = None

class FoodDetail(FoodItem):
    contains_egg: bool
    is_allergen_gluten: bool
    is_allergen_dairy: bool
    is_allergen_nuts: bool
    is_allergen_soy: bool
    is_allergen_shellfish: bool
    is_allergen_eggs: bool
    is_allergen_fish: bool
    suitable_diabetes: bool
    suitable_hypertension: bool
    suitable_heart_disease: bool
    suitable_thyroid: bool
    suitable_pcos: bool
    suitable_kidney_disease: bool
    suitable_gerd: bool

# ---------- Admin Schemas ----------
class UserInfo(BaseModel):
    username: str
    name: str
    email: str
    user_type: str
    is_active: bool
    registration_date: str
    last_login: Optional[str]
    login_count: int
    plans_created: int
    profiles_created: int

class SystemStats(BaseModel):
    total_users: int
    active_users: int
    admins: int
    total_logins: int
    today_logins: int
    plans_generated: int
    profiles_created: int

# ---------- Analysis ----------
class ImageAnalysisResponse(BaseModel):
    estimated_calories: int
    estimated_protein: float
    estimated_carbs: float
    estimated_fat: float
    food_name: Optional[str] = None