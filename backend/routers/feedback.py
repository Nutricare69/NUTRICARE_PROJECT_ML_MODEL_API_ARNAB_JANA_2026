# ==================================================================================================
# MODULE: feedback.py
# ==================================================================================================
# PURPOSE: Allow users to submit ratings (stars) and textual feedback for specific days of their
#          saved meal plans. Also provide endpoints to retrieve user's own feedback and admin
#          access to all user feedback.
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# 
# BACKEND (FastAPI):
#   - Place this file in your 'routers' or 'api' directory.
#   - In your main 'main.py' or 'app.py', include the router:
#        from routers import feedback
#        app.include_router(feedback.router)
#   - Ensure the utility functions (add_rating_to_meal_plan, get_user_feedback, get_all_users_feedback)
#     are implemented in 'utils/storage.py' and that they persist feedback data (e.g., in JSON or DB).
#   - The endpoints return JSON responses that can be consumed by any frontend.
#
# FRONTEND (Example with JavaScript fetch):
#   - Submit rating for a meal plan day:
#        POST /api/feedback/rate
#        Body: {"plan_id": 1, "day_name": "Day 02", "stars": 4, "feedback": "Good taste but less protein"}
#   - Get my feedback:
#        GET /api/feedback/my-feedback
#        (Requires authentication token in header)
#   - Admin get all feedback:
#        GET /api/feedback/admin/all-feedback
#        (Requires admin authentication)
#
# EXAMPLE INDIAN USER DATA & SCENARIOS:
#   - A user named "priya_verma" from Delhi follows a "North Indian Vegetarian Plan" (plan_id=1).
#   - After eating "Day 03" which includes "Paneer Butter Masala" and "Naan", she rates it 5 stars
#     with feedback: "Very tasty, but a bit heavy. Could reduce oil."
#   - Another user "amit_kumar" from Mumbai rates "Day 05" (South Indian plan) 3 stars with feedback:
#     "Sambar was too watery, rice portion too large."
#   - Admin can view all such feedback to improve meal plans.
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import APIRouter from FastAPI to create a route group for feedback endpoints.
# Depends is used for dependency injection (to get current user or admin).
# HTTPException is used to return standard HTTP errors (404, 401, etc.).
from fastapi import APIRouter, Depends, HTTPException

# Import List and Dict from typing for type hints – improves code readability and IDE support.
from typing import List, Dict

# Import Pydantic models that define request/response shapes:
#   - RatingRequest: expects plan_id (int), day_name (str), stars (int 1-5), feedback (optional str)
#   - RatingResponse: returned when retrieving feedback (includes rated_at timestamp)
#   - UserFeedbackSummary: might be used for aggregate stats (not directly used here but imported for completeness)
from models import RatingRequest, RatingResponse, UserFeedbackSummary

# Import storage utility functions:
#   - add_rating_to_meal_plan: stores a rating/feedback for a specific day of a meal plan.
#   - get_user_feedback: retrieves all feedback submitted by a given user.
#   - get_all_users_feedback: retrieves all feedback from all users (admin only).
from utils.storage import add_rating_to_meal_plan, get_user_feedback, get_all_users_feedback

# Import authentication dependencies:
#   - get_current_active_user: ensures the request is from an authenticated active user (returns user dict).
#   - get_current_admin: ensures the user has admin privileges (returns admin dict).
from dependencies import get_current_active_user, get_current_admin

# --------------------------------------------------------------------------------------------------
# ROUTER INITIALIZATION
# --------------------------------------------------------------------------------------------------
# Create an APIRouter instance with URL prefix '/api/feedback' and tag 'Feedback' for OpenAPI docs.
# All endpoints defined below will be mounted under /api/feedback.
# Example full URL: http://yourdomain.com/api/feedback/rate
router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

# --------------------------------------------------------------------------------------------------
# ENDPOINT 1: POST /api/feedback/rate
# --------------------------------------------------------------------------------------------------
# Purpose: Submit a rating (1-5 stars) and optional textual feedback for a specific day of a saved meal plan.
# Request body: JSON matching RatingRequest model.
# Response: JSON with success message.
# Error: 404 if meal plan or user not found.
# Example Indian user request:
#   POST /api/feedback/rate
#   Authorization: Bearer <token>
#   Content-Type: application/json
#   Body: {
#       "plan_id": 3,
#       "day_name": "Day 04",
#       "stars": 5,
#       "feedback": "Excellent! The 'Chole Bhature' was delicious but I'd prefer less oil."
#   }
# Example response (success):
#   {"message": "Rating saved successfully"}
# Example response (failure, plan not found):
#   {"detail": "Meal plan or user not found"}
# --------------------------------------------------------------------------------------------------

@router.post("/rate", response_model=Dict)
def rate_meal_plan_day(
    rating: RatingRequest,                       # The rating data from request body (automatically parsed by FastAPI)
    current_user: Dict = Depends(get_current_active_user)  # Dependency that provides the authenticated user's info
):
    """Submit a rating (1-5 stars) and optional feedback for a specific day of a saved meal plan."""
    # Call the storage function to persist the rating.
    # It will:
    #   1. Locate the user by username.
    #   2. Find the meal plan by plan_id within that user's meal_plan_history.
    #   3. Find the specific day (day_name) within that plan's day_summaries.
    #   4. Add the rating and feedback (with timestamp) to that day's data.
    # Returns True if successful, False if user or plan or day not found.
    success = add_rating_to_meal_plan(
        username=current_user["username"],   # Extract username from authenticated user dict
        plan_id=rating.plan_id,              # e.g., 3
        day_name=rating.day_name,            # e.g., "Day 04"
        stars=rating.stars,                  # e.g., 5
        feedback=rating.feedback             # e.g., "Excellent! ..."
    )
    # If the storage function returns False, raise HTTP 404 error with appropriate detail.
    if not success:
        raise HTTPException(status_code=404, detail="Meal plan or user not found")
    # On success, return a simple JSON message.
    return {"message": "Rating saved successfully"}

# --------------------------------------------------------------------------------------------------
# ENDPOINT 2: GET /api/feedback/my-feedback
# --------------------------------------------------------------------------------------------------
# Purpose: Retrieve all ratings and feedback submitted by the currently authenticated user.
# Authentication: Requires valid active user (non-admin allowed).
# Response: List of RatingResponse objects (each contains plan_id, day_name, stars, feedback, rated_at).
# Example Indian user response (for user "priya_verma"):
#   GET /api/feedback/my-feedback
#   Authorization: Bearer <token>
#   Response body:
#   [
#       {
#           "plan_id": 1,
#           "day_name": "Day 03",
#           "stars": 5,
#           "feedback": "Very tasty, but a bit heavy. Could reduce oil.",
#           "rated_at": "2025-03-16T12:34:56"
#       },
#       {
#           "plan_id": 2,
#           "day_name": "Day 01",
#           "stars": 3,
#           "feedback": "Too much rice, less vegetables.",
#           "rated_at": "2025-03-20T08:15:22"
#       }
#   ]
# --------------------------------------------------------------------------------------------------

@router.get("/my-feedback", response_model=List[RatingResponse])
def get_my_feedback(current_user: Dict = Depends(get_current_active_user)):
    """Get all ratings and feedback submitted by the logged-in user."""
    # Call storage function to retrieve raw feedback data for this user.
    # Returns a list of dictionaries, each with keys: plan_id, day_name, stars, feedback, rated_at
    feedback_data = get_user_feedback(current_user["username"])
    # Convert each dictionary into a RatingResponse Pydantic model.
    # Using list comprehension for conciseness.
    # .get("feedback") returns None if key missing (optional field).
    return [
        RatingResponse(
            plan_id=item["plan_id"],
            day_name=item["day_name"],
            stars=item["stars"],
            feedback=item.get("feedback"),   # May be None if no text feedback provided
            rated_at=item["rated_at"]        # Timestamp string (e.g., ISO format)
        )
        for item in feedback_data
    ]

# --------------------------------------------------------------------------------------------------
# ENDPOINT 3: GET /api/feedback/admin/all-feedback
# --------------------------------------------------------------------------------------------------
# Purpose: Admin-only endpoint to retrieve all ratings and feedback from all users.
# Authentication: Requires admin privileges (via get_current_admin dependency).
# Response: Structured data containing all users' feedback (format depends on storage implementation).
# Example admin response (aggregated):
#   GET /api/feedback/admin/all-feedback
#   Authorization: Bearer <admin_token>
#   Response body:
#   {
#       "total_ratings": 45,
#       "average_stars": 4.2,
#       "feedbacks": [
#           {
#               "username": "priya_verma",
#               "plan_id": 1,
#               "day_name": "Day 03",
#               "stars": 5,
#               "feedback": "Very tasty, but a bit heavy...",
#               "rated_at": "2025-03-16T12:34:56"
#           },
#           {
#               "username": "amit_kumar",
#               "plan_id": 2,
#               "day_name": "Day 05",
#               "stars": 3,
#               "feedback": "Sambar was too watery...",
#               "rated_at": "2025-03-18T19:20:00"
#           }
#       ]
#   }
# Note: The exact structure depends on what get_all_users_feedback() returns.
# --------------------------------------------------------------------------------------------------

@router.get("/admin/all-feedback")
def get_all_feedback_admin(_: Dict = Depends(get_current_admin)):
    """Admin only: retrieve all ratings and feedback from all users."""
    # The underscore '_' indicates we don't need to use the returned admin dict, but the dependency still runs.
    # Call the storage function that collects feedback across all users.
    # This may return a dictionary with aggregated statistics and detailed list.
    return get_all_users_feedback()