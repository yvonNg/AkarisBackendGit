# Author: Ng Yee Von
# Created date: 22/04/2025
# Schemas file (define logic of data when handling CRUD request)
# this is for user login

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from src.schemas.userNLogin import LoginCreate, LoginOut
from src.models.model import User, Login
from src.database import SessionLocal

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Reuse your DB session dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

# Password verification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Login endpoint
@router.post("/users/login/", response_model=LoginOut)
async def login_user(login_data: LoginCreate, db: AsyncSession = Depends(get_db)):
    # Find user by email
    query = select(User).filter(User.email == login_data.email)
    result = await db.execute(query)
    user = result.scalars().first()

     # Check if user does not exist
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registered user found with this email")

    # Check if password is incorrect
    if not verify_password(login_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    # Save login info to Login table
    new_login = Login(
        user_id=user.user_id,
        ip_address=login_data.ip_address or "0.0.0.0"  # default if not sent
    )

    db.add(new_login)
    await db.commit()
    await db.refresh(new_login)

   # If it's the first login, set last_login_date
    if user.last_login_date is None:
        user.last_login_date = new_login.login_timestamp
    else:
        user.last_login_date = new_login.login_timestamp
        
    await db.commit()

    return new_login
