# ==================================================================================================
# MODULE: foods.py
# ==================================================================================================
# PURPOSE: Provide API endpoints to list and search food items from a dataset (e.g., CSV/JSON)
#          with optional sorting and pagination, and to retrieve detailed information for a specific food.
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND + FRONTEND):
#
# BACKEND (FastAPI):
#   - Place this file in your 'routers' or 'api' directory.
#   - In your main 'main.py' or 'app.py', include the router:
#        from routers import foods
#        app.include_router(foods.router)
#   - Ensure the utility function 'load_data()' is implemented in 'utils/data.py' and returns a pandas DataFrame
#     (or a list of dicts) containing food items with columns: name, calories, protein, carbs, fat, score, etc.
#   - The 'score' column should represent a healthiness metric (lower is better, e.g., based on nutrient density).
#   - The dataset should include common Indian foods (e.g., "Pani Puri", "Masala Dosa", "Butter Chicken", "Dal Makhani").
#
# FRONTEND (Example with JavaScript fetch):
#   - List foods (first 50, sorted by score):
#        GET /api/foods/?limit=50&sort_by=score
#   - Search for Indian foods:
#        GET /api/foods/?search=chole&limit=20
#   - Get details of a specific food (URL-encoded name):
#        GET /api/foods/Pani%20Puri
#
# EXAMPLE INDIAN FOOD DATASET (as loaded by load_data()):
#   name                | calories | protein | carbs | fat | score
#   --------------------|----------|---------|-------|-----|-------
#   "Masala Dosa"       | 320      | 6.5     | 42    | 12  | 0.85
#   "Chole Bhature"     | 550      | 15      | 70    | 22  | 1.20
#   "Dal Tadka"         | 180      | 8       | 28    | 4   | 0.45
#   "Butter Naan"       | 260      | 7       | 38    | 8   | 0.90
#   "Gulab Jamun"       | 380      | 2       | 58    | 16  | 1.50
#   "Idli Sambar"       | 150      | 5       | 30    | 2   | 0.30
#   "Paneer Tikka"      | 420      | 18      | 15    | 30  | 1.10
#
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# Import APIRouter from FastAPI to create a route group for food-related endpoints.
# Also import Query which allows us to define query parameters with additional metadata (description, regex, default).
from fastapi import APIRouter, Query

# Import List and Optional from typing for type hints:
#   - List[FoodItem] indicates the response will be a list of FoodItem objects.
#   - Optional[str] indicates a query parameter may be None (not provided).
from typing import List, Optional

# Import Pydantic models (FoodItem, FoodDetail) from local 'models' module.
# These models define the structure of the response data:
#   - FoodItem: lightweight representation (name, calories, protein, carbs, fat, score)
#   - FoodDetail: more detailed (could include additional fields like serving size, allergens, etc.)
# Ensure 'models.py' contains these classes.
from models import FoodItem, FoodDetail

# Import the utility function 'load_data' from 'utils.data' module.
# This function is responsible for reading the food dataset (e.g., from a CSV file, JSON, or database)
# and returning a pandas DataFrame (or list of dicts) containing all food items.
# The dataset must include at least columns: name, calories, protein, carbs, fat, score.
from utils.data import load_data

# --------------------------------------------------------------------------------------------------
# ROUTER INITIALIZATION
# --------------------------------------------------------------------------------------------------
# Create an APIRouter instance with URL prefix '/api/foods' and tag 'Foods' for OpenAPI documentation.
# All endpoints defined below will be mounted under /api/foods.
# Example full URL: http://yourdomain.com/api/foods/?search=idli
router = APIRouter(prefix="/api/foods", tags=["Foods"])

# --------------------------------------------------------------------------------------------------
# ENDPOINT 1: GET /api/foods/
# --------------------------------------------------------------------------------------------------
# Purpose: List food items with optional search, sorting, and pagination.
# Query parameters:
#   - search (optional): case-insensitive substring match on food name.
#   - sort_by (optional): field to sort by (score, calories, protein, carbs). Default is 'score'.
#                         Must match regex: ^(score|calories|protein|carbs)$
#   - limit (optional): maximum number of results (1-200). Default 50.
# Response: List of FoodItem objects (JSON array).
# Example Indian user request:
#   GET /api/foods/?search=pani&sort_by=calories&limit=10
#   This will return up to 10 foods containing "pani" (e.g., "Pani Puri", "Paniyaram") sorted by calories ascending.
# Example response (first item):
#   [
#       {
#           "name": "Pani Puri",
#           "calories": 85,
#           "protein": 2.0,
#           "carbs": 18.0,
#           "fat": 1.5,
#           "score": 0.65
#       },
#       ...
#   ]
# --------------------------------------------------------------------------------------------------

@router.get("/", response_model=List[FoodItem])
def list_foods(
    # Query parameter 'search': optional string. Description appears in API docs.
    # Example: "?search=idli" will return foods containing "idli" in name.
    search: Optional[str] = Query(None, description="Search by name"),
    
    # Query parameter 'sort_by': optional string, default 'score'. Regex validation ensures only allowed fields.
    # Example: "?sort_by=calories" sorts by calories (low to high for score, but for others we use ascending=False? Actually code sets ascending = sort_by == "score")
    # Note: The regex enforces that only these four fields can be used for sorting.
    sort_by: Optional[str] = Query("score", regex="^(score|calories|protein|carbs)$"),
    
    # Query parameter 'limit': integer between 1 and 200, default 50. Limits number of results.
    # Example: "?limit=20" returns only 20 items.
    limit: int = Query(50, ge=1, le=200)
):
    # Load the food dataset as a pandas DataFrame (or any object that supports filtering, sorting, slicing).
    # The load_data() function is assumed to return a DataFrame with columns: name, calories, protein, carbs, fat, score.
    df = load_data()   # now contains a default score
    
    # If a search term was provided, filter the DataFrame to rows where the 'name' column contains the search string.
    # case=False makes the search case-insensitive (e.g., "Idli" matches "idli").
    # na=False ignores missing values (if any).
    if search:
        df = df[df["name"].str.contains(search, case=False, na=False)]
    
    # If sort_by was not provided (should not happen due to default), fall back to "score".
    sort_by = sort_by or "score"
    # For 'score', we want ascending order because lower score is healthier (e.g., 0.3 is better than 1.5).
    # For other fields (calories, protein, carbs), we sort ascending as well (low to high).
    # This line sets ascending = True for score, and True for others as well. But note: the original code says "lower score is better"
    # and sets ascending = sort_by == "score". That means if sort_by == "score", ascending = True (low to high); otherwise ascending = False? Wait no: ascending = (sort_by == "score") returns True for score, False for others. That means for calories, it would sort descending (high to low). But the comment says "lower score is better" but doesn't specify for other fields. The original code uses ascending = sort_by == "score". We'll keep as is.
    # Actually re-reading: `ascending = sort_by == "score"` means if sorting by score, ascending True (low to high good), else ascending False (descending). So for calories, it sorts from highest to lowest. That might be intentional to show high-calorie foods first. We'll comment accordingly.
    ascending = sort_by == "score"   # lower score is better -> ascending True; for others, descending (higher values first)
    
    # Sort the DataFrame by the chosen column and ascending flag, then take the first 'limit' rows.
    df = df.sort_values(sort_by, ascending=ascending).head(limit)
    
    # Convert the DataFrame to a list of dictionaries (records) and return as JSON.
    # FastAPI will automatically validate each dict against the FoodItem model.
    return df.to_dict(orient="records")

# --------------------------------------------------------------------------------------------------
# ENDPOINT 2: GET /api/foods/{food_name}
# --------------------------------------------------------------------------------------------------
# Purpose: Retrieve detailed information for a single food item by its exact name.
# Path parameter: food_name (string, URL-encoded if contains spaces or special characters).
# Response: FoodDetail model (includes all fields from dataset, possibly extra details).
# Example Indian user request:
#   GET /api/foods/Masala%20Dosa
# Example response (success):
#   {
#       "name": "Masala Dosa",
#       "calories": 320,
#       "protein": 6.5,
#       "carbs": 42.0,
#       "fat": 12.0,
#       "score": 0.85,
#       "serving_size": "1 piece (approx 150g)",
#       "description": "A crispy rice crepe filled with spiced potato masala, served with coconut chutney and sambar."
#   }
# Example response (failure, food not found):
#   {"error": "Food not found"}
# --------------------------------------------------------------------------------------------------

@router.get("/{food_name}", response_model=FoodDetail)
def get_food(food_name: str):
    # Load the dataset (same as above).
    df = load_data()
    # Filter for the row where 'name' exactly matches the requested food_name.
    # Note: This is case-sensitive. For better user experience, you might want to case-insensitive match.
    food = df[df["name"] == food_name]
    # If the resulting DataFrame is empty, return an error dictionary (but note: response_model=FoodDetail expects a FoodDetail object,
    # so returning {"error": ...} would violate the model. In practice, you'd raise HTTPException. However, the original code does this,
    # so we keep it as is but comment on the potential issue.
    if food.empty:
        return {"error": "Food not found"}   # This does not conform to FoodDetail; better to raise HTTPException(404)
    # Return the first (and only) matching row as a dictionary.
    # FastAPI will try to validate it against FoodDetail; if extra fields exist, they may be ignored or cause error.
    return food.iloc[0].to_dict()