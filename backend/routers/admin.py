# ------------------------------------------------------------------------------
# IMPORT SECTION: Import required modules and functions for the admin API router
# ------------------------------------------------------------------------------


# Import APIRouter to create a route group, Depends for dependency injection, HTTPException for error responses.
# These are core FastAPI components. In a web dev project, install fastapi and import as shown.
from fastapi import APIRouter, Depends, HTTPException

# Import List and Dict from typing for type hints (Python standard library, no installation needed).
# Type hints improve code readability and enable IDE autocompletion.
from typing import List, Dict

# Import Pydantic models (UserInfo, SystemStats, UserRegister) from local module 'models'.
# These define the shape of request/response data. Ensure 'models.py' exists in the same directory or Python path.
from models import UserInfo, SystemStats, UserRegister

# Import storage utility functions from 'utils.storage' module.
# In a web project, organize utilities in a 'utils' package. Use relative or absolute imports based on project structure.
from utils.storage import (
    get_all_users,      # Retrieves all user records
    update_user_status, # Toggles user active/inactive status
    delete_user,        # Removes a user account
    register_user,      # (unused here) registers a new standard user
    get_system_stats,   # Returns platform statistics (user count, etc.)
    load_users,         # Reads user data from JSON file
    save_users,         # Writes user data back to JSON file
    hash_password       # Securely hashes a plain text password
)

# Import the admin authentication dependency from 'dependencies' module.
# This function ensures the requesting user is logged in as an admin.
# In FastAPI, dependencies are callables that return values (here a dict of admin info).
from dependencies import get_current_admin

# Import datetime from Python's standard library to handle timestamps for registration dates.
from datetime import datetime

# ------------------------------------------------------------------------------
# ROUTER INITIALIZATION: Create an APIRouter instance with a prefix and tag for OpenAPI docs
# ------------------------------------------------------------------------------

# Create a router object that groups all admin endpoints under '/api/admin' URL prefix.
# The 'tags' parameter groups these endpoints under "Admin" in the automatic API documentation (Swagger UI).
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ------------------------------------------------------------------------------
# ENDPOINT: GET /api/admin/stats - Retrieve system-wide statistics (only accessible by admin)
# ------------------------------------------------------------------------------

# Define a GET endpoint at '/stats' (full path '/api/admin/stats') that returns a SystemStats model.
@router.get("/stats", response_model=SystemStats)
# The 'stats' function receives the admin dependency (the underscore '_' means we ignore the returned value but still enforce auth).
# Depends(get_current_admin) runs the dependency to verify admin privileges before executing this function.
def stats(_: Dict = Depends(get_current_admin)):
    # Call get_system_stats() from storage to fetch statistics (total users, active users, etc.)
    # The result is automatically serialized to JSON matching SystemStats schema.
    return get_system_stats()

# ------------------------------------------------------------------------------
# ENDPOINT: GET /api/admin/users - List all registered users with detailed info (admin only)
# ------------------------------------------------------------------------------

# Define a GET endpoint at '/users' that returns a list of UserInfo objects.
@router.get("/users", response_model=List[UserInfo])
# The 'list_users' function enforces admin authentication via dependency injection.
def list_users(_: Dict = Depends(get_current_admin)):
    # Retrieve a dictionary where keys are usernames and values are user data dicts.
    users = get_all_users()
    # Initialize an empty list to accumulate UserInfo instances.
    result = []
    # Iterate over each key-value pair in the users dictionary.
    for username, data in users.items():
        # Append a new UserInfo object constructed from the raw data.
        # .get() provides default values if a key is missing (defensive programming).
        result.append(UserInfo(
            username=username,                           # Unique login name
            name=data.get('name', 'N/A'),               # Full name, fallback 'N/A'
            email=data.get('email', 'N/A'),             # Email address, fallback 'N/A'
            user_type=data.get('user_type', 'user'),    # 'admin' or 'user', default 'user'
            is_active=data.get('is_active', True),      # Account active status, default True
            registration_date=data.get('registration_date', ''),  # Timestamp of account creation
            last_login=data.get('last_login'),          # Last login time (None if never logged in)
            login_count=data.get('login_count', 0),     # Number of logins, default 0
            plans_created=len(data.get('meal_plan_history', [])),  # Count of meal plans created
            profiles_created=len(data.get('profile_history', []))  # Count of profiles created
        ))
    # Return the list of UserInfo objects; FastAPI converts to JSON array.
    return result

# ------------------------------------------------------------------------------
# ENDPOINT: POST /api/admin/users/{username}/status - Activate or deactivate a user (admin only)
# ------------------------------------------------------------------------------

# Define a POST endpoint that takes a username from the URL path and a boolean query or body parameter 'is_active'.
@router.post("/users/{username}/status")
# The 'set_user_status' function expects 'username' (path param) and 'is_active' (usually query param, but here as a function argument).
# FastAPI automatically reads 'is_active' from the request body (if JSON) or query string if not specified.
def set_user_status(username: str, is_active: bool, _: Dict = Depends(get_current_admin)):
    # Call the storage function to update the user's active status.
    # Returns True if the user exists and update succeeded, otherwise False.
    success = update_user_status(username, is_active)
    # If the user was not found, raise an HTTP 404 (Not Found) exception.
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    # Return a JSON response confirming the status change.
    return {"message": f"User {username} status updated to {'active' if is_active else 'inactive'}"}

# ------------------------------------------------------------------------------
# ENDPOINT: DELETE /api/admin/users/{username} - Permanently remove a user account (admin only)
# ------------------------------------------------------------------------------

# Define a DELETE endpoint to remove a user by username.
@router.delete("/users/{username}")
# The 'delete_user_endpoint' function receives the username path parameter.
def delete_user_endpoint(username: str, _: Dict = Depends(get_current_admin)):
    # Call delete_user(username) which returns a tuple: (success_flag, message_string)
    success, message = delete_user(username)
    # If deletion fails (e.g., user doesn't exist or trying to delete the last admin), raise HTTP 400.
    if not success:
        raise HTTPException(status_code=400, detail=message)
    # On success, return the message from the storage function (e.g., "User deleted").
    return {"message": message}

# ------------------------------------------------------------------------------
# NEW ENDPOINT: POST /api/admin/users/{username}/upgrade - Upgrade a standard user to premium (admin only)
# ------------------------------------------------------------------------------

# Define a POST endpoint to upgrade a user's account to premium status.
@router.post("/users/{username}/upgrade")
# The 'upgrade_user' function receives the username path parameter.
def upgrade_user(username: str, _: Dict = Depends(get_current_admin)):
    # Import the upgrade function from storage inside the endpoint to avoid circular import issues.
    # This is a common pattern when the endpoint file also imports from the same storage module.
    from utils.storage import upgrade_user_to_premium
    # Call the function; returns True if user existed and was upgraded, False otherwise.
    success = upgrade_user_to_premium(username)
    # If the user doesn't exist, return a 404 error.
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    # Return a success message.
    return {"message": f"User {username} upgraded to premium"}

# ------------------------------------------------------------------------------
# ENDPOINT: POST /api/admin/users - Create a new admin account (only accessible by existing admin)
# ------------------------------------------------------------------------------

# Define a POST endpoint at '/users' (full path '/api/admin/users') that expects a UserRegister body.
# The response is a dictionary (simple message).
@router.post("/users", response_model=Dict)
# The 'create_admin' function receives the UserRegister model (username, password, email, name) and admin dependency.
def create_admin(user: UserRegister, _: Dict = Depends(get_current_admin)):
    # Load all existing users from the JSON storage file into a dictionary.
    users = load_users()
    # Check if the requested username already exists in the loaded data.
    if user.username in users:
        # If duplicate, raise HTTP 400 (Bad Request) with an appropriate message.
        raise HTTPException(status_code=400, detail="Username already exists")
    # Create a new entry for the admin user.
    users[user.username] = {
        # Hash the plain password using the utility function (e.g., bcrypt or werkzeug).
        'password': hash_password(user.password),
        'email': user.email,
        'name': user.name,
        # Generate a timestamp string in the format "YYYY-MM-DD HH:MM:SS".
        'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'profile_history': [],          # Empty list to store created profiles later
        'meal_plan_history': [],        # Empty list to store created meal plans later
        'last_login': None,             # No login yet
        'user_type': 'admin',           # Explicitly set role to admin
        'is_active': True,              # Account is active by default
        'login_count': 0                # Initial login count
    }
    # Save the updated users dictionary back to the JSON file.
    save_users(users)
    # Return a confirmation message.
    return {"message": f"Admin {user.username} created successfully"}