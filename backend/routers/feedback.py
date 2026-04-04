from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from models import RatingRequest, RatingResponse, UserFeedbackSummary
from utils.storage import add_rating_to_meal_plan, get_user_feedback, get_all_users_feedback
from dependencies import get_current_active_user, get_current_admin

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

@router.post("/rate", response_model=Dict)
def rate_meal_plan_day(
    rating: RatingRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """Submit a rating (1-5 stars) and optional feedback for a specific day of a saved meal plan."""
    success = add_rating_to_meal_plan(
        username=current_user["username"],
        plan_id=rating.plan_id,
        day_name=rating.day_name,
        stars=rating.stars,
        feedback=rating.feedback
    )
    if not success:
        raise HTTPException(status_code=404, detail="Meal plan or user not found")
    return {"message": "Rating saved successfully"}

@router.get("/my-feedback", response_model=List[RatingResponse])
def get_my_feedback(current_user: Dict = Depends(get_current_active_user)):
    """Get all ratings and feedback submitted by the logged-in user."""
    feedback_data = get_user_feedback(current_user["username"])
    # Convert to list of RatingResponse
    return [
        RatingResponse(
            plan_id=item["plan_id"],
            day_name=item["day_name"],
            stars=item["stars"],
            feedback=item.get("feedback"),
            rated_at=item["rated_at"]
        )
        for item in feedback_data
    ]

@router.get("/admin/all-feedback")
def get_all_feedback_admin(_: Dict = Depends(get_current_admin)):
    """Admin only: retrieve all ratings and feedback from all users."""
    return get_all_users_feedback()