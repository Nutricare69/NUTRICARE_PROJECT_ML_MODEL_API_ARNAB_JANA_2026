from fastapi import APIRouter, UploadFile, File, HTTPException
from models import ImageAnalysisResponse
import random

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

@router.post("/food-image", response_model=ImageAnalysisResponse)
async def analyze_food_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")
    return ImageAnalysisResponse(
        estimated_calories=random.randint(100, 500),
        estimated_protein=round(random.uniform(5, 30), 1),
        estimated_carbs=round(random.uniform(10, 60), 1),
        estimated_fat=round(random.uniform(2, 20), 1),
        food_name="Samosa"
    )