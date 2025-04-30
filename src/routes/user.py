# Author: Ng Yee Von
# Created date: 22/04/2025
# Schemas file (define logic of data when handling CRUD request)
# this is for creating a new user

from fastapi import APIRouter, HTTPException, status, Depends
from src.schemas.userNLogin import UserCreate, UserOut
from src.models.model import User
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import SessionLocal
from sqlalchemy.future import select
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import re

def validate_password(password: str) -> bool:
    if not 8 <= len(password) <= 16:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):  # At least one digit
        return False
    if not re.search(r"[^\w\s]", password):  # At least one special character (not letter/number/underscore/space)
        return False
    return True


# Initialize the router and password hashing context
router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

# Password hash function
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Route to register a new user
#UserCreate is used (complete info together with input in UserBase)
@router.post("/users/register/", response_model=UserOut)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if the email already exists
    query = select(User).filter(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalars().first()
# if same email re-registered, return output "Email alredy registered"    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Validate password format
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 8-16 characters, include upper and lower case letters, at least one number, and one symbol."
        )
    
    # Hash the password
    hashed_password = hash_password(user_data.password)
    
    # Create new user instance
    new_user = User(
        first_name=user_data.first_name,
        last_name = user_data.last_name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password=hashed_password
    )
    
    # Add the user to the database
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user
