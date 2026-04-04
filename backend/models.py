# ==================================================================================================
# MODULE: models.py
# ==================================================================================================
# PURPOSE: Define Pydantic models (schemas) for request/response validation and serialization.
#          These models ensure data consistency across all API endpoints.
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# BACKEND (FastAPI):
#   - Import these models in routers to define request body shapes and response structures.
#   - Example: from models import UserRegister, MealPlanRequest, RatingResponse
#   - FastAPI automatically validates incoming JSON against these models and generates OpenAPI docs.
#
# FRONTEND (React/Angular/Vue):
#   - These models define the expected JSON format that frontend must send and receive.
#   - For example, when registering an Indian user, frontend must send:
#        { "username": "priya_sharma", "password": "Pass@123", "email": "priya@gmail.com", "name": "Priya Sharma" }
#   - Frontend can create TypeScript interfaces matching these models for type safety.
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import BaseModel (core of Pydantic for data validation), Field (adds metadata like constraints),
# EmailStr (validates email format automatically). Install with: pip install pydantic[email]
from pydantic import BaseModel, Field, EmailStr, validator
# Import typing helpers for list, optional, dict, any types.
from typing import List, Optional, Dict, Any
# Import datetime (used in some models as type hint, though not directly used in fields here)
from datetime import datetime

# ==================================================================================================
# AUTH SCHEMAS (Authentication)
# ==================================================================================================

# Model for user registration request body.
class UserRegister(BaseModel):
    username: str                      # Unique login name (e.g., "raj_verma")
    password: str                      # Plain text password (hashed on backend)
    email: EmailStr                    # Valid email format (e.g., "raj.verma@gmail.com")
    name: str                          # Full name (e.g., "Raj Verma")

# Model for user login request body.
class UserLogin(BaseModel):
    username: str                      # Login username
    password: str                      # Plain text password

# Model for token response after successful login (used if JWT implemented).
class TokenResponse(BaseModel):
    access_token: str                  # JWT token string
    token_type: str = "bearer"         # Fixed to "bearer" (OAuth2 standard)
    user_type: str                     # "user" or "admin"

# ==================================================================================================
# PROFILE SCHEMAS (User Profile Management)
# ==================================================================================================

# Model for user profile input (used when saving a profile or generating meal plan).
class UserProfile(BaseModel):
    name: str                          # User's full name (e.g., "Priya Sharma")
    age: int = Field(ge=10, le=100)    # Age between 10 and 100
    gender: str                        # "Male", "Female", or "Other"
    weight: float = Field(ge=30, le=200)  # Weight in kg (30-200)
    height: float = Field(ge=120, le=220) # Height in cm (120-220)
    goal: str                          # "Weight Loss", "Muscle Gain", or "Maintenance"
    food_preference: str               # "Vegetarian", "Eggetarian", "Non-Vegetarian", "Any"
    medical_conditions: List[str] = [] # e.g., ["Diabetes", "Hypertension"]
    allergies: List[str] = []          # e.g., ["Gluten", "Dairy", "Nuts"]
    activity_level: str                # "Sedentary", "Lightly Active", "Moderately Active", "Very Active"

    # Custom validator for gender field
    @validator('gender')
    def validate_gender(cls, v):
        # Ensure value is one of allowed options
        if v not in ["Male", "Female", "Other"]:
            raise ValueError('Gender must be Male, Female, or Other')
        return v

    # Validator for goal field
    @validator('goal')
    def validate_goal(cls, v):
        if v not in ["Weight Loss", "Muscle Gain", "Maintenance"]:
            raise ValueError('Goal must be Weight Loss, Muscle Gain, or Maintenance')
        return v

    # Validator for food_preference
    @validator('food_preference')
    def validate_food_preference(cls, v):
        if v not in ["Vegetarian", "Eggetarian", "Non-Vegetarian", "Any"]:
            raise ValueError('Invalid food preference')
        return v

    # Validator for activity_level
    @validator('activity_level')
    def validate_activity(cls, v):
        if v not in ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]:
            raise ValueError('Invalid activity level')
        return v

# Model that extends UserProfile with computed metrics (BMI and TDEE).
class ProfileWithMetrics(UserProfile):
    bmi: float                         # Body Mass Index (e.g., 22.5)
    tdee: float                        # Total Daily Energy Expenditure (calories)

# Model for a profile history item (includes timestamp and plan_id).
class ProfileHistoryItem(ProfileWithMetrics):
    timestamp: str                     # When profile was saved (e.g., "2025-03-15 10:30:00")
    plan_id: int                       # Auto-incremented ID within user's history

# ==================================================================================================
# MEAL PLAN SCHEMAS
# ==================================================================================================

# Model for generating a meal plan (inherits all UserProfile fields and adds days).
class MealPlanRequest(UserProfile):
    days: int = 7                      # Number of days for the plan (1-14, depends on subscription)

# Model for a single food item within a meal.
class MealFood(BaseModel):
    name: str                          # Food name (e.g., "Masala Dosa")
    calories: float = Field(..., description="Calories (kcal)")   # Required field
    protein: float = Field(..., description="Protein (grams)")
    fat: float = Field(..., description="Fat (grams)")
    carbs: float = Field(..., description="Carbohydrates (grams)")

# Model for summary of a single day (actual vs target macros).
class DaySummary(BaseModel):
    total_calories: float = Field(..., description="Total calories for the day (kcal)")
    total_protein: float = Field(..., description="Total protein (grams)")
    total_fat: float = Field(..., description="Total fat (grams)")
    total_carbs: float = Field(..., description="Total carbohydrates (grams)")
    target_calories: int = Field(..., description="Daily calorie target (kcal)")
    target_protein: float = Field(..., description="Target protein intake (grams)")
    target_fat: float = Field(..., description="Target fat intake (grams)")
    target_carbs: float = Field(..., description="Target carbohydrate intake (grams)")

# Response model when generating a meal plan.
class MealPlanResponse(BaseModel):
    user_profile: ProfileWithMetrics               # User's profile with metrics
    daily_calorie_target: int                      # TDEE adjusted for goal
    meal_plan: Dict[str, Dict[str, List[MealFood]]]  # Nested dict: day -> meal -> list of foods
    day_summaries: Dict[str, DaySummary]           # Per-day summaries
    filtered_foods_count: int                      # Number of foods considered after filtering

# Model for a saved meal plan history item.
class MealPlanHistoryItem(BaseModel):
    plan_id: int                                   # Unique ID within user's history
    timestamp: str                                 # When plan was generated
    user_profile: ProfileWithMetrics               # Profile snapshot at generation time
    plan_data: Dict[str, Dict[str, List[MealFood]]]  # Full meal plan
    day_summaries: Dict[str, DaySummary]           # Per-day summaries
    food_count: int                                # Number of foods used in generation

# ==================================================================================================
# FOOD SCHEMAS
# ==================================================================================================

# Lightweight model for listing foods (used in search results).
class FoodItem(BaseModel):
    name: str                          # Food name (e.g., "Chole Bhature")
    calories: float                    # Calories per serving
    protein: float                     # Protein in grams
    fat: float                         # Fat in grams
    carbs: float                       # Carbohydrates in grams
    is_veg: bool                       # True if vegetarian
    score: Optional[float] = None      # Macro match score (lower is better)

# Detailed model for a single food (includes allergen and suitability flags).
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

# ==================================================================================================
# ADMIN SCHEMAS
# ==================================================================================================

# Model for returning user information in admin endpoints.
class UserInfo(BaseModel):
    username: str                      # Login name
    name: str                          # Full name
    email: str                         # Email address
    user_type: str                     # "admin" or "user"
    is_active: bool                    # Account active status
    registration_date: str             # Timestamp of registration
    last_login: Optional[str]          # Last login timestamp (may be None)
    login_count: int                   # Number of logins
    plans_created: int                 # Number of meal plans generated
    profiles_created: int              # Number of profile snapshots saved

# Model for system statistics (admin dashboard).
class SystemStats(BaseModel):
    total_users: int                   # All registered users
    active_users: int                  # Users with is_active=True
    admins: int                        # Number of admin accounts
    total_logins: int                  # Sum of login_count across all users
    today_logins: int                  # Users who logged in today
    plans_generated: int               # Total meal plans generated
    profiles_created: int              # Total profile snapshots saved

# ==================================================================================================
# ANALYSIS SCHEMAS (Food Image Analysis)
# ==================================================================================================

# Model for response from food image analysis endpoint.
class ImageAnalysisResponse(BaseModel):
    estimated_calories: int            # Estimated calories (kcal)
    estimated_protein: float           # Protein in grams
    estimated_carbs: float             # Carbs in grams
    estimated_fat: float               # Fat in grams
    food_name: Optional[str] = None    # Recognized food name (if any)

# ==================================================================================================
# RATING & FEEDBACK SCHEMAS
# ==================================================================================================

# Model for submitting a rating/feedback for a meal plan day.
class RatingRequest(BaseModel):
    plan_id: int                       # ID of the meal plan
    day_name: str                      # e.g., "Day 01" or "Monday"
    stars: int = Field(ge=1, le=5)     # Rating from 1 to 5
    feedback: Optional[str] = Field(None, max_length=500)  # Optional comment

# Model for returning a rating (used in user feedback list).
class RatingResponse(BaseModel):
    plan_id: int
    day_name: str
    stars: int
    feedback: Optional[str]
    rated_at: str                      # Timestamp when rating was submitted

# Model for aggregated user feedback summary (includes all ratings per plan).
class UserFeedbackSummary(BaseModel):
    plan_id: int
    plan_timestamp: str
    ratings: Dict[str, RatingResponse]   # Key = day_name (e.g., "Day 01")