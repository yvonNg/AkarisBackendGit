# Author: Ng Yee Von
# Created date: 26/04/2025
# CRUD routes for farm operations (uses JWT for user identity)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from src.models import model
from src.models.model import FarmStatusEnum, FarmExpectationEnum, User
from src.schemas import farm
from src.database import get_db
from src.dependencies import get_current_user

router = APIRouter(prefix="/farms", tags=["Farms"])

# CREATE new farm
@router.post("/create", response_model=farm.FarmOut)
async def create_farm(
    farm_data: farm.FarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # current_user is the object returned by get_current_user
    print(f"Creating farm for user: {current_user.user_id}")

    new_farm = model.Farm(
        user_id=current_user.user_id,
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

# READ (all farm belong to a user in list)
@router.get("/my-farms", response_model=list[farm.FarmOut])
async def get_user_farms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(model.Farm).where(
            model.Farm.user_id == current_user.user_id,
            model.Farm.farm_is_active == True
        )
    )
    farms = result.scalars().all()
    return farms

# UPDATE
@router.put("/update/{farm_id}", response_model=farm.FarmOut)
async def update_farm(
    farm_id: int,
    farm_update: farm.FarmCreateNUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
        farm_obj = result.scalar_one_or_none()
        if not farm_obj:
            raise HTTPException(status_code=404, detail="Farm not found")
        
        # Check farm ownership
        if farm_obj.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Unauthorized to update this farm")

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
async def soft_delete_farm(farm_id: int, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
    farm_obj = result.scalar_one_or_none()
    if not farm_obj:
        raise HTTPException(status_code=404, detail="Farm not found")

    #Check Ownership
    if farm_obj.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this farm")

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
