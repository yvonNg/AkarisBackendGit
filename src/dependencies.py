# Author: Ng Yee Von
# Created date: 28/04/2025
# Dependency for getting the current user from JWT token

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.models.model import User
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# OAuth2 scheme for bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login/")

# Dependency to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    query = select(User).where(User.user_id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
