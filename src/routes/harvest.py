# Author: Ng Yee Von
# Created date: 29/04/2025
# CRUD route for harvests

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from typing import List

from src.models import model
from src.models.model import HarvestUnitEnum
from src.schemas import harvest
from src.database import get_db
from src.dependencies import get_current_user

router = APIRouter(prefix="/harvest", tags=["Harvest"])

@router.post("/new", response_model=harvest.OutHarvest)
async def create_harvest_from_nfc(
    new_harvest: harvest.CreateHarvest,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    try:
        # Step 1: Retrieve crop by NFC code and verify crop status is active
        crop = await db.execute(
            select(model.CropDtl)
            .where(model.CropDtl.nfc_code == new_harvest.nfc_code)
        )
        crop = crop.scalar_one_or_none()

        if not crop:
            raise HTTPException(status_code=404, detail="Crop with this NFC code not found")

        if crop.crop_status != model.CropStatusEnum.active:
            raise HTTPException(status_code=400, detail="Crop is not active")

        # Step 2: Verify that the crop belongs to the current user
        farm = await db.execute(
            select(model.Farm)
            .where(model.Farm.farm_id == crop.farm_id, model.Farm.user_id == current_user.user_id)
        )
        farm = farm.scalar_one_or_none()

        if not farm:
            raise HTTPException(status_code=403, detail="You do not have permission to harvest this crop")

        # Step 3: Ensure no harvest exists on the same day for the same NFC code
        existing_harvest = await db.execute(
            select(model.Harvest)
            .where(
                model.Harvest.nfc_code == new_harvest.nfc_code,
                model.Harvest.harvest_date == new_harvest.harvest_date.date(),
                model.Harvest.record_status == model.RecordStatusEnum.active
            )
        )
        existing_harvest = existing_harvest.scalar_one_or_none()

        if existing_harvest:
            raise HTTPException(status_code=400, detail="Harvest already exists for this crop today")

        # Step 4: Verify if harvest_unit is 'unit', and ensure estimated_kg is provided
        if new_harvest.harvest_unit == HarvestUnitEnum.unit and new_harvest.estimated_kg is None:
            raise HTTPException(status_code=400, detail="estimated_kg must be provided when harvest_unit is 'unit'")

        # Step 5: Create and save the new harvest record
        harvest_record = model.Harvest(
            crop_id=crop.crop_id,
            farm_id=crop.farm_id,  # farm_id comes from the crop data (from cropDtl)
            nfc_code=new_harvest.nfc_code,
            quantity=new_harvest.quantity,
            harvest_unit=new_harvest.harvest_unit,
            estimated_kg=new_harvest.estimated_kg,
            harvest_avg_quality=new_harvest.harvest_avg_quality,
            earn=new_harvest.earn,
            harvest_date=new_harvest.harvest_date,
            record_status=model.RecordStatusEnum.active,
            record_created_date=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        db.add(harvest_record)

        # Step 6: Update the crop's last_harvest_date to the current harvest_date
        crop.last_harvest_date = new_harvest.harvest_date
        crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)  # Set modified date to current time

        # Commit the transaction after the validations are successful
        await db.commit()
        await db.refresh(harvest_record)

        return harvest_record
    except Exception as e:
        # Handle any exceptions here and rollback the transaction if necessary
        await db.rollback()  # Ensure rollback if anything goes wrong
        raise HTTPException(status_code=500, detail=str(e))

# READ: Get latest active harvest for a farm
@router.get("/{nfc_code}", response_model=harvest.OutHarvest)
async def get_latest_harvest(
    nfc_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    # Step 1: Get the crop by NFC code
    result = await db.execute(
        select(model.CropDtl).where(
            model.CropDtl.nfc_code == nfc_code
        )
    )
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found for the given NFC code")

    # Step 2: Verify farm ownership through crop.farm_id
    result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == crop.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Not authorized to view this farm")

    # Step 3: Get latest harvest for this crop/farm
    result = await db.execute(
        select(model.Harvest)
        .where(
            model.Harvest.farm_id == crop.farm_id,
            model.Harvest.nfc_code == nfc_code,
            model.Harvest.record_status == model.RecordStatusEnum.active
        )
        .order_by(model.Harvest.harvest_date.desc())
        .limit(1)
    )
    latest_harvest = result.scalar_one_or_none()
    if not latest_harvest:
        raise HTTPException(status_code=404, detail="No active harvest record found")

    return latest_harvest


# READ: Get all active harvests of a NFC code
@router.get("/{nfc_code}/all", response_model=List[harvest.OutHarvest])
async def get_all_harvests(
    nfc_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    # Step 1: Get the crop by NFC code
    result = await db.execute(
        select(model.CropDtl).where(
            model.CropDtl.nfc_code == nfc_code
        )
    )
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found for the given NFC code")

    # Step 2: Check ownership (crop ➝ farm ➝ user)
    result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == crop.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Not authorized to view this farm")

    # Step 3: Fetch all harvests by farm and NFC code
    result = await db.execute(
        select(model.Harvest)
        .where(
            model.Harvest.farm_id == crop.farm_id,
            model.Harvest.nfc_code == nfc_code,
            model.Harvest.record_status == model.RecordStatusEnum.active
        )
        .order_by(model.Harvest.record_created_date.desc())
    )
    harvests = result.scalars().all()

    if not harvests:
        raise HTTPException(status_code=404, detail="No active harvest records found for this NFC code")

    return harvests

# UPDATE: by given NFC code
@router.put("/{nfc_code}/{harvest_id}", response_model=harvest.OutHarvest)
async def update_harvest(
    nfc_code: str,
    harvest_id: int,
    update_data: harvest.UpdateHarvest,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    # 1. Get crop by NFC code and check if it is active
    result = await db.execute(
        select(model.CropDtl)
        .where(
            model.CropDtl.nfc_code == nfc_code,
            model.CropDtl.crop_status == model.CropStatusEnum.active  # Check if crop is active
        )
    )
    crop = result.scalar_one_or_none()

    if not crop:
        raise HTTPException(status_code=404, detail="Active crop not found")

    # 2. Verify farm ownership
    result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == crop.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Not authorized to update this crop")

    # 3. Find the specific harvest record by harvest_id
    result = await db.execute(
        select(model.Harvest)
        .where(
            model.Harvest.farm_id == crop.farm_id,
            model.Harvest.nfc_code == nfc_code,
            model.Harvest.harvest_id == harvest_id,  # Check by harvest_id
            model.Harvest.record_status == model.RecordStatusEnum.active
        )
    )
    harvest_record = result.scalar_one_or_none()

    if not harvest_record:
        raise HTTPException(status_code=404, detail="Harvest record not found")

    # 4. Business logic validations
    if update_data.harvest_unit == model.HarvestUnitEnum.unit:
        if update_data.estimated_kg is None or update_data.estimated_kg == 0:
            raise HTTPException(status_code=422, detail="estimated_kg must be provided and non-zero when harvest_unit is 'unit'")

    if update_data.harvest_date and update_data.harvest_date != crop.last_harvest_date:
        crop.last_harvest_date = update_data.harvest_date
        crop.crop_modified_date = datetime.utcnow()

    # 5. Update the harvest record using model_dump
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(harvest_record, key, value)

    harvest_record.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(harvest_record)

    return harvest_record

# DELETE: Soft delete a harvest record
@router.delete("/delete/{harvest_id}", response_model=dict)
async def soft_delete_harvest(
    harvest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: model.User = Depends(get_current_user)
):
    # Step 1: Retrieve harvest record
    result = await db.execute(
        select(model.Harvest).where(model.Harvest.harvest_id == harvest_id)
    )
    harvest_record = result.scalar_one_or_none()
    if not harvest_record:
        raise HTTPException(status_code=404, detail="Harvest record not found")

    # Step 2: Check if already deleted
    if harvest_record.record_status == model.RecordStatusEnum.deleted:
        return {"message": f"Harvest record {harvest_id} is already marked as deleted."}

    # Step 3: Verify farm ownership
    farm_result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == harvest_record.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    if not farm_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized to delete this harvest record")

    # Step 4: Get the crop
    crop_result = await db.execute(
        select(model.CropDtl).where(model.CropDtl.nfc_code == harvest_record.nfc_code)
    )
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    # Step 5: Check if this harvest is the most recent (include it in the list)
    all_active_harvests_result = await db.execute(
        select(model.Harvest)
        .where(
            model.Harvest.nfc_code == harvest_record.nfc_code,
            model.Harvest.record_status == model.RecordStatusEnum.active
        )
        .order_by(model.Harvest.harvest_date.desc())
    )
    active_harvests = all_active_harvests_result.scalars().all()

    # Include the current (soon-to-be deleted) record to check if it's most recent
    is_most_recent = not active_harvests or (
        active_harvests and harvest_record.harvest_date >= active_harvests[0].harvest_date
    )

    if is_most_recent:
        # Find next most recent (excluding the one to be deleted)
        next_recent = next(
            (h for h in active_harvests if h.harvest_id != harvest_record.harvest_id), None
        )
        crop.last_harvest_date = next_recent.harvest_date if next_recent else None
        crop.crop_modified_date = datetime.utcnow()

    # Step 6: Soft delete the harvest record
    harvest_record.record_status = model.RecordStatusEnum.deleted
    harvest_record.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 7: Commit
    await db.commit()
    await db.refresh(harvest_record)
    await db.refresh(crop)

    return {
        "message": f"Harvest record {harvest_id} marked as deleted.",
        "last_harvest_date": crop.last_harvest_date
    }
