# Author: Ng Yee Von
# Created date: 26/04/2025
# CRUD route for farm_expect schemas
# for farm_expect, not allow update, as this may affect insight value of history data

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models import model
from src.schemas import farmExpectation
from src.database import get_db
from datetime import datetime, timezone

router = APIRouter(prefix="/farm-expect", tags=["Farm Expectations"])

# CREATE a new farm expectation
@router.post("/create-new/farm/{farm_id}", response_model=farmExpectation.FarmExpectOut)
async def create_farm_expect(farm_expect: farmExpectation.FarmExpectCreate, farm_id: int, db: AsyncSession = Depends(get_db)):
    # Check if farm exists
    result = await db.execute(select(model.Farm).where(model.Farm.farm_id == farm_id))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

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

# READ (get single farm expectation)
@router.get("/{farm_expect_id}", response_model=farmExpectation.FarmExpectOut)
async def get_farm_expect(farm_expect_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(model.FarmExpect).where(model.FarmExpect.farm_expect_id == farm_expect_id))
    farm_expect = result.scalar_one_or_none()
    if not farm_expect:
        raise HTTPException(status_code=404, detail="Farm Expectation not found")
    return farm_expect

# DELETE (soft delete) farm expectation
@router.delete("/delete-expect/{farm_expect_id}")
async def soft_delete_farm_expect(farm_expect_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(model.FarmExpect).where(model.FarmExpect.farm_expect_id == farm_expect_id))
    farm_expect = result.scalar_one_or_none()
    if not farm_expect:
        raise HTTPException(status_code=404, detail="Farm Expectation not found")

    farm_expect.record_status = model.FarmExpectationEnum.deleted
    farm_expect.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(farm_expect)

    return {"message": f"Farm Expectation {farm_expect_id} marked as deleted."}
