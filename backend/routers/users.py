# ==================================================================================================
# MODULE: users.py
# ==================================================================================================
# PURPOSE: Provide endpoints for authenticated users to manage their profile (save/view current profile)
#          and retrieve their history (profile snapshots and meal plans).
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# BACKEND (FastAPI):
#   - Place this file in your 'routers' or 'api' directory.
#   - In your main 'main.py' or 'app.py', include the router:
#        from routers import users
#        app.include_router(users.router)
#   - Ensure the utility functions are implemented in 'utils/data.py' and 'utils/storage.py':
#        calculate_user_metrics() – computes BMI and TDEE.
#        save_user_profile() – appends a profile snapshot to user's profile_history.
#        get_user_history() – retrieves both profile_history and meal_plan_history.
#        load_users() – loads the entire users database (for direct access).
#   - Authentication is handled via get_current_active_user (from dependencies.py).
#   - All endpoints require a valid JWT token (or session) and an active user account.
#
# FRONTEND (Example with JavaScript fetch):
#   - Get current profile (most recent snapshot):
#        GET /api/user/profile
#        Headers: { "Authorization": "Bearer <token>" }
#   - Save a new profile snapshot:
#        POST /api/user/profile
#        Body: { "age": 28, "gender": "female", "weight": 65, "height": 165,
#                "activity_level": "moderate", "goal": "weight_loss" }
#   - Get full history (all profiles and meal plans):
#        GET /api/user/history
#
# EXAMPLE INDIAN USER INPUTS:
#   - User: Ramesh, 35 years, male, weight 80 kg, height 170 cm,
#     activity level "moderate", goal "weight_loss".
#   - The system calculates BMI = 80 / (1.70^2) = 27.7 (overweight).
#   - TDEE based on Mifflin-St Jeor: BMR = 10*80 + 6.25*170 - 5*35 + 5 = 800 + 1062.5 - 175 + 5 = 1692.5
#     Multiply by activity factor 1.55 = ~2623 calories/day.
#   - Profile snapshot is saved with timestamp, BMI, TDEE.
#   - Later, after 2 months, user saves another profile with weight 74 kg, showing progress.
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import APIRouter from FastAPI to create a route group for user-related endpoints.
# Depends is used for dependency injection (e.g., getting current authenticated user).
# HTTPException is imported but not used in this file (kept for potential future error handling).
from fastapi import APIRouter, Depends, HTTPException

# Import Dict and List from typing for type hints – specify that functions return dictionaries and lists.
from typing import Dict, List

# Import Pydantic models:
#   - UserProfile: base profile input (age, gender, weight, height, activity_level, goal).
#   - ProfileWithMetrics: extends UserProfile with computed fields (bmi, tdee).
from models import UserProfile, ProfileWithMetrics

# Import utility functions from 'utils.data' module:
#   - calculate_user_metrics: computes BMI and TDEE based on user parameters.
from utils.data import calculate_user_metrics

# Import storage utility functions from 'utils.storage':
#   - save_user_profile: appends a profile snapshot to the user's profile_history list.
#   - get_user_history: retrieves both profile_history and meal_plan_history for a user.
#   - load_users: loads the entire users dictionary from the JSON storage (used in GET /profile).
from utils.storage import save_user_profile, get_user_history, load_users

# Import authentication dependency: get_current_active_user ensures the request is from
# an authenticated and active user. It returns a dict containing user info (username, etc.).
from dependencies import get_current_active_user

# --------------------------------------------------------------------------------------------------
# ROUTER INITIALIZATION
# --------------------------------------------------------------------------------------------------
# Create an APIRouter instance with URL prefix '/api/user' and tag 'User' for OpenAPI documentation.
# All endpoints defined below will be mounted under /api/user.
# Example full URL: http://yourdomain.com/api/user/profile
router = APIRouter(prefix="/api/user", tags=["User"])

# --------------------------------------------------------------------------------------------------
# ENDPOINT 1: GET /api/user/profile
# --------------------------------------------------------------------------------------------------
# Purpose: Retrieve the most recent profile snapshot for the authenticated user.
# Authentication: Required (get_current_active_user).
# Response: JSON containing the latest profile (with metrics) or a message if none exists.
# Example Indian user request:
#   GET /api/user/profile
#   Authorization: Bearer <token>
# Example response (if profile exists):
#   {
#       "age": 35,
#       "gender": "male",
#       "weight": 80,
#       "height": 170,
#       "activity_level": "moderate",
#       "goal": "weight_loss",
#       "bmi": 27.7,
#       "tdee": 2623,
#       "timestamp": "2025-03-15 10:30:00"
#   }
# Example response (if no profile saved):
#   {"message": "No profile saved yet"}
# --------------------------------------------------------------------------------------------------

@router.get("/profile", response_model=Dict)
def get_current_profile(current_user: Dict = Depends(get_current_active_user)):
    # Load the entire users database (dictionary of username -> user data).
    users = load_users()
    # Retrieve the data for the current user using their username.
    # Assumes current_user["username"] exists and is valid.
    user_data = users[current_user["username"]]
    # Check if the user has any saved profiles in profile_history.
    # profile_history is a list of profile snapshots (dictionaries), each with a timestamp.
    if user_data["profile_history"]:
        # Return the most recent profile (last element in the list).
        # Assumes list is ordered chronologically (oldest first, newest last).
        return user_data["profile_history"][-1]
    # If no profiles exist, return a friendly message.
    return {"message": "No profile saved yet"}

# --------------------------------------------------------------------------------------------------
# ENDPOINT 2: POST /api/user/profile
# --------------------------------------------------------------------------------------------------
# Purpose: Save a new profile snapshot for the authenticated user.
# Request body: JSON matching UserProfile model (without metrics).
# Response: ProfileWithMetrics (includes computed BMI and TDEE).
# Authentication: Required (get_current_active_user).
# Example Indian user request:
#   POST /api/user/profile
#   Authorization: Bearer <token>
#   Content-Type: application/json
#   Body:
#   {
#       "age": 35,
#       "gender": "male",
#       "weight": 80,
#       "height": 170,
#       "activity_level": "moderate",
#       "goal": "weight_loss"
#   }
# Example response:
#   {
#       "age": 35,
#       "gender": "male",
#       "weight": 80,
#       "height": 170,
#       "activity_level": "moderate",
#       "goal": "weight_loss",
#       "bmi": 27.7,
#       "tdee": 2623
#   }
# Note: The storage function save_user_profile will also attach a timestamp automatically.
# --------------------------------------------------------------------------------------------------

@router.post("/profile", response_model=ProfileWithMetrics)
def save_profile(profile: UserProfile, current_user: Dict = Depends(get_current_active_user)):
    # Calculate BMI (Body Mass Index) and TDEE (Total Daily Energy Expenditure) using the user's inputs.
    # The calculate_user_metrics function uses standard formulas:
    #   BMI = weight(kg) / (height(m))^2
    #   BMR (Mifflin-St Jeor): for men = 10*weight + 6.25*height - 5*age + 5; for women = ... -161
    #   TDEE = BMR * activity_factor, then adjusted based on goal (weight_loss: -500, muscle_gain: +500, maintenance: 0)
    bmi, tdee = calculate_user_metrics(
        profile.age, profile.gender, profile.weight, profile.height,
        profile.activity_level, profile.goal
    )
    # Convert the UserProfile Pydantic model to a dictionary (so we can add extra fields).
    profile_with_metrics = profile.dict()
    # Add the computed metrics to the dictionary.
    profile_with_metrics.update({"bmi": bmi, "tdee": tdee})
    # Save the profile snapshot to the user's profile_history list in storage.
    # The storage function will also add a timestamp (e.g., datetime.now()).
    save_user_profile(current_user["username"], profile_with_metrics)
    # Return the enriched profile as a ProfileWithMetrics object (automatically validated).
    return ProfileWithMetrics(**profile_with_metrics)

# --------------------------------------------------------------------------------------------------
# ENDPOINT 3: GET /api/user/history
# --------------------------------------------------------------------------------------------------
# Purpose: Retrieve the full history of profile snapshots and meal plans for the authenticated user.
# Authentication: Required (get_current_active_user).
# Response: JSON object with two keys: "profile_history" (list) and "meal_plan_history" (list).
# Example Indian user request:
#   GET /api/user/history
#   Authorization: Bearer <token>
# Example response:
#   {
#       "profile_history": [
#           { "timestamp": "2025-01-10 09:15:00", "age": 35, "weight": 85, "bmi": 29.4, ... },
#           { "timestamp": "2025-02-10 10:30:00", "age": 35, "weight": 82, "bmi": 28.4, ... },
#           { "timestamp": "2025-03-15 11:00:00", "age": 35, "weight": 80, "bmi": 27.7, ... }
#       ],
#       "meal_plan_history": [
#           { "plan_id": 1, "timestamp": "2025-01-10 09:20:00", "day_summaries": {...} },
#           { "plan_id": 2, "timestamp": "2025-02-10 10:45:00", "day_summaries": {...} }
#       ]
#   }
# --------------------------------------------------------------------------------------------------

@router.get("/history", response_model=Dict[str, List])
def get_history(current_user: Dict = Depends(get_current_active_user)):
    # Call get_user_history to retrieve both history lists for the current user.
    # The function returns a tuple: (profiles_list, meal_plans_list).
    # Each list contains dictionaries with timestamps and other fields.
    profiles, meal_plans = get_user_history(current_user["username"])
    # Return a dictionary with both lists, matching the expected response_model.
    return {
        "profile_history": profiles,
        "meal_plan_history": meal_plans
    }