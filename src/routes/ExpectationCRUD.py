# Author: Ng Yee Von
# Created date: 26/04/2025
# CRUD route for farm_expect schemas
# For farm_expect, updates are not allowed as this may affect insight value of history data

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from src.models import model
from src.schemas import farmExpectation
from typing import List
from src.database import get_db
from src.dependencies import get_current_user

router = APIRouter(prefix="/farm-expect", tags=["Farm Expectations"])

# CREATE a new farm expectation
@router.post("/new/farm/{farm_id}", response_model=farmExpectation.FarmExpectOut)
async def create_farm_expect(
    farm_expect: farmExpectation.FarmExpectCreate,
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    # Step 1: Check if the farm exists
    result = await db.execute(
        select(model.Farm).where(model.Farm.farm_id == farm_id)
    )
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Step 2: Check if the current user owns the farm
    if farm.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this farm")

    # Step 3: Check if the farm is active
    if not farm.farm_is_active:
        raise HTTPException(status_code=400, detail="Farm is not active or has been terminated")

    # Step 4: Create the farm expectation record
    new_farm_expect = model.FarmExpect(
        farm_id=farm_id,
        farm_abbrev=farm.farm_abbrev,
        expected_harvest_date=farm_expect.expected_harvest_date,
        expected_harvest_base_uom=farm_expect.expected_harvest_base_uom,
        expected_income=farm_expect.expected_income,
        record_status=model.FarmExpectationEnum.active
    )

    db.add(new_farm_expect)
    await db.commit()
    await db.refresh(new_farm_expect)

    return new_farm_expect

# READ (get latest active farm expectation by farm_id)
@router.get("/{farm_id}", response_model=farmExpectation.FarmExpectOut)
async def get_latest_farm_expect(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    # Check if user owns the farm
    farm_result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Not authorized to view this farm")

    # Get the latest active farm expectation
    result = await db.execute(
        select(model.FarmExpect)
        .where(
            model.FarmExpect.farm_id == farm_id,
            model.FarmExpect.record_status == 'active'
        )
        .order_by(model.FarmExpect.record_created_date.desc())
        .limit(1)
    )
    farm_expect = result.scalar_one_or_none()
    if not farm_expect:
        raise HTTPException(status_code=404, detail="No active farm expectation found for this farm")

    return farm_expect

# Get aAll Expectation in DECS
@router.get("/{farm_id}/expectations", response_model=List[farmExpectation.FarmExpectOut])
async def get_farm_expectations(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    # Check if user owns the farm
    farm_result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Not authorized to view this farm")

    # Get all active expectations sorted from newest to oldest
    result = await db.execute(
        select(model.FarmExpect)
        .where(
            model.FarmExpect.farm_id == farm_id,
            model.FarmExpect.record_status == 'active'
        )
        .order_by(model.FarmExpect.record_created_date.desc())
    )
    expectations = result.scalars().all()

    if not expectations:
        raise HTTPException(status_code=404, detail="No active farm expectations found")

    return expectations

# DELETE (soft delete) farm expectation
@router.delete("/delete/{farm_expect_id}")
async def soft_delete_farm_expect(
    farm_expect_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    result = await db.execute(
        select(model.FarmExpect).where(model.FarmExpect.farm_expect_id == farm_expect_id)
    )
    farm_expect = result.scalar_one_or_none()
    if not farm_expect:
        raise HTTPException(status_code=404, detail="Farm Expectation not found")

    # Ownership check via related farm
    farm_result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == farm_expect.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Not authorized to delete this farm expectation")

    farm_expect.record_status = model.FarmExpectationEnum.deleted
    farm_expect.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(farm_expect)

    return {"message": f"Farm Expectation {farm_expect_id} marked as deleted."}
