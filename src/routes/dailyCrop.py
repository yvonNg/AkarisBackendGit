# Author: Ng Yee Von
# Created date: 27/04/2025
# Refined CRUD routes for CropDaily after NFC scanning flow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, Date
from src.models import model
from src.models.model import DailyCropStatusEnum, CropDaily
from src.schemas import cropDaily
from src.schemas.userNLogin import UserOut
from src.database import get_db
from src.dependencies import get_current_user
from datetime import datetime, timezone, timedelta
from typing import List

router = APIRouter(prefix="/crop-daily", tags=["CropDaily"])

@router.post("/new", response_model=cropDaily.OutDailyCrop)
async def create_daily_crop(
    daily_crop: cropDaily.CreateDailyCrop,
    db: AsyncSession = Depends(get_db)
):
    # Step 1: Find the parent crop by NFC code
    crop_result = await db.execute(
        select(model.CropDtl).where(
            model.CropDtl.nfc_code == daily_crop.nfc_code,
            model.CropDtl.crop_is_active == True
        )
    )
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found for given NFC code.")

    # Step 2: Check if today's record already exists
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    existing_daily_result = await db.execute(
        select(model.CropDaily).where(
            model.CropDaily.nfc_code == daily_crop.nfc_code,
            model.CropDaily.record_created_date >= today_start,
            model.CropDaily.record_created_date < today_end,
            model.CropDaily.crop_status == DailyCropStatusEnum.active
        )
    )
    existing_daily_crop = existing_daily_result.scalar_one_or_none()
    if existing_daily_crop:
        raise HTTPException(
            status_code=400,
            detail="A daily crop record already exists for today."
        )

    # Step 3: Create the new Daily Crop record
    new_daily_crop = model.CropDaily(
        crop_id=crop.crop_id,
        nfc_code=daily_crop.nfc_code,
        crop_stage=daily_crop.crop_stage,
        stage_duration_day=daily_crop.stage_duration_day,
        crop_status=DailyCropStatusEnum.active
    )
    db.add(new_daily_crop)

    # Step 4: Update parent crop stage if changed
    if crop.crop_stage != daily_crop.crop_stage:
        crop.crop_stage = daily_crop.crop_stage
        crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 5: Commit all changes
    await db.commit()
    await db.refresh(new_daily_crop)

    return new_daily_crop

# ----------------------- READ Today's Daily Crop by NFC Code -----------------------
@router.get("/latest/{nfc_code}", response_model=cropDaily.OutDailyCrop)
async def get_latest_daily_crop(
    nfc_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    # Step 1: Find the crop by NFC
    crop_result = await db.execute(
        select(model.CropDtl)
        .where(
            model.CropDtl.nfc_code == nfc_code,
            model.CropDtl.crop_is_active == True
        )
    )
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found.")

    # Step 2: Verify the farm belongs to the current user
    farm_result = await db.execute(
        select(model.Farm)
        .where(
            model.Farm.farm_id == crop.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Access denied to this crop.")

    # Step 3: Get the latest CropDaily record
    daily_result = await db.execute(
        select(model.CropDaily)
        .where(model.CropDaily.nfc_code == nfc_code)
        .order_by(desc(model.CropDaily.record_created_date))
        .limit(1)
    )
    latest_daily = daily_result.scalar_one_or_none()
    if not latest_daily:
        raise HTTPException(status_code=404, detail=f"No daily record found for crop {nfc_code}")

    return latest_daily

# Get history value of a nfc_code
@router.get("/history/{nfc_code}", response_model=List[cropDaily.OutDailyCrop])
async def get_crop_daily_history(
    nfc_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    # Step 1: Find the crop by NFC
    crop_result = await db.execute(
        select(model.CropDtl)
        .where(
            model.CropDtl.nfc_code == nfc_code,
            model.CropDtl.crop_is_active == True
        )
    )
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found.")

    # Step 2: Verify the farm belongs to the current user
    farm_result = await db.execute(
        select(model.Farm)
        .where(
            model.Farm.farm_id == crop.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Access denied to this crop.")

    # Step 3: Get all CropDaily records for this crop, ordered from latest to oldest
    history_result = await db.execute(
        select(model.CropDaily)
        .where(model.CropDaily.nfc_code == nfc_code)
        .order_by(desc(model.CropDaily.record_created_date))
    )
    crop_history = history_result.scalars().all()

    if not crop_history:
        raise HTTPException(status_code=404, detail=f"No daily records found for crop {nfc_code}")

    return crop_history

# ----------------------- UPDATE Daily Crop -----------------------
@router.put("/update/{nfc_code}", response_model=cropDaily.OutDailyCrop)
async def update_latest_daily_crop(
    nfc_code: str,
    daily_crop_update: cropDaily.UpdateDailyCrop,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    # Step 1: Find the crop by NFC and validate user ownership via farm
    crop_result = await db.execute(
        select(model.CropDtl)
        .join(model.Farm, model.CropDtl.farm_id == model.Farm.farm_id)
        .where(
            model.CropDtl.nfc_code == nfc_code,
            model.CropDtl.crop_is_active == True,
            model.Farm.user_id == current_user.user_id
        )
    )
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=403, detail="Access denied or crop not found.")

    # Step 2: Get the latest CropDaily record for this crop
    daily_result = await db.execute(
        select(model.CropDaily)
        .where(model.CropDaily.nfc_code == nfc_code)
        .order_by(desc(model.CropDaily.record_created_date))
        .limit(1)
    )
    latest_daily = daily_result.scalar_one_or_none()
    if not latest_daily:
        raise HTTPException(status_code=404, detail=f"No daily record found for crop {nfc_code}")

    # Step 3: Update fields
    update_data = daily_crop_update.model_dump(exclude_unset=True)
    crop_stage_updated = update_data.get("crop_stage")

    for key, value in update_data.items():
        setattr(latest_daily, key, value)

    # Step 4: Update timestamp
    latest_daily.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 5: If crop_stage changed, update parent CropDtl
    if crop_stage_updated is not None and crop.crop_stage != crop_stage_updated:
        crop.crop_stage = crop_stage_updated
        crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 6: Commit and return
    await db.commit()
    await db.refresh(latest_daily)

    return latest_daily

# ----------------------- DELETE (Soft Delete) Daily Crop by NFC -----------------------
@router.delete("/delete/{nfc_code}")
async def soft_delete_today_daily_crop_by_nfc(
    nfc_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    today = datetime.now(timezone.utc).date()

    # Step 1: Find the crop by NFC
    crop_result = await db.execute(
        select(model.CropDtl).where(
            model.CropDtl.nfc_code == nfc_code,
            model.CropDtl.crop_is_active == True
        )
    )
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found.")

    # Step 2: Check that the farm belongs to the current user
    farm_result = await db.execute(
        select(model.Farm).where(
            model.Farm.farm_id == crop.farm_id,
            model.Farm.user_id == current_user.user_id
        )
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=403, detail="Access denied to this crop.")

    # Step 3: Get today's daily crop
    daily_result = await db.execute(
        select(model.CropDaily).where(
            model.CropDaily.nfc_code == nfc_code,
            model.CropDaily.record_created_date.cast(Date) == today,
            model.CropDaily.crop_status != DailyCropStatusEnum.deleted
        )
    )
    daily_crop = daily_result.scalar_one_or_none()
    if not daily_crop:
        raise HTTPException(status_code=400, detail="No daily record for today. Cannot delete previous records.")

    # Step 4: Soft delete
    daily_crop.crop_status = DailyCropStatusEnum.deleted
    daily_crop.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 5: Check and reset crop_stage in CropDtl if needed
    if crop.crop_stage == daily_crop.crop_stage:
    # Find the most recent non-deleted daily crop with the same NFC
        latest_active_result = await db.execute(
            select(model.CropDaily.crop_stage)
            .where(
                model.CropDaily.nfc_code == nfc_code,
                model.CropDaily.crop_status != DailyCropStatusEnum.deleted
            )
            .order_by(desc(model.CropDaily.record_created_date))
            .limit(1)
        )
        latest_active_stage = latest_active_result.scalar_one_or_none()

        # If no active stages are found, reset crop_stage to None
        if not latest_active_stage:
            crop.crop_stage = None
        else:
            # If we find an active stage, update crop_stage only if it's different
            if latest_active_stage != crop.crop_stage:
                crop.crop_stage = latest_active_stage

        # Update the modified date
        crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Commit the changes
    await db.commit()
    await db.refresh(crop)

    return {"message": f"Today's daily crop for NFC {nfc_code} marked as deleted."}
