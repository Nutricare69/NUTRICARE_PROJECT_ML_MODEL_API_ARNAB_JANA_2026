# ==================================================================================================
# MODULE: meal_plan.py
# ==================================================================================================
# PURPOSE: Generate personalized meal plans based on user metrics (age, weight, height, activity,
#          dietary preferences, allergies, medical conditions, and goal). Also save and retrieve
#          user profiles and meal plan history.
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):

# BACKEND (FastAPI):
#   - Place this file in your 'routers' or 'api' directory.
#   - In your main 'main.py' or 'app.py', include the router:
#        from routers import meal_plan
#        app.include_router(meal_plan.router)
#   - Ensure utility functions are implemented in 'utils/data.py' and 'utils/storage.py':
#        load_data(), filter_foods(), generate_meal_plan(), calculate_user_metrics()
#        save_user_profile(), save_meal_plan(), get_user_history()
#   - Authentication is handled via get_current_active_user dependency (from dependencies.py).
#   - The router expects a 'subscription_tier' field in the current_user dict (e.g., "free" or "premium").
#
# FRONTEND (Example with JavaScript fetch):
#   - Generate a meal plan:
#        POST /api/meal-plan/generate
#        Body: { "age": 28, "gender": "female", "weight": 65, "height": 165,
#                "activity_level": "moderate", "goal": "weight_loss", "days": 5,
#                "food_preference": "vegetarian", "allergies": ["dairy"],
#                "medical_conditions": ["diabetes"] }
#        Headers: { "Authorization": "Bearer <token>" }
#   - Get saved plans:
#        GET /api/meal-plan/saved
#
# EXAMPLE INDIAN USER INPUT:
#   - User: Priya, 32 years, female, weight 70 kg, height 160 cm, activity level "light",
#     goal "muscle_gain", days 7, food_preference "vegetarian", allergies ["gluten"],
#     medical_conditions ["thyroid"].
#   - The system calculates BMI and TDEE (Total Daily Energy Expenditure) using standard formulas.
#   - It filters the food database to exclude foods with gluten and those not vegetarian.
#   - Then generates a 7-day meal plan with breakfast, lunch, dinner, snacks, using Indian foods
#     like "Moong Dal Chilla", "Paneer Bhurji", "Brown Rice", "Vegetable Khichdi", etc.
#   - Saves the plan and user profile snapshot to history.
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import APIRouter from FastAPI to create a route group for meal-plan endpoints.
# Depends is used for dependency injection (e.g., getting current authenticated user).
from fastapi import APIRouter, Depends

# Import Dict and List from typing for type hints – specify that we return dictionaries and lists.
from typing import Dict, List

# Import Pydantic models that define the shape of request and response data:
#   - MealPlanRequest: user inputs (age, gender, weight, height, activity, goal, days, preferences, etc.)
#   - MealPlanResponse: structured output (user profile, calorie target, meal plan, day summaries, etc.)
#   - ProfileWithMetrics: includes BMI and TDEE along with basic profile.
#   - MealFood: representation of a single food item in a meal (name, portion, calories, etc.)
#   - DaySummary: aggregated totals (calories, protein, carbs, fat) for a day, with targets.
from models import MealPlanRequest, MealPlanResponse, ProfileWithMetrics, MealFood, DaySummary

# Import utility functions from 'utils.data' module:
#   - load_data: loads food dataset (pandas DataFrame) from CSV/JSON.
#   - filter_foods: applies dietary preferences, allergies, medical conditions, goal to filter foods.
#   - generate_meal_plan: core algorithm that creates daily meals and computes day summaries.
#   - calculate_user_metrics: computes BMI and TDEE based on user parameters.
from utils.data import load_data, filter_foods, generate_meal_plan, calculate_user_metrics

# Import storage utility functions from 'utils.storage':
#   - save_user_profile: stores a snapshot of user profile (with metrics) in profile_history.
#   - save_meal_plan: stores generated meal plan (with day summaries) in meal_plan_history.
from utils.storage import save_user_profile, save_meal_plan

# Import authentication dependency: get_current_active_user ensures the request comes from
# an authenticated and active user. It returns a dict containing user info including username
# and subscription_tier.
from dependencies import get_current_active_user

# --------------------------------------------------------------------------------------------------
# ROUTER INITIALIZATION
# --------------------------------------------------------------------------------------------------
# Create an APIRouter instance with URL prefix '/api/meal-plan' and tag 'Meal Plan' for OpenAPI docs.
# All endpoints will be mounted under /api/meal-plan.
# Example full URL: http://yourdomain.com/api/meal-plan/generate
router = APIRouter(prefix="/api/meal-plan", tags=["Meal Plan"])

# --------------------------------------------------------------------------------------------------
# ENDPOINT 1: POST /api/meal-plan/generate
# --------------------------------------------------------------------------------------------------
# Purpose: Generate a personalized meal plan based on user metrics, preferences, and constraints.
# Request body: JSON matching MealPlanRequest.
# Response: MealPlanResponse containing user profile, daily calorie target, meal plan, and summaries.
# Authentication: Required (get_current_active_user). Subscription tier affects max days.
# Example Indian user request:
#   POST /api/meal-plan/generate
#   Authorization: Bearer <token>
#   Content-Type: application/json
#   Body:
#   {
#       "age": 45,
#       "gender": "male",
#       "weight": 85,
#       "height": 175,
#       "activity_level": "sedentary",
#       "goal": "weight_loss",
#       "days": 10,
#       "food_preference": "vegetarian",
#       "allergies": ["peanut"],
#       "medical_conditions": ["high_blood_pressure"]
#   }
# Example response (abbreviated):
#   {
#       "user_profile": { "age": 45, "gender": "male", "weight": 85, "height": 175,
#                         "activity_level": "sedentary", "goal": "weight_loss", "bmi": 27.8, "tdee": 2100 },
#       "daily_calorie_target": 2100,
#       "meal_plan": { "Day 01": { "breakfast": [...], "lunch": [...], "dinner": [...], "snacks": [...] } },
#       "day_summaries": { "Day 01": { "total_calories": 1850, ... } },
#       "filtered_foods_count": 124
#   }
# --------------------------------------------------------------------------------------------------

@router.post("/generate", response_model=MealPlanResponse)
def generate_meal_plan_endpoint(
    request: MealPlanRequest,
    current_user: Dict = Depends(get_current_active_user)   # dependency ensures user is logged in and active
):
    # Enforce day limits based on subscription tier (free vs premium).
    # The current_user dict contains a field 'subscription_tier' set by the authentication system.
    if current_user["subscription_tier"] == "free" and request.days > 7:
        request.days = 7   # Cap free users to 7 days (or could raise HTTP 403 Forbidden)
    elif current_user["subscription_tier"] == "premium" and request.days > 14:
        request.days = 14  # Premium users get up to 14 days per plan
    # If you want to require authentication, uncomment the following line:
    # current_user: Dict = Depends(get_current_active_user):

    # Calculate BMI (Body Mass Index) and TDEE (Total Daily Energy Expenditure) using user metrics.
    # The function uses standard formulas: BMI = weight(kg) / (height(m))^2.
    # TDEE is based on BMR (Mifflin-St Jeor) multiplied by activity factor, then adjusted by goal.
    bmi, tdee = calculate_user_metrics(
        request.age, request.gender, request.weight, request.height,
        request.activity_level, request.goal
    )
    # Convert the request (Pydantic model) to a dictionary, then add the computed metrics.
    profile_with_metrics = request.dict()
    profile_with_metrics.update({"bmi": bmi, "tdee": tdee})

    # Load the food dataset (pandas DataFrame) from the data source (e.g., CSV).
    df = load_data()
    # Apply filters based on user's preferences, allergies, medical conditions, and goal.
    # This removes foods that contain allergens, violate dietary restrictions, or are unsuitable for
    # the goal (e.g., high-sugar foods for diabetes, high-calorie for weight loss).
    filtered_df = filter_foods(
        df,
        request.food_preference,
        request.allergies,
        request.medical_conditions,
        request.goal
    )

    # Generate the actual meal plan: returns a dictionary of days -> meals, and a dictionary of day summaries.
    # The algorithm uses optimization (e.g., knapsack or greedy) to meet calorie/macro targets while respecting
    # meal structure and food availability.
    meal_plan, day_summaries = generate_meal_plan(
        filtered_df, days=request.days, tdee=tdee, goal=request.goal
    )

    # Optionally save to history (authentication is now active, so we save profile and plan).
    # This stores a snapshot of the user's profile at the time of generation.
    save_user_profile(current_user["username"], profile_with_metrics)
    # If a meal plan was generated (non-empty), save it to the user's meal_plan_history.
    if meal_plan:
        save_meal_plan(current_user["username"], {
            "plan_data": meal_plan,
            "day_summaries": day_summaries,
            "user_profile": profile_with_metrics,
            "food_count": len(filtered_df)   # Number of foods considered after filtering
        })

    # Return the complete response, automatically validated against MealPlanResponse model.
    return MealPlanResponse(
        user_profile=ProfileWithMetrics(**profile_with_metrics),  # Unpack dict into model
        daily_calorie_target=tdee,
        meal_plan=meal_plan,
        day_summaries=day_summaries,
        filtered_foods_count=len(filtered_df)
    )

# --------------------------------------------------------------------------------------------------
# ENDPOINT 2: GET /api/meal-plan/saved
# --------------------------------------------------------------------------------------------------
# Purpose: Retrieve all saved profiles and meal plan histories for the authenticated user.
# Authentication: Required (get_current_active_user).
# Response: JSON object containing 'saved_plans' (list of meal plan dictionaries) and 'profiles' (list of profile snapshots).
# Example Indian user request:
#   GET /api/meal-plan/saved
#   Authorization: Bearer <token>
# Example response:
#   {
#       "saved_plans": [
#           {
#               "plan_id": 1,
#               "timestamp": "2025-03-15 10:30:00",
#               "day_summaries": { "Day 01": {...}, ... },
#               "ratings": { "Day 01": { "stars": 4, "feedback": "Good" } }
#           }
#       ],
#       "profiles": [
#           { "timestamp": "2025-03-15 10:30:00", "age": 32, "weight": 70, "bmi": 27.3, ... }
#       ]
#   }
# --------------------------------------------------------------------------------------------------

@router.get("/saved")
def get_saved_plans(current_user: Dict = Depends(get_current_active_user)):
    # Import get_user_history inside the function to avoid circular imports (if storage imports this module).
    # This function returns a tuple: (list_of_profile_snapshots, list_of_meal_plans)
    from utils.storage import get_user_history
    profiles, meal_plans = get_user_history(current_user["username"])
    # Ratings are already inside each plan (due to storage.py change) – this comment indicates that
    # the storage layer includes ratings in the plan dictionaries when retrieving.
    return {"saved_plans": meal_plans, "profiles": profiles}