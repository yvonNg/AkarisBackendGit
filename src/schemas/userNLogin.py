# Author: Ng Yee Von
# Created date: 22/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for user and login details

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum 

#---------User Schemas----------

class UserStatus(str, Enum):
    active ="active"
    inactive = "inactive"
    terminated = "deleted"

# Shared fields
class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str

# For creating a new user (input from frontend)
class UserCreate(UserBase):
    password: str  # Plain password from user input

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
    user_status:UserStatus
    user_is_active: bool

    class Config:
        orm_mode = True

#-----------User Login Schemas-------------

# Input from frontend
class LoginCreate(BaseModel):
    email: EmailStr
    password: str
    ip_address: Optional[str] = None

# Output only (when returning login info)
class LoginOut(BaseModel):
    login_id: int
    user_id: int
    login_timestamp: datetime
    ip_address: str

    class Config:
        orm_mode = True