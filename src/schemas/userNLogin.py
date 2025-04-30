from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional
from enum import Enum
import re

# User Status Enum
class UserStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    terminated = "deleted"

# Shared fields for user data
class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str

# For creating a new user (input from frontend)
class UserCreate(UserBase):
    password: str  # Plain password from user input

    @validator("password")
    def validate_password(cls, value):
        # Check password length
        if not 8 <= len(value) <= 16:
            raise ValueError("Password must be between 8 and 16 characters")
        # Check if there is at least one uppercase letter
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        # Check if there is at least one lowercase letter
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        # Check if there is at least one digit
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        # Check if there is at least one special character
        if not re.search(r"[^\w\s]", value):
            raise ValueError("Password must contain at least one special character")
        return value

# For user update (optional fields)
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

# For response data (output)
class UserOut(UserBase):
    user_id: int
    registered_date: datetime
    last_login_date: Optional[datetime] = None
    user_status: UserStatus
    user_is_active: bool

    class Config:
        orm_mode = True

#-----------User Login Schemas-------------
class LoginCreate(BaseModel):
    email: EmailStr
    password: str
    ip_address: Optional[str] = None

class LoginOut(BaseModel):
    login_id: int
    user_id: int
    login_timestamp: datetime
    ip_address: str

    class Config:
        orm_mode = True

# --------- Token Response Schemas ---------
class UserPreview(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    login_timestamp: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginResponse(Token):
    user: UserPreview
