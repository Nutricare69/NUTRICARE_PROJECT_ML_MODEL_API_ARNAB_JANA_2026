from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, meal_plan, admin, foods, analysis, analytics
from utils.storage import create_admin_account

# Create default admin on startup
create_admin_account()

app = FastAPI(
    title="NUTRI-CARE API",
    description="AI-Powered Indian Diet Planner",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(meal_plan.router)
app.include_router(admin.router)
app.include_router(foods.router)
app.include_router(analysis.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "Welcome to NUTRI-CARE API"}