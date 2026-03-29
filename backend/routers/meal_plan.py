from fastapi import APIRouter, Depends
from typing import Dict, List  # added missing import
from models import MealPlanRequest, MealPlanResponse, ProfileWithMetrics
from utils.data import load_data, filter_foods, generate_meal_plan, calculate_user_metrics
from utils.storage import save_user_profile, save_meal_plan
from dependencies import get_current_active_user

router = APIRouter(prefix="/api/meal-plan", tags=["Meal Plan"])

@router.post("/generate", response_model=MealPlanResponse)
def generate_meal_plan_endpoint(request: MealPlanRequest,):
                                # current_user: Dict = Depends(get_current_active_user)):
    # Calculate metrics
    bmi, tdee = calculate_user_metrics(
        request.age, request.gender, request.weight, request.height,
        request.activity_level, request.goal
    )
    profile_with_metrics = request.dict()
    profile_with_metrics.update({"bmi": bmi, "tdee": tdee})

    # Load and filter foods
    df = load_data()
    filtered_df = filter_foods(
        df,
        request.food_preference,
        request.allergies,
        request.medical_conditions,
        request.goal
    )

    # Generate meal plan
    meal_plan = generate_meal_plan(filtered_df, days=request.days)

    #Save profile and meal plan to history
    # save_user_profile(current_user["username"], profile_with_metrics)
    # if meal_plan:
    #     save_meal_plan(current_user["username"], {
    #         "plan_data": meal_plan,
    #         "user_profile": profile_with_metrics,
    #         "food_count": len(filtered_df)
    #     })

    return MealPlanResponse(
        user_profile=ProfileWithMetrics(**profile_with_metrics),
        meal_plan=meal_plan,
        filtered_foods_count=len(filtered_df)
    )

@router.get("/saved")
def get_saved_plans(current_user: Dict = Depends(get_current_active_user)):
    from utils.storage import get_user_history
    _, meal_plans = get_user_history(current_user["username"])
    return {"saved_plans": meal_plans}