"""
H.E.R.M.E.S. Authentication Module
Handles user login, JWT tokens, and password hashing.
"""

import json
import os
import secrets
import hashlib
import time

# Where we store user accounts
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# Secret key for signing JWT tokens - generated fresh on first run
SECRET_FILE = os.path.join(os.path.dirname(__file__), ".secret_key")

# Token expires after 24 hours
TOKEN_EXPIRY = 86400


def get_secret_key():
    """Load or create the secret key used to sign tokens."""
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "r") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(SECRET_FILE, "w") as f:
        f.write(key)
    return key


SECRET_KEY = get_secret_key()


def hash_password(password):
    """Hash a password with a random salt using SHA-256."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt + ":" + hashed


def verify_password(password, stored_hash):
    """Check a password against the stored hash."""
    parts = stored_hash.split(":")
    if len(parts) != 2:
        return False
    salt, expected = parts
    actual = hashlib.sha256((salt + password).encode()).hexdigest()
    return actual == expected


def load_users():
    """Load user accounts from disk."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    """Save user accounts to disk."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def create_user(username, password, role="viewer"):
    """Add a new user account."""
    users = load_users()
    if username in users:
        return False, "User already exists"
    users[username] = {
        "password": hash_password(password),
        "role": role,
        "created": time.time()
    }
    save_users(users)
    return True, "User created"


def authenticate(username, password):
    """Check login credentials and return a token if valid."""
    users = load_users()
    if username not in users:
        return None
    if not verify_password(password, users[username]["password"]):
        return None
    return create_token(username, users[username].get("role", "viewer"))


def create_token(username, role):
    """Build a simple signed token with expiration."""
    payload = {
        "user": username,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRY,
        "iat": int(time.time())
    }
    payload_str = json.dumps(payload, separators=(",", ":"))
    import base64
    encoded = base64.urlsafe_b64encode(payload_str.encode()).decode()
    signature = hashlib.sha256((encoded + SECRET_KEY).encode()).hexdigest()
    return encoded + "." + signature


def verify_token(token):
    """Validate a token and return the payload if it's legit."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        encoded, signature = parts
        expected_sig = hashlib.sha256((encoded + SECRET_KEY).encode()).hexdigest()
        if signature != expected_sig:
            return None
        import base64
        payload_str = base64.urlsafe_b64decode(encoded).decode()
        payload = json.loads(payload_str)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def delete_user(username):
    """remove a user account. can't delete the last admin."""
    users = load_users()
    if username not in users:
        return False, "user not found"
    # don't let someone remove the only admin
    admins = [u for u in users if users[u].get("role") == "admin"]
    if users[username].get("role") == "admin" and len(admins) <= 1:
        return False, "can't delete the only admin"
    del users[username]
    save_users(users)
    return True, "user deleted"


def list_users():
    """get all users without their password hashes"""
    users = load_users()
    result = []
    for name, info in users.items():
        result.append({
            "username": name,
            "role": info.get("role", "viewer")
        })
    return result


def setup_default_accounts():
    """create default admin and user accounts if nobody exists yet"""
    users = load_users()
    if len(users) == 0:
        create_user("admin", "hermes2026", role="admin")
        create_user("user", "hermes", role="viewer")
        print("Created default accounts:")
        print("  Admin  -> username: admin  password: hermes2026")
        print("  User   -> username: user   password: hermes")
        print("CHANGE THESE PASSWORDS after first login!")
