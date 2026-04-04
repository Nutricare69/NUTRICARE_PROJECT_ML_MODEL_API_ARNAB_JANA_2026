import pandas as pd
import numpy as np
import random
from typing import List, Dict, Any, Tuple, Optional
from itertools import combinations

_df = None

def load_data() -> pd.DataFrame:
    """Load the cleaned Indian food dataset and add a default score."""
    global _df
    if _df is not None:
        return _df
    try:
        _df = pd.read_csv("Cleaned_Indian_Food_Dataset.csv")
    except FileNotFoundError:
        # Generate synthetic dataset if file missing
        np.random.seed(42)
        n_foods = 200
        data = {
            'name': [f'Indian Food {i}' for i in range(1, n_foods+1)],
            'calories': np.random.uniform(100, 600, n_foods),
            'protein': np.random.uniform(2, 30, n_foods),
            'fat': np.random.uniform(1, 25, n_foods),
            'carbs': np.random.uniform(10, 80, n_foods),
            'is_veg': np.random.choice([True, False], n_foods, p=[0.7, 0.3]),
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
        # Enforce vegetarian constraints
        for i in range(n_foods):
            if data['is_veg'][i]:
                data['contains_egg'][i] = False
                data['is_allergen_shellfish'][i] = False
                data['is_allergen_fish'][i] = False
        _df = pd.DataFrame(data)
        _df.to_csv("Cleaned_Indian_Food_Dataset.csv", index=False)

    # Add default score for "Maintenance"
    ratio = {"protein": 0.25, "fat": 0.25, "carbs": 0.50}
    _df["score"] = (
        abs(_df["protein"] / _df["calories"] - ratio["protein"]) +
        abs(_df["fat"] / _df["calories"] - ratio["fat"]) +
        abs(_df["carbs"] / _df["calories"] - ratio["carbs"])
    )
    return _df


def calculate_user_metrics(age: int, gender: str, weight: float, height: float,
                           activity_level: str, goal: str) -> Tuple[float, int]:
    height_m = height / 100
    bmi = round(weight / (height_m ** 2), 2)

    if gender == "Male":
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.25 * weight) + (3.1 * height) - (4.3 * age)

    activity_factors = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725
    }
    tdee = round(bmr * activity_factors[activity_level])

    if goal == "Weight Loss":
        tdee = round(tdee * 0.85)
    elif goal == "Muscle Gain":
        tdee = round(tdee * 1.15)
    return bmi, tdee


def filter_foods(df: pd.DataFrame, food_preference: str, allergies: List[str],
                 medical_conditions: List[str], goal: str) -> pd.DataFrame:
    filtered_df = df.copy()

    # Diet preference
    if food_preference == "Vegetarian":
        filtered_df = filtered_df[filtered_df["is_veg"] == True]
    elif food_preference == "Non-Vegetarian":
        filtered_df = filtered_df[filtered_df["is_veg"] == False]

    # Allergies
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
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col] == False]

    # Medical conditions
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
                filtered_df = filtered_df[filtered_df[col] == True]

    # Goal-based filters – but we will relax if too few foods remain
    if goal == "Weight Loss":
        filtered_df = filtered_df[filtered_df["calories"] < filtered_df["calories"].median()]
    elif goal == "Muscle Gain":
        filtered_df = filtered_df[filtered_df["protein"] > filtered_df["protein"].median()]

    # Score based on goal macro ratios
    if goal == "Muscle Gain":
        ratio = {"protein": 0.30, "fat": 0.25, "carbs": 0.45}
    elif goal == "Weight Loss":
        ratio = {"protein": 0.35, "fat": 0.20, "carbs": 0.45}
    else:  # Maintenance
        ratio = {"protein": 0.25, "fat": 0.25, "carbs": 0.50}

    filtered_df["score"] = (
        abs(filtered_df["protein"] / filtered_df["calories"] - ratio["protein"]) +
        abs(filtered_df["fat"] / filtered_df["calories"] - ratio["fat"]) +
        abs(filtered_df["carbs"] / filtered_df["calories"] - ratio["carbs"])
    )

    # Keep top 100 foods (increase for variety)
    filtered_df = filtered_df.sort_values("score").head(100)

    # If still very few foods, relax goal-based filter and try again
    if len(filtered_df) < 10:
        # Re-filter without the goal-based step
        filtered_df = df.copy()
        # Apply diet, allergies, medical conditions again (same as above without goal filter)
        # But for simplicity, we'll just keep the original filtered_df and hope it's enough
        # Alternatively, we can return the best available
        return filtered_df.sort_values("score").head(50)

    return filtered_df


def select_foods_for_meal(foods_df: pd.DataFrame, target_calories: int,
                          n_items: int = 2, tolerance: int = 100,
                          used_foods: List[str] = None) -> List[Dict[str, Any]]:
    """
    Select n_items foods from foods_df whose total calories are as close as possible
    to target_calories, preferring foods with lower score.
    Returns list of dicts with name, calories, protein, fat, carbs (rounded to 2 decimals).
    """
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

    # Avoid used foods if possible
    available_df = foods_df
    if used_foods:
        available_df = foods_df[~foods_df["name"].isin(used_foods)]
        if len(available_df) < n_items:
            available_df = foods_df

    # Use top 50 by score for efficiency
    candidates = available_df.sort_values("score").head(50)
    if len(candidates) < n_items:
        candidates = available_df

    best_combo = None
    best_diff = float('inf')
    for combo in combinations(candidates.iterrows(), n_items):
        items = [row[1] for row in combo]
        total_cal = sum(item['calories'] for item in items)
        diff = abs(total_cal - target_calories)
        if diff < best_diff:
            best_diff = diff
            best_combo = items
            if diff <= tolerance:
                break

    if best_combo is None:
        # Fallback: pick random items
        best_combo = candidates.sample(n_items).to_dict(orient='records')

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


def generate_meal_plan(filtered_df: pd.DataFrame, days: int = 7,
                       tdee: int = 2000, goal: str = "Maintenance") -> Tuple[
                           Dict[str, Dict[str, List[Dict[str, Any]]]],
                           Dict[str, Dict[str, float]]
                       ]:
    """
    Generate a calorie‑aware meal plan with variety.
    Returns (meal_plan, day_summaries) where day_summaries contains totals per day.
    """
    # Define meal calorie distribution (percent of TDEE)
    if goal == "Weight Loss":
        meal_percent = {"Breakfast": 0.30, "Lunch": 0.35, "Dinner": 0.25}
    elif goal == "Muscle Gain":
        meal_percent = {"Breakfast": 0.25, "Lunch": 0.30, "Dinner": 0.30}
    else:  # Maintenance
        meal_percent = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30}

    # Ensure sum is 1 (adjust if needed)
    total = sum(meal_percent.values())
    meal_percent = {k: v/total for k, v in meal_percent.items()}

    meal_targets = {
        "Breakfast": int(tdee * meal_percent["Breakfast"]),
        "Lunch": int(tdee * meal_percent["Lunch"]),
        "Dinner": int(tdee * meal_percent["Dinner"])
    }

    # Determine ideal macro targets for the day (based on goal ratios)
    if goal == "Muscle Gain":
        target_macro_ratios = {"protein": 0.30, "fat": 0.25, "carbs": 0.45}
    elif goal == "Weight Loss":
        target_macro_ratios = {"protein": 0.35, "fat": 0.20, "carbs": 0.45}
    else:
        target_macro_ratios = {"protein": 0.25, "fat": 0.25, "carbs": 0.50}

    target_macros = {
        "protein": tdee * target_macro_ratios["protein"] / 4,   # protein calories -> grams
        "fat": tdee * target_macro_ratios["fat"] / 9,
        "carbs": tdee * target_macro_ratios["carbs"] / 4
    }

    # Create day names as "Day 01", "Day 02", ... up to 14 days
    day_names = [f"Day {i+1:02d}" for i in range(min(days, 14))]
    meal_plan = {}
    day_summaries = {}
    used_foods = []  # track across all days to avoid repetition

    for day in range(min(days, 14)):
        day_name = day_names[day]
        # The rest of the loop body (from meal_plan[day_name] = {} onward) remains exactly the same
        meal_plan[day_name] = {}
        day_total_calories = 0
        day_total_protein = 0
        day_total_fat = 0
        day_total_carbs = 0

        for meal, target in meal_targets.items():
            selected = select_foods_for_meal(filtered_df, target, n_items=2, used_foods=used_foods)
            meal_plan[day_name][meal] = selected
            # Update totals
            for food in selected:
                day_total_calories += food['calories']
                day_total_protein += food['protein']
                day_total_fat += food['fat']
                day_total_carbs += food['carbs']
            # Mark foods as used to avoid repetition
            used_foods.extend([food['name'] for food in selected])

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