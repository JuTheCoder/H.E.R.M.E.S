"""
auth.py: handles user authentication using JWT tokens.
Creates and verifies tokens so only logged in users can 
access the dashboard and API endpoints.
"""
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

#Secret key used to sign tokens (has to be kept private)
SECRET_KEY = os.getenv("SECRET_KEY", "hermes-secret-key-change-in-product")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

#Password hashing setup so we never store plain text passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

#Hardcoded users for now - in production you'd use a database
USERS = {
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash("hermes2026")
    }
}

def verify_password(plain_password, hashed_password):
    """Check if the entered password matches the stored hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    """Creates a JWT token that expires after TOKEN_EXPIRE_MINUTES"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validates the token and returns the username if valid"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
         raise credentials_exception
    return username
