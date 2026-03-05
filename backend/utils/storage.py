import json
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

USER_FILE = "users.json"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict[str, Any]:
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users: Dict[str, Any]) -> None:
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def register_user(username: str, password: str, email: str, name: str) -> Tuple[bool, str]:
    users = load_users()
    if username in users:
        return False, "Username already exists!"
    # Email validation (simple)
    if "@" not in email or "." not in email:
        return False, "Invalid email format!"
    users[username] = {
        'password': hash_password(password),
        'email': email,
        'name': name,
        'registration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'profile_history': [],
        'meal_plan_history': [],
        'last_login': None,
        'user_type': 'user',
        'is_active': True,
        'login_count': 0
    }
    save_users(users)
    return True, "Registration successful!"

def authenticate_user(username: str, password: str, is_admin: bool = False) -> Tuple[bool, str]:
    users = load_users()
    if username not in users:
        return False, "User not found!"
    user = users[username]
    if is_admin and user.get('user_type') != 'admin':
        return False, "Access denied! Admin privileges required."
    if not user.get('is_active', True):
        return False, "Account is deactivated. Contact administrator."
    if user['password'] == hash_password(password):
        # Update last login
        user['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user['login_count'] = user.get('login_count', 0) + 1
        save_users(users)
        return True, "Login successful!"
    return False, "Incorrect password!"

def save_user_profile(username: str, profile_data: Dict[str, Any]) -> bool:
    users = load_users()
    if username in users:
        profile_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        profile_data['plan_id'] = len(users[username]['profile_history']) + 1
        users[username]['profile_history'].append(profile_data)
        users[username]['profile_history'] = users[username]['profile_history'][-10:]
        save_users(users)
        return True
    return False

def save_meal_plan(username: str, meal_plan_data: Dict[str, Any]) -> bool:
    users = load_users()
    if username in users:
        meal_plan_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meal_plan_data['plan_id'] = len(users[username]['meal_plan_history']) + 1
        users[username]['meal_plan_history'].append(meal_plan_data)
        users[username]['meal_plan_history'] = users[username]['meal_plan_history'][-10:]
        save_users(users)
        return True
    return False

def get_user_history(username: str) -> Tuple[List[Dict], List[Dict]]:
    users = load_users()
    if username in users:
        return users[username].get('profile_history', []), users[username].get('meal_plan_history', [])
    return [], []

def get_all_users() -> Dict[str, Any]:
    return load_users()

def update_user_status(username: str, is_active: bool) -> bool:
    users = load_users()
    if username in users:
        users[username]['is_active'] = is_active
        save_users(users)
        return True
    return False

def delete_user(username: str) -> Tuple[bool, str]:
    users = load_users()
    if username not in users:
        return False, "User not found!"
    if users[username].get('user_type') == 'admin':
        return False, "Cannot delete admin accounts!"
    del users[username]
    save_users(users)
    return True, "User deleted successfully!"

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
            'login_count': 0
        }
        save_users(users)
        return True
    return False

def get_system_stats() -> Dict[str, int]:
    users = get_all_users()
    stats = {
        'total_users': len(users),
        'active_users': sum(1 for u in users.values() if u.get('is_active', True)),
        'admins': sum(1 for u in users.values() if u.get('user_type') == 'admin'),
        'total_logins': sum(u.get('login_count', 0) for u in users.values()),
        'today_logins': 0,
        'plans_generated': sum(len(u.get('meal_plan_history', [])) for u in users.values()),
        'profiles_created': sum(len(u.get('profile_history', [])) for u in users.values())
    }
    today = datetime.now().strftime("%Y-%m-%d")
    for user in users.values():
        last_login = user.get('last_login')
        if last_login and last_login.startswith(today):
            stats['today_logins'] += 1
    return stats