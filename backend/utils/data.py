import pandas as pd
import numpy as np
import random
from typing import List, Dict, Any, Tuple

# Cache the dataset in memory
_df = None

def load_data() -> pd.DataFrame:
    """Load the cleaned Indian food dataset (cached)."""
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
    return _df


def calculate_user_metrics(age: int, gender: str, weight: float, height: float,
                           activity_level: str, goal: str) -> Tuple[float, int]:
    """Calculate BMI and TDEE."""
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
    """Filter and score foods based on user inputs."""
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

    # Goal-based filters
    if goal == "Weight Loss":
        filtered_df = filtered_df[filtered_df["calories"] < filtered_df["calories"].median()]
    elif goal == "Muscle Gain":
        filtered_df = filtered_df[filtered_df["protein"] > filtered_df["protein"].median()]

    # Score based on ideal macro ratios
    if goal == "Muscle Gain":
        ratio = {"protein": 0.30, "fat": 0.25, "carbs": 0.45}
    elif goal == "Weight Loss":
        ratio = {"protein": 0.35, "fat": 0.20, "carbs": 0.45}
    else:  # Maintenance
        ratio = {"protein": 0.25, "fat": 0.25, "carbs": 0.50}

    if not filtered_df.empty:
        filtered_df["score"] = (
            abs(filtered_df["protein"] / filtered_df["calories"] - ratio["protein"]) +
            abs(filtered_df["fat"] / filtered_df["calories"] - ratio["fat"]) +
            abs(filtered_df["carbs"] / filtered_df["calories"] - ratio["carbs"])
        )
        filtered_df = filtered_df.sort_values("score").head(50)
    else:
        filtered_df = df.head(10)

    return filtered_df


def generate_meal_plan(filtered_df: pd.DataFrame, days: int = 7) -> Dict[str, Dict[str, List[str]]]:
    """Generate a meal plan for the given number of days."""
    if len(filtered_df) < 21:
        return {}
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    meal_plan = {}
    for day in range(min(days, 7)):
        day_name = day_names[day]
        meal_plan[day_name] = {
            "Breakfast": random.sample(list(filtered_df["name"].head(30)), 2),
            "Lunch": random.sample(list(filtered_df["name"].head(30)), 2),
            "Dinner": random.sample(list(filtered_df["name"].head(30)), 2)
        }
    return meal_plan