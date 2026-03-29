from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models import UserProfile
from utils.storage import load_users
from dependencies import get_current_active_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

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

    # Flatten all days from all plans into a list sorted by date
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
        # day_summaries keys are day names (Monday, Tuesday...)
        # We need to map day names to offsets (Monday=0, Tuesday=1, ...)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for offset, day_name in enumerate(day_names):
            if day_name in day_summaries:
                day_data = day_summaries[day_name]
                # Calculate actual date: plan_date + offset days
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

    # Sort by date
    daily_records.sort(key=lambda x: x["date"])

    # Format for Chart.js: separate arrays for labels (dates) and datasets
    labels = [rec["date"] for rec in daily_records]
    calories_consumed = [rec["calories"] for rec in daily_records]
    calories_target = [rec["target_calories"] for rec in daily_records]
    protein_consumed = [rec["protein"] for rec in daily_records]
    protein_target = [rec["target_protein"] for rec in daily_records]
    fat_consumed = [rec["fat"] for rec in daily_records]
    fat_target = [rec["target_fat"] for rec in daily_records]
    carbs_consumed = [rec["carbs"] for rec in daily_records]
    carbs_target = [rec["target_carbs"] for rec in daily_records]

    return {
        "labels": labels,
        "datasets": {
            "calories": calories_consumed,
            "calories_target": calories_target,
            "protein": protein_consumed,
            "protein_target": protein_target,
            "fat": fat_consumed,
            "fat_target": fat_target,
            "carbs": carbs_consumed,
            "carbs_target": carbs_target
        }
    }


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

    # For each plan, extract its day summaries (keyed by day name)
    comparison = {}
    for plan in selected_plans:
        plan_id = plan["plan_id"]
        plan_data = plan.get("day_summaries", {})
        # Convert to list of day totals ordered by day
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_data = []
        for day in day_names:
            if day in plan_data:
                days_data.append({
                    "day": day,
                    "calories": plan_data[day].get("total_calories", 0),
                    "protein": plan_data[day].get("total_protein", 0),
                    "fat": plan_data[day].get("total_fat", 0),
                    "carbs": plan_data[day].get("total_carbs", 0)
                })
        comparison[f"Plan {plan_id}"] = days_data

    # Also return target macro info from the first plan for reference
    first_plan = selected_plans[0]
    target_info = {}
    if first_plan.get("day_summaries"):
        sample_day = list(first_plan["day_summaries"].values())[0]
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