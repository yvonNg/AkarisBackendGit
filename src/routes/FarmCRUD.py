# Author: Ng Yee Von
# Created date: 26/04/2025
# Schemas file (define logic of data when handling CRUD request)
# CRUD route for farm schemas

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models import model
from src.models.model import Farm, FarmStatusEnum, FarmExpectationEnum, FarmExpect
from src.schemas import farm, farmExpectation
from src.database import get_db
from datetime import datetime, timezone

router = APIRouter(prefix="/farms", tags=["Farms"])

# CREATE new farm
@router.post("/create-farm/users/{user_id}", response_model=farm.FarmOut)
async def create_farm(farm: farm.FarmCreate, user_id: int, db: AsyncSession = Depends(get_db)):
    # Create the new Farm record
    new_farm = model.Farm(
        user_id=user_id,
        farm_abbrev=farm.farm_abbrev,
        crop_type=farm.crop_type,
        farm_size=farm.farm_size,
        farm_location=farm.farm_location,
        farm_status=FarmStatusEnum.active,  
        farm_is_active=True
    )
    
    # Add new farm to DB
    db.add(new_farm)
    await db.commit()
    await db.refresh(new_farm)
    
    return new_farm

# READ (get single farm)
@router.get("/get-farm/{farm_id}", response_model=farm.FarmOut)
async def get_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm

# UPDATE
@router.put("/update-farm/{farm_id}", response_model=farm.FarmOut)
async def update_farm(farm_id: int, farm_update: farm.FarmCreateNUpdate, db: AsyncSession = Depends(get_db)):
    try:
        # Find the existing farm
        result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
        farm = result.scalar_one_or_none()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")

        # Track if the farm.abbrev is updated
        is_farm_abbrev_updated = False

        # Update the Farm record
        for key, value in farm_update.model_dump(exclude_unset=True).items():
            if key == "farm_abbrev" and getattr(farm, key) != value:
                is_farm_abbrev_updated = True
            setattr(farm, key, value)

        # Set the updated date
        farm.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

        # Commit changes to the database
        await db.commit()
        await db.refresh(farm)

        # Update FarmExpectation only if farm.abbrev was updated
        if is_farm_abbrev_updated:
            farm_expectation = await db.execute(select(model.FarmExpect).where(model.FarmExpect.farm_id == farm_id))
            farm_expect = farm_expectation.scalar_one_or_none()
            if farm_expect:
                farm_expect.farm_abbrev = farm.farm_abbrev
                farm_expect.record_updated_date = farm.record_updated_date
                await db.commit()
                await db.refresh(farm_expect)

        return farm
    
    except Exception as e:
        # If an error occurs, raise a 500 internal server error with details
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# DELETE (soft delete)
@router.delete("/delete-farm/{farm_id}")
async def soft_delete_farm(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Set farm status to terminated and mark as inactive (soft delete)
    farm.farm_is_active = False
    farm.farm_status = FarmStatusEnum.terminated 
    farm.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Update the corresponding FarmExpectation record to inactive
    farm_expectation = await db.execute(select(model.FarmExpect).where(model.FarmExpect.farm_id == farm_id))
    farm_expect = farm_expectation.scalar_one_or_none()
    if farm_expect:
        farm_expect.record_status = FarmExpectationEnum.deleted 
        farm_expect.record_updated_date = farm.record_updated_date  # update the record_updated_date
        await db.commit()
        await db.refresh(farm_expect)

    await db.commit()
    await db.refresh(farm)

    return {"message": f"Farm {farm_id} marked as terminated, and farm expectation status set to inactive."}

