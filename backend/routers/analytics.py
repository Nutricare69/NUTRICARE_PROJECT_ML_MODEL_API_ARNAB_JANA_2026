import re
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models import UserProfile
from utils.storage import load_users
from dependencies import get_current_active_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# ========== Helper function for sorting day keys ==========
def day_number(key: str) -> int:
    """
    Convert a day key (e.g., "Day 01", "Monday") into a sortable integer.
    Handles both new "Day XX" format and old weekday names.
    """
    # If key looks like "Day 01", extract the numeric part
    match = re.search(r'\d+', key)
    if match:
        return int(match.group())
    # Otherwise, assume weekday names and map to index (backward compatibility)
    weekday_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                    "Friday": 4, "Saturday": 5, "Sunday": 6}
    return weekday_order.get(key, 0)


# ---------- Endpoint 1: Daily Trends (line chart) ----------
@router.get("/daily-trends")
def get_daily_trends(current_user: Dict = Depends(get_current_active_user)):
    """
    Returns a time series of daily totals (calories, macros) from all saved meal plans.
    Each day from each plan is represented as a point, with the actual date calculated
    from the plan's timestamp and the day offset.
    """
    users = load_users()
    user_data = users.get(current_user["username"])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    plans = user_data.get("meal_plan_history", [])
    if not plans:
        return {"message": "No meal plans found"}

    daily_records = []
    for plan in plans:
        plan_timestamp = plan.get("timestamp")
        if not plan_timestamp:
            continue
        try:
            plan_date = datetime.strptime(plan_timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        day_summaries = plan.get("day_summaries", {})
        if not day_summaries:
            continue

        # Sort day keys (e.g., "Day 01", "Day 02", ...) using the helper
        sorted_days = sorted(day_summaries.keys(), key=day_number)

        for offset, day_key in enumerate(sorted_days):
            day_data = day_summaries[day_key]
            actual_date = plan_date + timedelta(days=offset)
            daily_records.append({
                "date": actual_date.strftime("%Y-%m-%d"),
                "calories": day_data.get("total_calories", 0),
                "protein": day_data.get("total_protein", 0),
                "fat": day_data.get("total_fat", 0),
                "carbs": day_data.get("total_carbs", 0),
                "target_calories": day_data.get("target_calories", 0),
                "target_protein": day_data.get("target_protein", 0),
                "target_fat": day_data.get("target_fat", 0),
                "target_carbs": day_data.get("target_carbs", 0)
            })

    daily_records.sort(key=lambda x: x["date"])
    labels = [rec["date"] for rec in daily_records]
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


# ---------- Endpoint 2: Macro Distribution (pie chart) ----------
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

    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbs = 0

    for plan in plans:
        day_summaries = plan.get("day_summaries", {})
        for day_name, day_data in day_summaries.items():
            total_calories += day_data.get("total_calories", 0)
            total_protein += day_data.get("total_protein", 0)
            total_fat += day_data.get("total_fat", 0)
            total_carbs += day_data.get("total_carbs", 0)

    if total_calories == 0:
        return {"message": "No calorie data available"}

    # Calculate percentages of calories from each macro
    protein_calories = total_protein * 4
    fat_calories = total_fat * 9
    carbs_calories = total_carbs * 4

    total_macro_calories = protein_calories + fat_calories + carbs_calories
    protein_percent = (protein_calories / total_macro_calories) * 100 if total_macro_calories else 0
    fat_percent = (fat_calories / total_macro_calories) * 100 if total_macro_calories else 0
    carbs_percent = (carbs_calories / total_macro_calories) * 100 if total_macro_calories else 0

    return {
        "labels": ["Protein", "Fat", "Carbs"],
        "data": [round(protein_percent, 1), round(fat_percent, 1), round(carbs_percent, 1)],
        "backgroundColors": ["#4caf50", "#ff9800", "#2196f3"]
    }


# ---------- Endpoint 3: Weight & BMI Progress (line chart) ----------
@router.get("/weight-progress")
def get_weight_progress(current_user: Dict = Depends(get_current_active_user)):
    """
    Returns weight and BMI over time from saved profiles.
    """
    users = load_users()
    user_data = users.get(current_user["username"])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    profiles = user_data.get("profile_history", [])
    if not profiles:
        return {"message": "No profiles saved"}

    # Sort by timestamp
    profiles.sort(key=lambda x: x.get("timestamp", ""))

    labels = []
    weights = []
    bmis = []
    for profile in profiles:
        labels.append(profile.get("timestamp", ""))
        weights.append(profile.get("weight", 0))
        bmis.append(profile.get("bmi", 0))

    return {
        "labels": labels,
        "datasets": {
            "weight": weights,
            "bmi": bmis
        }
    }


# ---------- Endpoint 4: Plan Comparison (table/bar chart) ----------
@router.get("/plan-comparison")
def compare_plans(plan_ids: str = None, current_user: Dict = Depends(get_current_active_user)):
    """
    Compare two or more meal plans by their plan_id (comma-separated).
    Returns daily totals for each selected plan.
    """
    if not plan_ids:
        raise HTTPException(status_code=400, detail="plan_ids parameter required (comma-separated)")

    plan_id_list = [int(x.strip()) for x in plan_ids.split(",") if x.strip().isdigit()]
    if len(plan_id_list) < 2:
        raise HTTPException(status_code=400, detail="At least two plan IDs required")

    users = load_users()
    user_data = users.get(current_user["username"])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    plans = user_data.get("meal_plan_history", [])
    selected_plans = [p for p in plans if p.get("plan_id") in plan_id_list]

    if len(selected_plans) != len(plan_id_list):
        raise HTTPException(status_code=404, detail="One or more plan IDs not found")

    comparison = {}
    for plan in selected_plans:
        plan_id = plan["plan_id"]
        day_summaries = plan.get("day_summaries", {})
        if not day_summaries:
            continue

        # Sort day keys using the helper
        sorted_days = sorted(day_summaries.keys(), key=day_number)
        days_data = []
        for day_key in sorted_days:
            day_data = day_summaries[day_key]
            days_data.append({
                "day": day_key,
                "calories": day_data.get("total_calories", 0),
                "protein": day_data.get("total_protein", 0),
                "fat": day_data.get("total_fat", 0),
                "carbs": day_data.get("total_carbs", 0)
            })
        comparison[f"Plan {plan_id}"] = days_data

    # Target info from first plan's first day (for reference)
    target_info = {}
    if selected_plans and selected_plans[0].get("day_summaries"):
        first_plan_days = selected_plans[0]["day_summaries"]
        if first_plan_days:
            sample_day = next(iter(first_plan_days.values()))
            target_info = {
                "target_calories": sample_day.get("target_calories"),
                "target_protein": sample_day.get("target_protein"),
                "target_fat": sample_day.get("target_fat"),
                "target_carbs": sample_day.get("target_carbs")
            }

    return {
        "comparison": comparison,
        "target_info": target_info
    }