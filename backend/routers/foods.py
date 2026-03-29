from fastapi import APIRouter, Query
from typing import List, Optional
from models import FoodItem, FoodDetail
from utils.data import load_data

router = APIRouter(prefix="/api/foods", tags=["Foods"])

@router.get("/", response_model=List[FoodItem])
def list_foods(
    search: Optional[str] = Query(None, description="Search by name"),
    sort_by: Optional[str] = Query("score", regex="^(score|calories|protein|carbs)$"),
    limit: int = Query(50, ge=1, le=200)
):
    df = load_data()
    if search:
        df = df[df["name"].str.contains(search, case=False, na=False)]
    if "score" not in df.columns:
        df["score"] = 0.0
    sort_by = sort_by or "score"
    ascending = sort_by == "score"
    df = df.sort_values(sort_by, ascending=ascending).head(limit)
    return df.to_dict(orient="records")

@router.get("/{food_name}", response_model=FoodDetail)
def get_food(food_name: str):
    df = load_data()
    food = df[df["name"] == food_name]
    if food.empty:
        return {"error": "Food not found"}
    return food.iloc[0].to_dict()