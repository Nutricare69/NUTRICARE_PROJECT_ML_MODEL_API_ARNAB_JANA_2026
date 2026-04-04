# ==================================================================================================
# MODULE: main.py
# ==================================================================================================
# PURPOSE: Entry point for the NUTRI-CARE FastAPI backend application.
#          Configures CORS, includes all API routers, and initializes default admin account.
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# 
# BACKEND (FastAPI):
#   - This is the main file you run with: uvicorn main:app --reload
#   - It aggregates all routers from the 'routers' package (auth, users, meal_plan, admin, foods, analysis, analytics, feedback).
#   - On startup, it calls create_admin_account() to ensure a default admin exists (username: "admin", password: "admin123").
#   - CORS middleware is configured to allow cross-origin requests from any frontend (for development).
#   - In production, restrict 'allow_origins' to your actual frontend domain (e.g., "https://nutricare.example.com").
#
# FRONTEND (React/Angular/Vue):
#   - The frontend application (e.g., built with React) runs on a different origin (e.g., http://localhost:3000).
#   - CORS settings allow the frontend to call API endpoints like http://localhost:8000/api/auth/login.
#   - Example fetch call from a React component (Indian user context):
#        const response = await fetch('http://localhost:8000/api/auth/login', {
#            method: 'POST',
#            headers: { 'Content-Type': 'application/json' },
#            body: JSON.stringify({ username: 'priya_sharma', password: 'Pass@123' })
#        });
#   - After login, store JWT token and include it in subsequent requests:
#        headers: { 'Authorization': `Bearer ${token}` }
#
# SAMPLE INDIAN USER SCENARIO:
#   1. User "raj_verma" registers via frontend -> POST /api/auth/register.
#   2. Admin "admin" (default) logs in via /api/auth/admin/login.
#   3. Admin upgrades "raj_verma" to premium via POST /api/admin/users/raj_verma/upgrade.
#   4. Raj generates a 14-day Indian diet plan (since premium) via POST /api/meal-plan/generate.
#   5. Frontend displays the plan with foods like "Masala Dosa", "Paneer Tikka", "Dal Makhani".
#   6. Raj rates each day's meals using POST /api/feedback/rate.
#   7. Admin views aggregated feedback via GET /api/feedback/admin/all-feedback.
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import FastAPI class to create the main application instance.
from fastapi import FastAPI
# Import CORSMiddleware to handle Cross-Origin Resource Sharing (allows frontend to call API from different domain).
from fastapi.middleware.cors import CORSMiddleware

# Import all routers from the 'routers' package (each router is an APIRouter instance).
# The 'routers' directory should contain auth.py, users.py, meal_plan.py, admin.py, foods.py, analysis.py, analytics.py, feedback.py.
from routers import auth, users, meal_plan, admin, foods, analysis, analytics, feedback
# Import the function that creates a default admin account if none exists.
from utils.storage import create_admin_account

# --------------------------------------------------------------------------------------------------
# INITIALIZATION: CREATE DEFAULT ADMIN ACCOUNT (RUNS ON STARTUP)
# --------------------------------------------------------------------------------------------------
# This function checks if an admin user exists in users.json; if not, creates one with:
#   username: "admin"
#   password: "admin123" (hashed)
#   user_type: "admin"
#   subscription_tier: "premium"
# This ensures that there is always at least one admin for the system.
create_admin_account()

# --------------------------------------------------------------------------------------------------
# CREATE FASTAPI APPLICATION INSTANCE
# --------------------------------------------------------------------------------------------------
# Instantiate the FastAPI app with metadata for automatic API documentation (Swagger UI at /docs).
app = FastAPI(
    title="NUTRI-CARE API",                                 # Title shown in API docs
    description="AI-Powered Indian Diet Planner",          # Brief description
    version="1.0.0"                                        # Version number
)

# --------------------------------------------------------------------------------------------------
# CORS MIDDLEWARE CONFIGURATION
# --------------------------------------------------------------------------------------------------
# Add CORS middleware to allow web browsers to make requests from a different origin.
# This is essential when frontend (e.g., React on port 3000) and backend (port 8000) run separately.
app.add_middleware(
    CORSMiddleware,
    # Allow all origins for development. In production, replace ["*"] with specific frontend URL(s),
    # e.g., ["https://nutricare.example.com", "http://localhost:3000"].
    allow_origins=["*"],
    # Allow cookies and authorization headers to be included in cross-origin requests.
    allow_credentials=True,
    # Allow all HTTP methods (GET, POST, PUT, DELETE, OPTIONS, etc.).
    allow_methods=["*"],
    # Allow all headers (e.g., Authorization, Content-Type).
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------------------
# INCLUDE ALL API ROUTERS
# --------------------------------------------------------------------------------------------------
# Each router is mounted under its own prefix (e.g., /api/auth, /api/user, /api/meal-plan, etc.)
# The prefixes and tags are defined inside each router file.

# Authentication endpoints: /api/auth/register, /api/auth/login, /api/auth/admin/login
app.include_router(auth.router)

# User profile and history endpoints: /api/user/profile, /api/user/history
app.include_router(users.router)

# Meal plan generation and saved plans: /api/meal-plan/generate, /api/meal-plan/saved
app.include_router(meal_plan.router)

# Admin endpoints: /api/admin/stats, /api/admin/users, /api/admin/users/{username}/status, etc.
app.include_router(admin.router)

# Food listing and search endpoints: /api/foods/, /api/foods/{food_name}
app.include_router(foods.router)

# Image analysis endpoint: /api/analysis/food-image (mock implementation)
app.include_router(analysis.router)

# Analytics endpoints (daily trends, macro distribution, weight progress, plan comparison)
app.include_router(analytics.router)

# Feedback endpoints (submit rating, get my feedback, admin all feedback)
app.include_router(feedback.router)

# --------------------------------------------------------------------------------------------------
# ROOT ENDPOINT: GET /
# --------------------------------------------------------------------------------------------------
# Simple welcome endpoint to verify the API is running.
@app.get("/")
def root():
    # Returns a JSON object with a welcome message.
    return {"message": "Welcome to NUTRI-CARE API"}