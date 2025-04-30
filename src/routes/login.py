# Author: Ng Yee Von
# Created date: 22/04/2025
# Logic file for user login - return JWT token and user preview

from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from src.schemas.userNLogin import LoginCreate, LoginResponse, UserPreview
from src.models.model import User, Login
from src.database import SessionLocal
from dotenv import load_dotenv
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load .env file
load_dotenv()

# Environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Database dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

# Password verification function
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT creation function
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Login endpoint
@router.post("/users/login/", response_model=LoginResponse)
async def login_user(
    login_data: LoginCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Fetch user by email
    query = select(User).filter(User.email == login_data.email)
    result = await db.execute(query)
    user = result.scalars().first()

    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered user found with this email"
        )

    # Verify password
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Get IP address from request
    client_ip = request.headers.get("x-forwarded-for", request.client.host)

    # Save login record
    new_login = Login(
        user_id=user.user_id,
        ip_address=client_ip
    )
    db.add(new_login)
    await db.commit()
    await db.refresh(new_login)

    # Update last login timestamp
    user.last_login_date = new_login.login_timestamp
    await db.commit()

    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(user.user_id)}
    )

    # Prepare user preview
    user_preview = UserPreview(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        last_login_date=user.last_login_date
    )

    # Return token and user data
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_preview
    )
