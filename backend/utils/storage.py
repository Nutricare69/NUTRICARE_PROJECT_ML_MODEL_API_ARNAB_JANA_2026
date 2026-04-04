# ==================================================================================================
# MODULE: storage.py
# ==================================================================================================
# PURPOSE: Persistent storage layer for user data using JSON file.
#          Handles user registration, authentication, profile/meal plan history,
#          admin functions, ratings/feedback, subscription management, and system statistics.
# ==================================================================================================
# INTEGRATION IN WEB DEVELOPMENT (BACKEND):
#
# BACKEND (FastAPI):
#   - Place this file in your 'utils' directory.
#   - Import functions in other modules (auth.py, users.py, meal_plan.py, admin.py, feedback.py, analytics.py):
#        from utils.storage import load_users, save_users, register_user, authenticate_user, ...
#   - The file uses a single JSON file 'users.json' in the working directory.
#   - All user data is stored as a dictionary: {username: user_data_dict}
#   - Passwords are hashed using SHA256 (for demo; use bcrypt in production).
#   - The JSON structure includes fields like profile_history, meal_plan_history, ratings, subscription_tier.
#
# FRONTEND (Indirect integration):
#   - Frontend never calls this file directly; it calls API endpoints (auth.py, users.py, etc.)
#     which internally use these storage functions.
#   - Example Indian user flow:
#       1. User "raj_verma" registers via POST /api/auth/register
#       2. storage.py creates entry: users["raj_verma"] = {..., "subscription_tier": "free", ...}
#       3. User generates a meal plan -> storage.py appends to meal_plan_history
#       4. User saves profile -> storage.py appends to profile_history
#       5. Admin upgrades user to premium -> storage.py changes subscription_tier to "premium"
# ==================================================================================================

# --------------------------------------------------------------------------------------------------
# IMPORT SECTION
# --------------------------------------------------------------------------------------------------
# json: Python standard library for reading/writing JSON files.
import json
# hashlib: Provides SHA256 hashing for passwords (simple, not for production; use bcrypt).
import hashlib
# os: Used to check if the user data file exists.
import os
# datetime: Used to generate timestamps for registration, login, profile saves, ratings, etc.
from datetime import datetime
# typing: Type hints for better code readability and IDE support.
from typing import Dict, Any, List, Tuple, Optional

# --------------------------------------------------------------------------------------------------
# CONSTANT: USER_FILE
# --------------------------------------------------------------------------------------------------
# Defines the name of the JSON file that stores all user data.
USER_FILE = "users.json"

# ==================================================================================================
# FUNCTION: hash_password(password: str) -> str
# ==================================================================================================
# Purpose: Hash a plain-text password using SHA256 (insecure for production; use bcrypt/argon2).
# Input: password (string)
# Output: Hexadecimal digest (string)
# Example: hash_password("MyPass123") -> "a6b3c4d5..." (64 chars)
# ==================================================================================================

def hash_password(password: str) -> str:
    # Encode the password string to bytes (UTF-8), then create SHA256 hash, then return hex digest.
    return hashlib.sha256(password.encode()).hexdigest()

# ==================================================================================================
# FUNCTION: load_users() -> Dict[str, Any]
# ==================================================================================================
# Purpose: Load the entire user database from the JSON file.
# Returns: Dictionary mapping username to user data dict. If file doesn't exist or is corrupted, returns {}.
# Example output:
#   {
#       "priya_sharma": { "password": "...", "email": "priya@example.com", ... },
#       "admin": { "password": "...", "user_type": "admin", ... }
#   }
# ==================================================================================================

def load_users() -> Dict[str, Any]:
    # Check if the JSON file exists in the current directory.
    if os.path.exists(USER_FILE):
        try:
            # Open file in read mode, load JSON content into a Python dict.
            with open(USER_FILE, "r") as f:
                return json.load(f)
        except:
            # If any error (e.g., corrupt JSON), return empty dict.
            return {}
    # If file doesn't exist, return empty dict.
    return {}

# ==================================================================================================
# FUNCTION: save_users(users: Dict[str, Any]) -> None
# ==================================================================================================
# Purpose: Write the entire user database to the JSON file with pretty indentation.
# Input: users dictionary (as loaded/modified)
# Output: None (writes to file)
# Example: save_users(users) -> creates/overwrites users.json with formatted JSON.
# ==================================================================================================

def save_users(users: Dict[str, Any]) -> None:
    # Open file in write mode, dump dict as JSON with indent=2 for readability.
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ==================================================================================================
# FUNCTION: register_user(username, password, email, name) -> Tuple[bool, str]
# ==================================================================================================
# Purpose: Create a new regular user account with 'free' subscription tier.
# Inputs:
#   username: unique login name (e.g., "raj_verma")
#   password: plain text (will be hashed)
#   email: must contain '@' and '.'
#   name: full name (e.g., "Raj Verma")
# Returns: (success: bool, message: str)
# Example Indian user:
#   register_user("raj_verma", "Pass@123", "raj.verma@gmail.com", "Raj Verma")
#   -> (True, "Registration successful!")
#   If username exists: (False, "Username already exists!")
# ==================================================================================================

def register_user(username: str, password: str, email: str, name: str) -> Tuple[bool, str]:
    # Load existing users.
    users = load_users()
    # Check for duplicate username.
    if username in users:
        return False, "Username already exists!"
    # Simple email validation (must contain '@' and at least one '.' after '@'? Actually just checks presence of '@' and '.' anywhere)
    if "@" not in email or "." not in email:
        return False, "Invalid email format!"
    
    # Create new user dictionary (fields explained inline).
    users[username] = {
        'password': hash_password(password),                           # Hashed password
        'email': email,                                                # User's email
        'name': name,                                                  # Full name
        'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # Timestamp of registration
        'profile_history': [],                                         # List of profile snapshots (each with timestamp)
        'meal_plan_history': [],                                       # List of generated meal plans (each with timestamp)
        'last_login': None,                                            # Timestamp of last login (initially None)
        'user_type': 'user',                                           # Role: 'user' or 'admin'
        'is_active': True,                                             # Account enabled/disabled by admin
        'login_count': 0,                                              # Number of successful logins
        'subscription_tier': 'free'                                    # 'free' or 'premium' (affects max plan days)
    }
    # Save the updated users dictionary to JSON.
    save_users(users)
    return True, "Registration successful!"

# ==================================================================================================
# FUNCTION: authenticate_user(username, password, is_admin=False) -> Tuple[bool, str]
# ==================================================================================================
# Purpose: Verify user credentials, optionally enforce admin role, update last_login and login_count.
# Inputs:
#   username: login name
#   password: plain text (hashed internally for comparison)
#   is_admin: if True, only admin users can log in
# Returns: (success: bool, message: str)
# Example Indian user login:
#   authenticate_user("raj_verma", "Pass@123", is_admin=False)
#   -> (True, "Login successful!") and updates last_login, increments login_count.
#   If account deactivated: (False, "Account is deactivated. Contact administrator.")
# ==================================================================================================

def authenticate_user(username: str, password: str, is_admin: bool = False) -> Tuple[bool, str]:
    users = load_users()
    # Check if user exists.
    if username not in users:
        return False, "User not found!"
    user = users[username]
    # If admin access required but user is not admin, deny.
    if is_admin and user.get('user_type') != 'admin':
        return False, "Access denied! Admin privileges required."
    # Check if account is active.
    if not user.get('is_active', True):
        return False, "Account is deactivated. Contact administrator."
    # Compare hashed password with stored hash.
    if user['password'] == hash_password(password):
        # Update last login timestamp and increment login count.
        user['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user['login_count'] = user.get('login_count', 0) + 1
        # Save changes to file.
        save_users(users)
        return True, "Login successful!"
    return False, "Incorrect password!"

# ==================================================================================================
# FUNCTION: save_user_profile(username, profile_data) -> bool
# ==================================================================================================
# Purpose: Append a profile snapshot (including BMI, TDEE, timestamp) to user's profile_history.
# Inputs:
#   username: string
#   profile_data: dict containing age, gender, weight, height, activity_level, goal, bmi, tdee
# Returns: True if user exists and saved, False otherwise.
# Example: save_user_profile("raj_verma", {"age":35,"weight":80,"bmi":27.7,"tdee":2200,...})
#   Appends a copy with added 'timestamp' and auto-incremented 'plan_id' (actually profile_id) to profile_history.
#   Keeps only last 10 profiles (slicing [-10:]).
# ==================================================================================================

def save_user_profile(username: str, profile_data: Dict[str, Any]) -> bool:
    users = load_users()
    if username in users:
        # Add a timestamp to this profile snapshot.
        profile_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Assign a sequential ID (starting from 1) based on current history length.
        profile_data['plan_id'] = len(users[username]['profile_history']) + 1
        # Append to profile_history list.
        users[username]['profile_history'].append(profile_data)
        # Keep only the most recent 10 profiles to avoid excessive file size.
        users[username]['profile_history'] = users[username]['profile_history'][-10:]
        save_users(users)
        return True
    return False

# ==================================================================================================
# FUNCTION: save_meal_plan(username, meal_plan_data) -> bool
# ==================================================================================================
# Purpose: Store a generated meal plan in user's meal_plan_history.
# Inputs:
#   username: string
#   meal_plan_data: dict containing plan_data, day_summaries, user_profile, food_count, etc.
# Returns: True if user exists and saved, False otherwise.
# Example: save_meal_plan("raj_verma", {"plan_data": {...}, "day_summaries": {...}, ...})
#   Adds 'timestamp', auto-incremented 'plan_id', and initializes empty 'ratings' dict.
#   Keeps only last 10 meal plans.
# ==================================================================================================

def save_meal_plan(username: str, meal_plan_data: Dict[str, Any]) -> bool:
    users = load_users()
    if username in users:
        # Add creation timestamp.
        meal_plan_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Generate a sequential plan ID.
        meal_plan_data['plan_id'] = len(users[username]['meal_plan_history']) + 1
        # Initialize empty ratings dictionary for storing user feedback per day.
        meal_plan_data['ratings'] = {}
        # Append to history.
        users[username]['meal_plan_history'].append(meal_plan_data)
        # Keep only last 10 plans.
        users[username]['meal_plan_history'] = users[username]['meal_plan_history'][-10:]
        save_users(users)
        return True
    return False

# ==================================================================================================
# FUNCTION: get_user_history(username) -> Tuple[List[Dict], List[Dict]]
# ==================================================================================================
# Purpose: Retrieve both profile_history and meal_plan_history for a user.
# Returns: (profile_history list, meal_plan_history list). Empty lists if user not found.
# Example output: ([{profile1}, {profile2}], [{plan1}, {plan2}])
# ==================================================================================================

def get_user_history(username: str) -> Tuple[List[Dict], List[Dict]]:
    users = load_users()
    if username in users:
        # Use .get() with default empty list to avoid KeyError.
        return users[username].get('profile_history', []), users[username].get('meal_plan_history', [])
    return [], []

# ==================================================================================================
# FUNCTION: get_all_users() -> Dict[str, Any]
# ==================================================================================================
# Purpose: Return the entire users dictionary (for admin endpoints).
# ==================================================================================================

def get_all_users() -> Dict[str, Any]:
    return load_users()

# ==================================================================================================
# FUNCTION: update_user_status(username, is_active) -> bool
# ==================================================================================================
# Purpose: Enable or disable a user account (admin function).
# Inputs: username, is_active (bool)
# Returns: True if user found and updated, False otherwise.
# Example: update_user_status("raj_verma", False) -> deactivates account, preventing login.
# ==================================================================================================

def update_user_status(username: str, is_active: bool) -> bool:
    users = load_users()
    if username in users:
        users[username]['is_active'] = is_active
        save_users(users)
        return True
    return False

# ==================================================================================================
# FUNCTION: delete_user(username) -> Tuple[bool, str]
# ==================================================================================================
# Purpose: Permanently remove a user account (admin only, cannot delete admin accounts).
# Returns: (success, message)
# Example: delete_user("raj_verma") -> (True, "User deleted successfully!")
#   If trying to delete admin: (False, "Cannot delete admin accounts!")
# ==================================================================================================

def delete_user(username: str) -> Tuple[bool, str]:
    users = load_users()
    if username not in users:
        return False, "User not found!"
    # Prevent deletion of any admin account.
    if users[username].get('user_type') == 'admin':
        return False, "Cannot delete admin accounts!"
    del users[username]
    save_users(users)
    return True, "User deleted successfully!"

# ==================================================================================================
# FUNCTION: create_admin_account() -> bool
# ==================================================================================================
# Purpose: Create a default admin account if none exists (run on first start).
# Credentials: username="admin", password="admin123", email="admin@nutricare.com"
# Returns: True if admin was created, False if already existed.
# Example: Call this during app initialization to ensure an admin exists.
# ==================================================================================================

def create_admin_account() -> bool:
    users = load_users()
    admin_username = "admin"
    if admin_username not in users:
        users[admin_username] = {
            'password': hash_password("admin123"),
            'email': "admin@nutricare.com",
            'name': "System Administrator",
            'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'profile_history': [],
            'meal_plan_history': [],
            'last_login': None,
            'user_type': 'admin',
            'is_active': True,
            'login_count': 0,
            'subscription_tier': 'premium'   # Admin gets premium by default.
        }
        save_users(users)
        return True
    return False

# ==================================================================================================
# FUNCTION: get_system_stats() -> Dict[str, int]
# ==================================================================================================
# Purpose: Compute aggregate statistics for admin dashboard.
# Returns: dict with keys: total_users, active_users, admins, total_logins, today_logins,
#          plans_generated, profiles_created.
# Example output:
#   {
#       "total_users": 15,
#       "active_users": 12,
#       "admins": 1,
#       "total_logins": 234,
#       "today_logins": 5,
#       "plans_generated": 42,
#       "profiles_created": 38
#   }
# ==================================================================================================

def get_system_stats() -> Dict[str, int]:
    users = get_all_users()
    # Initialize counters.
    stats = {
        'total_users': len(users),
        'active_users': sum(1 for u in users.values() if u.get('is_active', True)),
        'admins': sum(1 for u in users.values() if u.get('user_type') == 'admin'),
        'total_logins': sum(u.get('login_count', 0) for u in users.values()),
        'today_logins': 0,
        'plans_generated': sum(len(u.get('meal_plan_history', [])) for u in users.values()),
        'profiles_created': sum(len(u.get('profile_history', [])) for u in users.values())
    }
    # Count how many users logged in today (last_login starts with today's date).
    today = datetime.now().strftime("%Y-%m-%d")
    for user in users.values():
        last_login = user.get('last_login')
        if last_login and last_login.startswith(today):
            stats['today_logins'] += 1
    return stats

# ==================================================================================================
# FUNCTION: add_rating_to_meal_plan(username, plan_id, day_name, stars, feedback=None) -> bool
# ==================================================================================================
# Purpose: Store or update a rating (1-5 stars) and optional text feedback for a specific day of a saved meal plan.
# Inputs:
#   username: user who submits rating
#   plan_id: integer ID of the meal plan (as stored in meal_plan_history)
#   day_name: string like "Day 01" or "Monday"
#   stars: integer 1-5
#   feedback: optional string comment
# Returns: True if plan found and rating saved, False otherwise.
# Example Indian user: add_rating_to_meal_plan("priya_sharma", 2, "Day 03", 4, "Aloo paratha was tasty but oily")
#   This adds an entry under plan['ratings']['Day 03'] with timestamp.
# ==================================================================================================

def add_rating_to_meal_plan(username: str, plan_id: int, day_name: str, stars: int, feedback: str = None) -> bool:
    """Add or update a rating for a specific day of a meal plan."""
    users = load_users()
    if username not in users:
        return False

    # Iterate through user's meal plans to find the matching plan_id.
    for plan in users[username].get('meal_plan_history', []):
        if plan.get('plan_id') == plan_id:
            # Ensure ratings dict exists.
            if 'ratings' not in plan:
                plan['ratings'] = {}
            # Store rating data for the given day.
            plan['ratings'][day_name] = {
                'stars': stars,
                'feedback': feedback,
                'rated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_users(users)
            return True
    return False

# ==================================================================================================
# FUNCTION: get_user_feedback(username) -> List[Dict]
# ==================================================================================================
# Purpose: Retrieve all ratings submitted by a specific user across all their meal plans.
# Returns: List of dicts, each containing plan_id, plan_timestamp, day_name, stars, feedback, rated_at.
# Example output for user "priya_sharma":
#   [
#       { "plan_id": 2, "plan_timestamp": "2025-03-20 10:00:00", "day_name": "Day 03",
#         "stars": 4, "feedback": "Aloo paratha was tasty but oily", "rated_at": "2025-03-21 18:30:00" }
#   ]
# ==================================================================================================

def get_user_feedback(username: str) -> List[Dict]:
    """Retrieve all ratings across all meal plans of a user."""
    users = load_users()
    if username not in users:
        return []

    feedback_list = []
    for plan in users[username].get('meal_plan_history', []):
        # Check if plan has ratings.
        if 'ratings' in plan and plan['ratings']:
            for day, rating_data in plan['ratings'].items():
                feedback_list.append({
                    'plan_id': plan['plan_id'],
                    'plan_timestamp': plan.get('timestamp'),
                    'day_name': day,
                    'stars': rating_data.get('stars'),
                    'feedback': rating_data.get('feedback'),
                    'rated_at': rating_data.get('rated_at')
                })
    return feedback_list

# ==================================================================================================
# FUNCTION: get_all_users_feedback() -> List[Dict]
# ==================================================================================================
# Purpose: Admin function to collect all ratings from every user, including usernames and names.
# Returns: List of dicts with additional fields 'username' and 'user_name'.
# Example output:
#   [
#       { "username": "priya_sharma", "user_name": "Priya Sharma", "plan_id": 2, "day_name": "Day 03",
#         "stars": 4, "feedback": "...", "rated_at": "..." },
#       ...
#   ]
# ==================================================================================================

def get_all_users_feedback() -> List[Dict]:
    """Admin function: get all ratings from all users."""
    users = load_users()
    all_feedback = []
    for username, user_data in users.items():
        for plan in user_data.get('meal_plan_history', []):
            if 'ratings' in plan and plan['ratings']:
                for day, rating_data in plan['ratings'].items():
                    all_feedback.append({
                        'username': username,
                        'user_name': user_data.get('name'),
                        'plan_id': plan['plan_id'],
                        'plan_timestamp': plan.get('timestamp'),
                        'day_name': day,
                        'stars': rating_data.get('stars'),
                        'feedback': rating_data.get('feedback'),
                        'rated_at': rating_data.get('rated_at')
                    })
    return all_feedback

# ==================================================================================================
# FUNCTION: upgrade_user_to_premium(username) -> bool
# ==================================================================================================
# Purpose: Change a user's subscription tier from 'free' to 'premium' (admin action).
# Returns: True if user exists and upgraded, False otherwise.
# Example: upgrade_user_to_premium("raj_verma") -> sets subscription_tier to 'premium'.
#   This allows the user to generate meal plans up to 14 days instead of 7.
# ==================================================================================================

def upgrade_user_to_premium(username: str) -> bool:
    """Upgrade a user's subscription to premium."""
    users = load_users()
    if username not in users:
        return False
    users[username]['subscription_tier'] = 'premium'
    save_users(users)
    return True

# ==================================================================================================
# FUNCTION: get_user_subscription(username) -> str
# ==================================================================================================
# Purpose: Return subscription tier ('free' or 'premium') for a user. Defaults to 'free'.
# Example: get_user_subscription("raj_verma") -> "free" or "premium"
# ==================================================================================================

def get_user_subscription(username: str) -> str:
    """Return subscription tier ('free' or 'premium') for a user."""
    users = load_users()
    user = users.get(username)
    if user:
        return user.get('subscription_tier', 'free')
    return 'free'