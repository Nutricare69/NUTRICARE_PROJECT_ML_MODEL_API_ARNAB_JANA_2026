# ------------------------------------------------------------------------------
# IMPORT SECTION: Import required modules for the food image analysis API router
# ------------------------------------------------------------------------------

# Import APIRouter to create a route group for analysis endpoints, UploadFile for handling file uploads,
# File for declaring file parameters, and HTTPException for error responses.
# These are core FastAPI components. In a web development project, install FastAPI and uvicorn,
# then import these classes as shown. FastAPI automatically handles multipart/form-data file uploads.
from fastapi import APIRouter, UploadFile, File, HTTPException

# Import the Pydantic model 'ImageAnalysisResponse' from the local 'models' module.
# This model defines the shape of the JSON response (estimated calories, protein, carbs, fat, food name).
# Ensure 'models.py' exists in the same directory or Python path and contains the class definition.
from models import ImageAnalysisResponse

# Import Python's built-in 'random' module to generate mock analysis values.
# In a real web app, you would replace this with a machine learning model or external API call.
# No additional installation is needed for 'random' as it's part of the standard library.
import random

# ------------------------------------------------------------------------------
# ROUTER INITIALIZATION: Create an APIRouter instance for food analysis endpoints
# ------------------------------------------------------------------------------

# Create a router object that groups all analysis endpoints under '/api/analysis' URL prefix.
# The 'tags' parameter groups these endpoints under "Analysis" in the automatic API documentation (Swagger UI).
# This router can later be included in the main FastAPI app using app.include_router(analysis_router).
router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

# ------------------------------------------------------------------------------
# ENDPOINT: POST /api/analysis/food-image - Analyze an uploaded food image and return estimated nutrition
# ------------------------------------------------------------------------------

# Define a POST endpoint at '/food-image' (full path '/api/analysis/food-image') that accepts a file upload.
# The 'response_model' parameter specifies that the response must match the ImageAnalysisResponse schema.
@router.post("/food-image", response_model=ImageAnalysisResponse)
# The function is declared as 'async' to support asynchronous processing (e.g., waiting for external APIs).
# 'file' is a required parameter of type UploadFile, with default value File(...).
# The '...' (ellipsis) indicates that this field is required; FastAPI will expect a file part named 'file' in the request.
async def analyze_food_image(file: UploadFile = File(...)):
    # Check the content type (MIME type) of the uploaded file.
    # Only JPEG, PNG, and WebP images are accepted for analysis.
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        # If the file format is invalid, raise an HTTP 400 (Bad Request) exception with a detail message.
        # FastAPI will automatically convert this exception into a JSON error response.
        raise HTTPException(status_code=400, detail="Invalid image format")
    
    # Return a response object conforming to the ImageAnalysisResponse model.
    # In this mock implementation, we generate random values for the nutritional estimates.
    # In a real application, you would:
    #   1. Read the file contents: contents = await file.read()
    #   2. Pass the image bytes to a computer vision model or external API (e.g., Google Vision, NutriAPI)
    #   3. Parse the results and compute estimates.
    #   4. Return structured data as shown below.
    return ImageAnalysisResponse(
        estimated_calories=random.randint(100, 500),      # Random integer between 100 and 500 kcal
        estimated_protein=round(random.uniform(5, 30), 1), # Random float between 5 and 30, rounded to 1 decimal
        estimated_carbs=round(random.uniform(10, 60), 1),  # Random float between 10 and 60, rounded to 1 decimal
        estimated_fat=round(random.uniform(2, 20), 1),     # Random float between 2 and 20, rounded to 1 decimal
        food_name="Samosa"                                 # Hardcoded food name (mock)
    )