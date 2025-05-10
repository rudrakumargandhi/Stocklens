import json
import os

USER_DATA_FILE = "users.json"

# Default users
initial_users = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "portfolio": []
    },
    "user1": {
        "password": "user123",
        "role": "user",
        "portfolio": []
    }
}

# Load users safely (regenerate if corrupted or empty)
def load_users():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                data = f.read().strip()
                if data == "":
                    raise json.JSONDecodeError("Empty file", "", 0)
                return json.loads(data)
        except json.JSONDecodeError:
            print("⚠️ Corrupted or empty users.json. Regenerating default users.")
            save_users(initial_users)
            return initial_users
    else:
        save_users(initial_users)
        return initial_users
    

def register_user(username, password):
    users = load_users()
    if username in users:
        return False  # User already exists
    users[username] = {
        "password": password,
        "role": "user",
        "portfolio": []
    }
    save_users(users)
    return True


# Save users to file
def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

# Global users variable
users = load_users()
