# ==================================================================================================
# MODULE: data.py
# ==================================================================================================
# PURPOSE: Core data processing and meal plan generation logic.
#          - Load and preprocess Indian food dataset (real or synthetic)
#          - Calculate user metrics (BMI, TDEE)
#          - Filter foods based on preferences, allergies, medical conditions, and goal
#          - Generate personalized meal plans with day summaries
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND ONLY):
#
# 
# BACKEND (FastAPI):
#   - Place this file in your 'utils' directory.
#   - Import functions in other modules (e.g., meal_plan.py, users.py) like:
#        from utils.data import load_data, calculate_user_metrics, filter_foods, generate_meal_plan
#   - The file expects a CSV file 'Cleaned_Indian_Food_Dataset.csv' in the working directory.
#     If not found, it generates a synthetic dataset with realistic Indian food constraints.
#   - All functions are synchronous (no async) and work with pandas DataFrames.
#
# EXAMPLE INDIAN FOOD DATASET (after cleaning):
#   name               | calories | protein | fat | carbs | is_veg | suitable_diabetes | ...
#   -------------------|----------|---------|-----|-------|--------|-------------------|----
#   "Masala Dosa"      | 320      | 6.5     | 12  | 42    | True   | True              |
#   "Chole Bhature"    | 550      | 15      | 22  | 70    | True   | False             |
#   "Tandoori Chicken" | 480      | 40      | 25  | 10    | False  | True              |
#   "Idli Sambar"      | 150      | 5       | 2   | 30    | True   | True              |
#
# EXAMPLE USER METRICS (Indian user):
#   Input: age=32, gender="Female", weight=65kg, height=160cm,
#          activity_level="Moderately Active", goal="Weight Loss"
#   Output: BMI = 65 / (1.60^2) = 25.4, TDEE = ~2100 * 0.85 = 1785 kcal/day
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# pandas (pd): powerful data manipulation library. Install with: pip install pandas
# Used to load CSV, filter rows, sort, sample, and convert to dictionaries.
import pandas as pd
# numpy (np): numerical computing library, used here for random number generation in synthetic data.
import numpy as np
# random: Python standard library for random choices (used in fallback selection).
import random
# typing imports: provide type hints for function signatures (improves code readability and IDE support).
from typing import List, Dict, Any, Tuple, Optional
# itertools.combinations: generates all possible combinations of foods for a meal (used in select_foods_for_meal).
from itertools import combinations

# --------------------------------------------------------------------------------------------------
# GLOBAL VARIABLE: _df
# --------------------------------------------------------------------------------------------------
# This variable caches the loaded DataFrame so that subsequent calls to load_data() don't re-read the CSV.
# Initially None, gets assigned after first load.
_df = None

# ==================================================================================================
# FUNCTION: load_data() -> pd.DataFrame
# ==================================================================================================
# Purpose: Load the Indian food dataset from CSV or generate synthetic data if file missing.
#          Adds a default "score" column based on macro ratio for "Maintenance" goal.
# Returns: pandas DataFrame containing food items with nutritional and suitability columns.
# Example usage:
#   df = load_data()
#   print(df.head())
# ==================================================================================================

def load_data() -> pd.DataFrame:
    """Load the cleaned Indian food dataset and add a default score."""
    # Declare that we are using the global _df variable (to modify it).
    global _df
    # If already loaded, return cached version to avoid repeated I/O.
    if _df is not None:
        return _df
    try:
        # Attempt to read the real CSV file (expected to be in the same directory).
        _df = pd.read_csv("Cleaned_Indian_Food_Dataset.csv")
    except FileNotFoundError:
        # If CSV not found, generate a synthetic dataset for development/demo.
        # Set random seed for reproducible results.
        np.random.seed(42)
        n_foods = 200  # Number of synthetic food items to create.
        # Initialize dictionary with empty lists for each column.
        data = {
            'name': [f'Indian Food {i}' for i in range(1, n_foods+1)],
            'calories': np.random.uniform(100, 600, n_foods),      # kcal per serving
            'protein': np.random.uniform(2, 30, n_foods),          # grams
            'fat': np.random.uniform(1, 25, n_foods),              # grams
            'carbs': np.random.uniform(10, 80, n_foods),           # grams
            'is_veg': np.random.choice([True, False], n_foods, p=[0.7, 0.3]),   # 70% vegetarian
            'contains_egg': np.random.choice([True, False], n_foods, p=[0.3, 0.7]),
            'is_allergen_gluten': np.random.choice([True, False], n_foods, p=[0.2, 0.8]),
            'is_allergen_dairy': np.random.choice([True, False], n_foods, p=[0.3, 0.7]),
            'is_allergen_nuts': np.random.choice([True, False], n_foods, p=[0.2, 0.8]),
            'is_allergen_soy': np.random.choice([True, False], n_foods, p=[0.1, 0.9]),
            'is_allergen_shellfish': np.random.choice([True, False], n_foods, p=[0.1, 0.9]),
            'is_allergen_eggs': np.random.choice([True, False], n_foods, p=[0.2, 0.8]),
            'is_allergen_fish': np.random.choice([True, False], n_foods, p=[0.15, 0.85]),
            'suitable_diabetes': np.random.choice([True, False], n_foods, p=[0.6, 0.4]),
            'suitable_hypertension': np.random.choice([True, False], n_foods, p=[0.7, 0.3]),
            'suitable_heart_disease': np.random.choice([True, False], n_foods, p=[0.65, 0.35]),
            'suitable_thyroid': np.random.choice([True, False], n_foods, p=[0.8, 0.2]),
            'suitable_pcos': np.random.choice([True, False], n_foods, p=[0.7, 0.3]),
            'suitable_kidney_disease': np.random.choice([True, False], n_foods, p=[0.5, 0.5]),
            'suitable_gerd': np.random.choice([True, False], n_foods, p=[0.6, 0.4]),
        }
        # Enforce vegetarian constraints: if a food is veg, it cannot contain egg, shellfish, or fish.
        for i in range(n_foods):
            if data['is_veg'][i]:
                data['contains_egg'][i] = False
                data['is_allergen_shellfish'][i] = False
                data['is_allergen_fish'][i] = False
        # Convert dictionary to DataFrame.
        _df = pd.DataFrame(data)
        # Save the synthetic dataset to CSV for future runs (so next time it will load from file).
        _df.to_csv("Cleaned_Indian_Food_Dataset.csv", index=False)

    # Add default "score" column for "Maintenance" goal.
    # The score measures how close a food's macro distribution is to the ideal ratio.
    # Lower score = better (closer to target).
    ratio = {"protein": 0.25, "fat": 0.25, "carbs": 0.50}
    # For each food, compute absolute differences between actual macro/calorie ratio and target.
    # protein/calories gives the fraction of calories from protein.
    _df["score"] = (
        abs(_df["protein"] / _df["calories"] - ratio["protein"]) +
        abs(_df["fat"] / _df["calories"] - ratio["fat"]) +
        abs(_df["carbs"] / _df["calories"] - ratio["carbs"])
    )
    return _df

# ==================================================================================================
# FUNCTION: calculate_user_metrics(age, gender, weight, height, activity_level, goal)
# ==================================================================================================
# Purpose: Compute BMI and TDEE based on user inputs.
# Returns: Tuple (bmi: float, tdee: int)
# Example Indian user:
#   age=35, gender="Male", weight=80kg, height=170cm,
#   activity_level="Moderately Active", goal="Weight Loss"
#   Returns: (27.7, 2229) because 2623 * 0.85 = 2229
# ==================================================================================================

def calculate_user_metrics(age: int, gender: str, weight: float, height: float,
                           activity_level: str, goal: str) -> Tuple[float, int]:
    # Convert height from centimeters to meters.
    height_m = height / 100
    # BMI = weight (kg) / (height in meters)^2. Round to 2 decimals.
    bmi = round(weight / (height_m ** 2), 2)

    # BMR (Basal Metabolic Rate) using Mifflin-St Jeor equation.
    if gender == "Male":
        # Formula for males: 88.36 + (13.4 * weight in kg) + (4.8 * height in cm) - (5.7 * age in years)
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        # Formula for females: 447.6 + (9.25 * weight) + (3.1 * height) - (4.3 * age)
        bmr = 447.6 + (9.25 * weight) + (3.1 * height) - (4.3 * age)

    # Activity multipliers (standard values).
    activity_factors = {
        "Sedentary": 1.2,          # Little or no exercise
        "Lightly Active": 1.375,   # Light exercise 1-3 days/week
        "Moderately Active": 1.55, # Moderate exercise 3-5 days/week
        "Very Active": 1.725       # Hard exercise 6-7 days/week
    }
    # TDEE = BMR * activity factor, rounded to nearest integer.
    tdee = round(bmr * activity_factors[activity_level])

    # Adjust TDEE based on goal:
    if goal == "Weight Loss":
        tdee = round(tdee * 0.85)      # 15% calorie deficit
    elif goal == "Muscle Gain":
        tdee = round(tdee * 1.15)      # 15% calorie surplus
    # For "Maintenance", no adjustment.
    return bmi, tdee

# ==================================================================================================
# FUNCTION: filter_foods(df, food_preference, allergies, medical_conditions, goal)
# ==================================================================================================
# Purpose: Apply dietary filters, allergy exclusions, medical suitability, and goal-based constraints.
# Returns: Filtered DataFrame with a recalculated "score" based on the goal's ideal macro ratios.
# Example Indian input:
#   food_preference = "Vegetarian"
#   allergies = ["Dairy", "Gluten"]
#   medical_conditions = ["Diabetes"]
#   goal = "Weight Loss"
# ==================================================================================================

def filter_foods(df: pd.DataFrame, food_preference: str, allergies: List[str],
                 medical_conditions: List[str], goal: str) -> pd.DataFrame:
    # Work on a copy to avoid mutating the original DataFrame.
    filtered_df = df.copy()

    # ----- Diet preference filtering -----
    if food_preference == "Vegetarian":
        # Keep only rows where is_veg is True.
        filtered_df = filtered_df[filtered_df["is_veg"] == True]
    elif food_preference == "Non-Vegetarian":
        # Keep only non-vegetarian foods (is_veg == False)
        filtered_df = filtered_df[filtered_df["is_veg"] == False]

    # ----- Allergy filtering (exclude foods containing allergens) -----
    allergy_mapping = {
        "Gluten": "is_allergen_gluten",
        "Dairy": "is_allergen_dairy",
        "Nuts": "is_allergen_nuts",
        "Soy": "is_allergen_soy",
        "Shellfish": "is_allergen_shellfish",
        "Eggs": "is_allergen_eggs",
        "Fish": "is_allergen_fish"
    }
    for allergy in allergies:
        if allergy in allergy_mapping:
            col = allergy_mapping[allergy]
            # If the column exists, keep only foods where the allergen is False (i.e., safe).
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col] == False]

    # ----- Medical condition filtering (keep only suitable foods) -----
    medical_mapping = {
        "Diabetes": "suitable_diabetes",
        "Hypertension": "suitable_hypertension",
        "Heart Disease": "suitable_heart_disease",
        "Thyroid Issues": "suitable_thyroid",
        "PCOS": "suitable_pcos",
        "Kidney Disease": "suitable_kidney_disease",
        "GERD/Acid Reflux": "suitable_gerd"
    }
    for condition in medical_conditions:
        if condition in medical_mapping:
            col = medical_mapping[condition]
            if col in filtered_df.columns:
                # For medical conditions, we want foods that are suitable (True).
                filtered_df = filtered_df[filtered_df[col] == True]

    # ----- Goal-based filters (preliminary) -----
    # These are applied to reduce the search space, but if they eliminate too many foods,
    # we will relax later.
    if goal == "Weight Loss":
        # Keep foods with calories below the median (i.e., lower calorie options).
        filtered_df = filtered_df[filtered_df["calories"] < filtered_df["calories"].median()]
    elif goal == "Muscle Gain":
        # Keep foods with protein above the median.
        filtered_df = filtered_df[filtered_df["protein"] > filtered_df["protein"].median()]

    # ----- Recalculate score based on goal-specific macro ratios -----
    if goal == "Muscle Gain":
        # Ideal macro distribution for muscle gain: higher protein, moderate carbs.
        ratio = {"protein": 0.30, "fat": 0.25, "carbs": 0.45}
    elif goal == "Weight Loss":
        # For weight loss: higher protein (to preserve muscle), lower fat.
        ratio = {"protein": 0.35, "fat": 0.20, "carbs": 0.45}
    else:  # Maintenance
        ratio = {"protein": 0.25, "fat": 0.25, "carbs": 0.50}

    # Compute score as sum of absolute differences from target ratios.
    filtered_df["score"] = (
        abs(filtered_df["protein"] / filtered_df["calories"] - ratio["protein"]) +
        abs(filtered_df["fat"] / filtered_df["calories"] - ratio["fat"]) +
        abs(filtered_df["carbs"] / filtered_df["calories"] - ratio["carbs"])
    )

    # Keep only the top 100 foods with the lowest scores (best matches).
    filtered_df = filtered_df.sort_values("score").head(100)

    # If after all filters we have fewer than 10 foods, relax the goal-based filter.
    if len(filtered_df) < 10:
        # Re-filter from original df without the goal-based calorie/protein filter.
        filtered_df = df.copy()
        # Re-apply diet, allergy, and medical filters (same as before, but skip goal-based step).
        if food_preference == "Vegetarian":
            filtered_df = filtered_df[filtered_df["is_veg"] == True]
        elif food_preference == "Non-Vegetarian":
            filtered_df = filtered_df[filtered_df["is_veg"] == False]
        for allergy in allergies:
            if allergy in allergy_mapping:
                col = allergy_mapping[allergy]
                if col in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[col] == False]
        for condition in medical_conditions:
            if condition in medical_mapping:
                col = medical_mapping[condition]
                if col in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[col] == True]
        # Recompute score with goal ratio (without pre-filtering).
        filtered_df["score"] = (
            abs(filtered_df["protein"] / filtered_df["calories"] - ratio["protein"]) +
            abs(filtered_df["fat"] / filtered_df["calories"] - ratio["fat"]) +
            abs(filtered_df["carbs"] / filtered_df["calories"] - ratio["carbs"])
        )
        # Return top 50 best matches.
        return filtered_df.sort_values("score").head(50)

    return filtered_df

# ==================================================================================================
# FUNCTION: select_foods_for_meal(foods_df, target_calories, n_items=2, tolerance=100, used_foods=None)
# ==================================================================================================
# Purpose: Choose n_items foods whose total calories are as close as possible to target_calories.
#          Prefers foods with lower score (better macro match) and avoids recently used foods.
# Returns: List of dicts with name, calories, protein, fat, carbs (each rounded to 2 decimals).
# Example: target_calories = 500, n_items=2 -> could return [{"name":"Idli","calories":150,...}, {"name":"Sambar","calories":350,...}]
# ==================================================================================================

def select_foods_for_meal(foods_df: pd.DataFrame, target_calories: int,
                          n_items: int = 2, tolerance: int = 100,
                          used_foods: List[str] = None) -> List[Dict[str, Any]]:
    """
    Select n_items foods from foods_df whose total calories are as close as possible
    to target_calories, preferring foods with lower score.
    Returns list of dicts with name, calories, protein, fat, carbs (rounded to 2 decimals).
    """
    # If not enough foods available, just return all (fallback).
    if len(foods_df) < n_items:
        # fallback: just return the available foods
        return [
            {
                "name": row['name'],
                "calories": round(row['calories'], 2),
                "protein": round(row['protein'], 2),
                "fat": round(row['fat'], 2),
                "carbs": round(row['carbs'], 2)
            }
            for _, row in foods_df.iterrows()
        ]

    # Avoid used foods if possible to increase variety.
    available_df = foods_df
    if used_foods:
        # Exclude foods whose names are in the used_foods list.
        available_df = foods_df[~foods_df["name"].isin(used_foods)]
        # If after exclusion we have too few, revert to full list.
        if len(available_df) < n_items:
            available_df = foods_df

    # For efficiency, consider only top 50 best-scoring foods.
    candidates = available_df.sort_values("score").head(50)
    if len(candidates) < n_items:
        candidates = available_df

    # Iterate over all combinations of n_items foods to find the one with total calories closest to target.
    best_combo = None
    best_diff = float('inf')   # Initialize with infinity.
    # combinations(candidates.iterrows(), n_items) yields tuples of (index, row) pairs.
    for combo in combinations(candidates.iterrows(), n_items):
        # Extract the actual row (Series) from each tuple.
        items = [row[1] for row in combo]
        total_cal = sum(item['calories'] for item in items)
        diff = abs(total_cal - target_calories)
        if diff < best_diff:
            best_diff = diff
            best_combo = items
            # If difference is within tolerance, stop searching (good enough).
            if diff <= tolerance:
                break

    # If no combination found (should not happen), pick random items as fallback.
    if best_combo is None:
        # Fallback: pick random items
        best_combo = candidates.sample(n_items).to_dict(orient='records')

    # Return the selected foods as a list of dictionaries with rounded nutrition values.
    return [
        {
            "name": item['name'],
            "calories": round(item['calories'], 2),
            "protein": round(item['protein'], 2),
            "fat": round(item['fat'], 2),
            "carbs": round(item['carbs'], 2)
        }
        for item in best_combo
    ]

# ==================================================================================================
# FUNCTION: generate_meal_plan(filtered_df, days=7, tdee=2000, goal="Maintenance")
# ==================================================================================================
# Purpose: Generate a multi-day meal plan with breakfast, lunch, dinner for each day.
#          Distributes TDEE across meals, selects foods using select_foods_for_meal,
#          and computes daily summaries (actual vs target macros).
# Returns: Tuple (meal_plan, day_summaries)
#   - meal_plan: dict like {"Day 01": {"Breakfast": [...], "Lunch": [...], "Dinner": [...]}, ...}
#   - day_summaries: dict like {"Day 01": {"total_calories": 1850, "target_calories": 2000, ...}}
# Example Indian user: tdee=2000, goal="Weight Loss" -> meal targets: Breakfast 30% (600), Lunch 35% (700), Dinner 25% (500)
# ==================================================================================================

def generate_meal_plan(filtered_df: pd.DataFrame, days: int = 7,
                       tdee: int = 2000, goal: str = "Maintenance") -> Tuple[
                           Dict[str, Dict[str, List[Dict[str, Any]]]],
                           Dict[str, Dict[str, float]]
                       ]:
    """
    Generate a calorie‑aware meal plan with variety.
    Returns (meal_plan, day_summaries) where day_summaries contains totals per day.
    """
    # ----- Define meal calorie distribution (as percentage of TDEE) based on goal -----
    if goal == "Weight Loss":
        # Slightly larger breakfast to control hunger, smaller dinner.
        meal_percent = {"Breakfast": 0.30, "Lunch": 0.35, "Dinner": 0.25}
    elif goal == "Muscle Gain":
        # More balanced, with extra at lunch and dinner to support recovery.
        meal_percent = {"Breakfast": 0.25, "Lunch": 0.30, "Dinner": 0.30}
    else:  # Maintenance
        meal_percent = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30}

    # Normalize to ensure sum is exactly 1 (in case of rounding).
    total = sum(meal_percent.values())
    meal_percent = {k: v/total for k, v in meal_percent.items()}

    # Convert percentages to integer calorie targets per meal.
    meal_targets = {
        "Breakfast": int(tdee * meal_percent["Breakfast"]),
        "Lunch": int(tdee * meal_percent["Lunch"]),
        "Dinner": int(tdee * meal_percent["Dinner"])
    }

    # Determine ideal macro targets for the entire day (based on goal ratios).
    if goal == "Muscle Gain":
        target_macro_ratios = {"protein": 0.30, "fat": 0.25, "carbs": 0.45}
    elif goal == "Weight Loss":
        target_macro_ratios = {"protein": 0.35, "fat": 0.20, "carbs": 0.45}
    else:
        target_macro_ratios = {"protein": 0.25, "fat": 0.25, "carbs": 0.50}

    # Convert calorie percentages to grams:
    # protein: 4 cal/g, fat: 9 cal/g, carbs: 4 cal/g
    target_macros = {
        "protein": tdee * target_macro_ratios["protein"] / 4,
        "fat": tdee * target_macro_ratios["fat"] / 9,
        "carbs": tdee * target_macro_ratios["carbs"] / 4
    }

    # Create day names as "Day 01", "Day 02", ... up to max 14 days (or requested days).
    day_names = [f"Day {i+1:02d}" for i in range(min(days, 14))]
    meal_plan = {}
    day_summaries = {}
    used_foods = []  # Track food names used across all days to avoid repetition.

    # Loop over each day.
    for day in range(min(days, 14)):
        day_name = day_names[day]
        meal_plan[day_name] = {}
        day_total_calories = 0
        day_total_protein = 0
        day_total_fat = 0
        day_total_carbs = 0

        # For each meal (Breakfast, Lunch, Dinner) in this day.
        for meal, target in meal_targets.items():
            # Select 2 foods for this meal (e.g., 2 dishes per meal).
            selected = select_foods_for_meal(filtered_df, target, n_items=2, used_foods=used_foods)
            meal_plan[day_name][meal] = selected
            # Accumulate daily totals.
            for food in selected:
                day_total_calories += food['calories']
                day_total_protein += food['protein']
                day_total_fat += food['fat']
                day_total_carbs += food['carbs']
            # Mark these foods as used to avoid same food appearing too often.
            used_foods.extend([food['name'] for food in selected])

        # Store day summary with actual totals and target values.
        day_summaries[day_name] = {
            "total_calories": round(day_total_calories, 2),
            "total_protein": round(day_total_protein, 2),
            "total_fat": round(day_total_fat, 2),
            "total_carbs": round(day_total_carbs, 2),
            "target_calories": tdee,
            "target_protein": round(target_macros["protein"], 2),
            "target_fat": round(target_macros["fat"], 2),
            "target_carbs": round(target_macros["carbs"], 2)
        }

    return meal_plan, day_summaries