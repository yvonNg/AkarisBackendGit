# Author: Ng Yee Von
# Created date: 26/04/2025
# CRUD routes for farm operations (uses JWT for user identity)

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from jose import jwt, JWTError
from src.models import model
from src.models.model import FarmStatusEnum, FarmExpectationEnum
from src.schemas import farm
from src.database import get_db
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

router = APIRouter(prefix="/farms", tags=["Farms"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login/")

# Helper function to extract user_id from JWT token
def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except JWTError:
        raise credentials_exception

# CREATE new farm
@router.post("/create", response_model=farm.FarmOut)
async def create_farm(
    farm_data: farm.FarmCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    new_farm = model.Farm(
        user_id=user_id,
        farm_abbrev=farm_data.farm_abbrev,
        crop_type=farm_data.crop_type,
        farm_size=farm_data.farm_size,
        farm_location=farm_data.farm_location,
        farm_status=FarmStatusEnum.active,
        farm_is_active=True
    )

    db.add(new_farm)
    await db.commit()
    await db.refresh(new_farm)

    return new_farm

# READ (get single farm)
@router.get("/get/{farm_id}", response_model=farm.FarmOut)
async def get_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
    farm_obj = result.scalar_one_or_none()
    if not farm_obj:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm_obj

# UPDATE
@router.put("/update/{farm_id}", response_model=farm.FarmOut)
async def update_farm(
    farm_id: int,
    farm_update: farm.FarmCreateNUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
        farm_obj = result.scalar_one_or_none()
        if not farm_obj:
            raise HTTPException(status_code=404, detail="Farm not found")

        is_farm_abbrev_updated = False

        for key, value in farm_update.model_dump(exclude_unset=True).items():
            if key == "farm_abbrev" and getattr(farm_obj, key) != value:
                is_farm_abbrev_updated = True
            setattr(farm_obj, key, value)

        farm_obj.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

        await db.commit()
        await db.refresh(farm_obj)

        if is_farm_abbrev_updated:
            farm_expectation = await db.execute(select(model.FarmExpect).where(model.FarmExpect.farm_id == farm_id))
            farm_expect = farm_expectation.scalar_one_or_none()
            if farm_expect:
                farm_expect.farm_abbrev = farm_obj.farm_abbrev
                farm_expect.record_updated_date = farm_obj.record_updated_date
                await db.commit()
                await db.refresh(farm_expect)

        return farm_obj

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# DELETE (soft delete)
@router.delete("/delete/{farm_id}")
async def soft_delete_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
    farm_obj = result.scalar_one_or_none()
    if not farm_obj:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm_obj.farm_is_active = False
    farm_obj.farm_status = FarmStatusEnum.terminated
    farm_obj.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    farm_expectation = await db.execute(select(model.FarmExpect).where(model.FarmExpect.farm_id == farm_id))
    farm_expect = farm_expectation.scalar_one_or_none()
    if farm_expect:
        farm_expect.record_status = FarmExpectationEnum.deleted
        farm_expect.record_updated_date = farm_obj.record_updated_date
        await db.commit()
        await db.refresh(farm_expect)

    await db.commit()
    await db.refresh(farm_obj)

    return {"message": f"Farm {farm_id} marked as terminated, and farm expectation status set to inactive."}
