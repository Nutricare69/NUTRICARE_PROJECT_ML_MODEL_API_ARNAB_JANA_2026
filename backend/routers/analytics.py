# --------------------------------------------------------------------------------------------------
# MODULE: analytics.py
# --------------------------------------------------------------------------------------------------
# PURPOSE: Provide analytics endpoints for authenticated users to visualize their nutritional data,
#          meal plan trends, macro distribution, weight/BMI progress, and plan comparisons.
# --------------------------------------------------------------------------------------------------
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# BACKEND (FastAPI):
#   - Place this file in your 'routers' or 'api' directory.
#   - In your main 'main.py' or 'app.py', include the router:
#        from routers import analytics
#        app.include_router(analytics.router)
#   - Ensure the dependencies (get_current_active_user) and storage functions (load_users) are correctly implemented.
#   - The endpoints return JSON that can be consumed by any frontend (React, Vue, Angular, etc.).
#
# FRONTEND (Example with JavaScript fetch):
#   - Fetch daily trends: GET /api/analytics/daily-trends
#   - Fetch macro distribution: GET /api/analytics/macro-distribution
#   - Fetch weight progress: GET /api/analytics/weight-progress
#   - Compare plans: GET /api/analytics/plan-comparison?plan_ids=1,2,3
#
# SAMPLE INDIAN USER DATA (as stored in JSON):
#   "meal_plan_history": [
#       {
#           "plan_id": 1,
#           "timestamp": "2025-03-15 10:30:00",
#           "day_summaries": {
#               "Day 01": {"total_calories": 1850, "total_protein": 70, "total_fat": 45, "total_carbs": 230,
#                          "target_calories": 2000, "target_protein": 75, "target_fat": 55, "target_carbs": 250},
#               "Day 02": {"total_calories": 1920, "total_protein": 68, "total_fat": 50, "total_carbs": 240,
#                          "target_calories": 2000, "target_protein": 75, "target_fat": 55, "target_carbs": 250}
#           }
#       }
#   ],
#   "profile_history": [
#       {"timestamp": "2025-01-10", "weight": 75.5, "bmi": 24.2},
#       {"timestamp": "2025-02-10", "weight": 74.0, "bmi": 23.8}
#   ]
# --------------------------------------------------------------------------------------------------

# ==================================================================================================
# IMPORT SECTION
# ==================================================================================================

# Import 're' (regular expression) – Python standard library, no installation required.
# Used in the helper function 'day_number' to extract numeric part from strings like "Day 01".
import re

# Import FastAPI core components:
#   APIRouter – to group analytics endpoints under a common prefix and tags.
#   Depends – for dependency injection (e.g., getting current authenticated user).
#   HTTPException – to return standard HTTP errors (400, 404) with custom messages.
# Installation: pip install fastapi
from fastapi import APIRouter, Depends, HTTPException

# Import typing helpers: List, Dict, Any – for type hints (code clarity and IDE support).
# These are part of Python's standard typing module.
from typing import List, Dict, Any

# Import datetime and timedelta from Python's standard library for date manipulation.
# Used to calculate actual dates based on plan timestamp and day offsets.
from datetime import datetime, timedelta

# Import the UserProfile model from the local 'models' module.
# This model defines the structure of a user profile (weight, height, age, etc.).
# Even though not directly used in this file, it's kept for future expansion.
from models import UserProfile

# Import 'load_users' function from 'utils.storage' module.
# This function reads the entire users database from a JSON file (or any storage backend).
# It returns a dictionary: {username: user_data_dict}
from utils.storage import load_users

# Import 'get_current_active_user' dependency from 'dependencies' module.
# This function verifies that the request contains a valid JWT token and that the user is active.
# It returns the user dictionary (containing username, email, etc.) or raises 401.
from dependencies import get_current_active_user

# ==================================================================================================
# ROUTER INITIALIZATION
# ==================================================================================================

# Create an APIRouter instance with URL prefix '/api/analytics' and tag 'Analytics' for OpenAPI docs.
# All endpoints defined below will be mounted under this prefix.
# Example full URL: http://yourdomain.com/api/analytics/daily-trends
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# ==================================================================================================
# HELPER FUNCTION: day_number(key: str) -> int
# ==================================================================================================
# Purpose: Convert a day key string into a sortable integer.
# Supports two formats:
#   1. New format: "Day 01", "Day 02", ... → extracts digits (1, 2, ...)
#   2. Old format (backward compatibility): weekday names like "Monday", "Tuesday" → map to 0-6.
# Used when sorting day summaries to ensure correct chronological order.
# Example inputs:
#   - "Day 01" -> 1
#   - "Day 12" -> 12
#   - "Monday" -> 0
#   - "Wednesday" -> 2
# ==================================================================================================

def day_number(key: str) -> int:
    """
    Convert a day key (e.g., "Day 01", "Monday") into a sortable integer.
    Handles both new "Day XX" format and old weekday names.
    """
    # Use regular expression search to find the first group of digits in the string.
    # r'\d+' matches one or more digits. If found, convert to int and return.
    # Example: "Day 01" -> match.group() = "01" -> int("01") = 1
    match = re.search(r'\d+', key)
    if match:
        return int(match.group())
    # If no digits found, assume it's an old weekday name (e.g., "Monday").
    # Map each weekday to its index (0 = Monday, 6 = Sunday) for correct sorting.
    weekday_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                    "Friday": 4, "Saturday": 5, "Sunday": 6}
    # Return the mapped index, defaulting to 0 if key is not found (fallback).
    return weekday_order.get(key, 0)


# ==================================================================================================
# ENDPOINT 1: GET /api/analytics/daily-trends
# ==================================================================================================
# Purpose: Return a time series of daily nutritional totals (calories, protein, fat, carbs)
#          along with their target values, calculated from all saved meal plans.
# Use case: Frontend line chart showing user's progress over time.
# Authentication: Requires a valid active user (via get_current_active_user dependency).
# Response format:
#   {
#     "labels": ["2025-03-15", "2025-03-16", ...],
#     "datasets": {
#       "calories": [1850, 1920, ...],
#       "calories_target": [2000, 2000, ...],
#       "protein": [70, 68, ...],
#       ...
#     }
#   }
# Example Indian user scenario: A user from Delhi logs meals like "chole bhature" (high calories)
# and "dal chawal" (moderate). The endpoint shows daily fluctuations.
# ==================================================================================================

@router.get("/daily-trends")
def get_daily_trends(current_user: Dict = Depends(get_current_active_user)):
    """
    Returns a time series of daily totals (calories, macros) from all saved meal plans.
    Each day from each plan is represented as a point, with the actual date calculated
    from the plan's timestamp and the day offset.
    """
    # Load the entire users database from storage (e.g., users.json)
    users = load_users()
    # Retrieve the specific user's data using the username from the authenticated user.
    # current_user is a dict returned by get_current_active_user, e.g., {"username": "raj_kumar"}
    user_data = users.get(current_user["username"])
    # If user not found in storage (should not happen if auth is consistent), raise 404.
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Get the list of meal plans saved for this user (each plan is a dict).
    # Example: user_data["meal_plan_history"] = [plan1, plan2, ...]
    plans = user_data.get("meal_plan_history", [])
    if not plans:
        # If no plans exist, return a friendly message (instead of empty arrays).
        return {"message": "No meal plans found"}

    # List to accumulate daily records (each record corresponds to one day from one plan)
    daily_records = []

    # Iterate over each meal plan in the user's history
    for plan in plans:
        # Extract the timestamp when this plan was created (stored as string).
        plan_timestamp = plan.get("timestamp")
        if not plan_timestamp:
            # Skip plans without a timestamp (they cannot be placed on a timeline)
            continue
        try:
            # Convert the timestamp string (format "YYYY-MM-DD HH:MM:SS") to a datetime object.
            # Example: "2025-03-15 10:30:00" -> datetime(2025, 3, 15, 10, 30, 0)
            plan_date = datetime.strptime(plan_timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # If the string format doesn't match, skip this plan (invalid data)
            continue

        # Get the day summaries dictionary for this plan.
        # Structure: {"Day 01": {...}, "Day 02": {...}} or old weekday keys.
        day_summaries = plan.get("day_summaries", {})
        if not day_summaries:
            # No day data in this plan – skip
            continue

        # Sort the day keys using our helper function to ensure correct order.
        # Example: ["Day 01", "Day 02", "Day 03"] or ["Monday", "Tuesday", ...]
        sorted_days = sorted(day_summaries.keys(), key=day_number)

        # Iterate over each day with its index (offset) to calculate actual calendar date.
        # offset = 0 for first day, 1 for second, etc.
        for offset, day_key in enumerate(sorted_days):
            day_data = day_summaries[day_key]  # Dictionary with totals for that day
            # Calculate the real date: plan creation date + offset days.
            # Example: plan_date = 2025-03-15, offset=2 → actual_date = 2025-03-17
            actual_date = plan_date + timedelta(days=offset)
            # Append a record with all relevant data for this day.
            daily_records.append({
                "date": actual_date.strftime("%Y-%m-%d"),  # Convert date to string "YYYY-MM-DD"
                "calories": day_data.get("total_calories", 0),
                "protein": day_data.get("total_protein", 0),
                "fat": day_data.get("total_fat", 0),
                "carbs": day_data.get("total_carbs", 0),
                "target_calories": day_data.get("target_calories", 0),
                "target_protein": day_data.get("target_protein", 0),
                "target_fat": day_data.get("target_fat", 0),
                "target_carbs": day_data.get("target_carbs", 0)
            })

    # After processing all plans, sort the daily_records by date (ascending).
    daily_records.sort(key=lambda x: x["date"])
    # Extract labels (dates) as a list of strings for the x-axis of the chart.
    labels = [rec["date"] for rec in daily_records]
    # Return structured data suitable for a line chart with multiple datasets.
    return {
        "labels": labels,
        "datasets": {
            "calories": [rec["calories"] for rec in daily_records],
            "calories_target": [rec["target_calories"] for rec in daily_records],
            "protein": [rec["protein"] for rec in daily_records],
            "protein_target": [rec["target_protein"] for rec in daily_records],
            "fat": [rec["fat"] for rec in daily_records],
            "fat_target": [rec["target_fat"] for rec in daily_records],
            "carbs": [rec["carbs"] for rec in daily_records],
            "carbs_target": [rec["target_carbs"] for rec in daily_records]
        }
    }


# ==================================================================================================
# ENDPOINT 2: GET /api/analytics/macro-distribution
# ==================================================================================================
# Purpose: Compute average percentage of calories coming from protein, fat, and carbohydrates
#          across all saved meal plans. Ideal for a pie chart visualization.
# Authentication: Requires valid active user.
# Response format:
#   {
#     "labels": ["Protein", "Fat", "Carbs"],
#     "data": [22.5, 35.2, 42.3],
#     "backgroundColors": ["#4caf50", "#ff9800", "#2196f3"]
#   }
# Example Indian input: A user who eats a typical Indian vegetarian diet may get ~15% protein,
# 30% fat (from ghee/oil), 55% carbs (from rice/roti). This endpoint quantifies that.
# ==================================================================================================

@router.get("/macro-distribution")
def get_macro_distribution(current_user: Dict = Depends(get_current_active_user)):
    """
    Returns average macro percentages (protein, fat, carbs) across all saved meal plans.
    Useful for a pie chart.
    """
    users = load_users()
    user_data = users.get(current_user["username"])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    plans = user_data.get("meal_plan_history", [])
    if not plans:
        return {"message": "No meal plans found"}

    # Accumulate total grams of each macronutrient across all days of all plans.
    total_calories = 0
    total_protein = 0   # in grams
    total_fat = 0       # in grams
    total_carbs = 0     # in grams

    for plan in plans:
        day_summaries = plan.get("day_summaries", {})
        # Iterate over each day's data (values are the day summary dicts)
        for day_name, day_data in day_summaries.items():
            total_calories += day_data.get("total_calories", 0)
            total_protein += day_data.get("total_protein", 0)
            total_fat += day_data.get("total_fat", 0)
            total_carbs += day_data.get("total_carbs", 0)

    if total_calories == 0:
        # Avoid division by zero; return message instead of error.
        return {"message": "No calorie data available"}

    # Calculate the calories contributed by each macronutrient:
    # Protein: 4 calories per gram
    # Fat: 9 calories per gram
    # Carbohydrates: 4 calories per gram
    protein_calories = total_protein * 4
    fat_calories = total_fat * 9
    carbs_calories = total_carbs * 4

    total_macro_calories = protein_calories + fat_calories + carbs_calories
    # Compute percentages relative to total macro calories (should be close to total_calories).
    protein_percent = (protein_calories / total_macro_calories) * 100 if total_macro_calories else 0
    fat_percent = (fat_calories / total_macro_calories) * 100 if total_macro_calories else 0
    carbs_percent = (carbs_calories / total_macro_calories) * 100 if total_macro_calories else 0

    # Return data formatted for a pie chart (Chart.js, D3, etc.)
    return {
        "labels": ["Protein", "Fat", "Carbs"],
        "data": [round(protein_percent, 1), round(fat_percent, 1), round(carbs_percent, 1)],
        "backgroundColors": ["#4caf50", "#ff9800", "#2196f3"]  # Green, Orange, Blue
    }


# ==================================================================================================
# ENDPOINT 3: GET /api/analytics/weight-progress
# ==================================================================================================
# Purpose: Return a time series of user's weight and BMI from all saved profile snapshots.
# Use case: Frontend line chart to track weight loss/gain over time.
# Authentication: Requires valid active user.
# Response format:
#   {
#     "labels": ["2025-01-10", "2025-02-10", "2025-03-10"],
#     "datasets": {
#       "weight": [75.5, 74.0, 72.3],
#       "bmi": [24.2, 23.8, 23.1]
#     }
#   }
# Example Indian input: A user from Mumbai logs weight monthly: initial 80 kg, after 3 months 75 kg.
# BMI is calculated from height (e.g., 1.75m) and weight.
# ==================================================================================================

@router.get("/weight-progress")
def get_weight_progress(current_user: Dict = Depends(get_current_active_user)):
    """
    Returns weight and BMI over time from saved profiles.
    """
    users = load_users()
    user_data = users.get(current_user["username"])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve the list of profile snapshots (each contains weight, bmi, timestamp)
    profiles = user_data.get("profile_history", [])
    if not profiles:
        return {"message": "No profiles saved"}

    # Sort the profiles by their timestamp (ascending) to ensure chronological order.
    # The lambda uses .get("timestamp", "") to handle missing keys gracefully.
    profiles.sort(key=lambda x: x.get("timestamp", ""))

    labels = []
    weights = []
    bmis = []
    for profile in profiles:
        # Append the timestamp as the label (x-axis value)
        labels.append(profile.get("timestamp", ""))
        # Append weight (in kg) – ensure default 0 if missing
        weights.append(profile.get("weight", 0))
        # Append BMI (Body Mass Index) – calculated during profile creation
        bmis.append(profile.get("bmi", 0))

    return {
        "labels": labels,
        "datasets": {
            "weight": weights,
            "bmi": bmis
        }
    }


# ==================================================================================================
# ENDPOINT 4: GET /api/analytics/plan-comparison
# ==================================================================================================
# Purpose: Compare two or more meal plans side by side. Accepts a comma-separated list of plan_ids.
# Use case: Frontend table or grouped bar chart to compare nutritional totals across different plans.
# Authentication: Requires valid active user.
# Query parameter: plan_ids (e.g., ?plan_ids=1,2,3)
# Response format:
#   {
#     "comparison": {
#       "Plan 1": [
#         {"day": "Day 01", "calories": 1850, "protein": 70, "fat": 45, "carbs": 230},
#         {"day": "Day 02", "calories": 1920, ...}
#       ],
#       "Plan 2": [...]
#     },
#     "target_info": {
#       "target_calories": 2000,
#       "target_protein": 75,
#       "target_fat": 55,
#       "target_carbs": 250
#     }
#   }
# Example Indian input: Compare a "vegetarian plan" (plan_id=1) with an "egg-inclusive plan" (plan_id=2)
# to see which provides better protein intake for a user from Chennai.
# ==================================================================================================

@router.get("/plan-comparison")
def compare_plans(plan_ids: str = None, current_user: Dict = Depends(get_current_active_user)):
    """
    Compare two or more meal plans by their plan_id (comma-separated).
    Returns daily totals for each selected plan.
    """
    # Validate that the 'plan_ids' query parameter was provided.
    if not plan_ids:
        raise HTTPException(status_code=400, detail="plan_ids parameter required (comma-separated)")

    # Split the comma-separated string into a list of integers.
    # Example: "1,2,3" -> [1, 2, 3]
    # .strip() removes whitespace, .isdigit() ensures only numeric characters.
    plan_id_list = [int(x.strip()) for x in plan_ids.split(",") if x.strip().isdigit()]
    # Require at least two plan IDs for a meaningful comparison.
    if len(plan_id_list) < 2:
        raise HTTPException(status_code=400, detail="At least two plan IDs required")

    users = load_users()
    user_data = users.get(current_user["username"])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Get the full list of meal plans from user data.
    plans = user_data.get("meal_plan_history", [])
    # Filter only those plans whose plan_id is in the requested list.
    selected_plans = [p for p in plans if p.get("plan_id") in plan_id_list]

    # Ensure that we found all requested plans (no missing IDs).
    if len(selected_plans) != len(plan_id_list):
        raise HTTPException(status_code=404, detail="One or more plan IDs not found")

    # Dictionary to hold comparison data keyed by plan identifier (e.g., "Plan 1")
    comparison = {}

    # Process each selected plan
    for plan in selected_plans:
        plan_id = plan["plan_id"]  # e.g., 1, 2, 3
        day_summaries = plan.get("day_summaries", {})
        if not day_summaries:
            # If a plan has no day data, skip adding it to comparison (or continue with empty list)
            continue

        # Sort the day keys (e.g., "Day 01", "Day 02") using the helper function.
        sorted_days = sorted(day_summaries.keys(), key=day_number)
        days_data = []
        for day_key in sorted_days:
            day_data = day_summaries[day_key]
            # For each day, create a small dictionary with day name and nutritional totals.
            days_data.append({
                "day": day_key,
                "calories": day_data.get("total_calories", 0),
                "protein": day_data.get("total_protein", 0),
                "fat": day_data.get("total_fat", 0),
                "carbs": day_data.get("total_carbs", 0)
            })
        # Store under a friendly key like "Plan 1"
        comparison[f"Plan {plan_id}"] = days_data

    # Extract target information from the first plan's first day (assuming all plans share same targets).
    # This is used as a reference for the user (e.g., "Your daily target is 2000 calories").
    target_info = {}
    if selected_plans and selected_plans[0].get("day_summaries"):
        first_plan_days = selected_plans[0]["day_summaries"]
        if first_plan_days:
            # Get the first day's data (any day works, since targets are usually constant across days)
            sample_day = next(iter(first_plan_days.values()))
            target_info = {
                "target_calories": sample_day.get("target_calories"),
                "target_protein": sample_day.get("target_protein"),
                "target_fat": sample_day.get("target_fat"),
                "target_carbs": sample_day.get("target_carbs")
            }

    # Return both the comparison data and the reference target info.
    return {
        "comparison": comparison,
        "target_info": target_info
    }