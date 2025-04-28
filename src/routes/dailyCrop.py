# Author: Ng Yee Von
# Created date: 27/04/2025
# Refined CRUD routes for CropDaily after NFC scanning flow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models import model
from src.models.model import DailyCropStatusEnum, CropDaily
from src.schemas import cropDaily
from src.database import get_db
from datetime import datetime, timezone, timedelta
from sqlalchemy import Date

router = APIRouter(prefix="/crop-daily", tags=["CropDaily"])

# ----------------------- CHECK if today's record exist -----------------------
@router.get("/check-today/{nfc_code}")
async def check_today_crop_daily(
    nfc_code: str,
    db: AsyncSession = Depends(get_db)
):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    result = await db.execute(
        select(model.CropDaily)
        .where(
            model.CropDaily.nfc_code == nfc_code,
            model.CropDaily.record_created_date >= today_start,
            model.CropDaily.record_created_date < today_end,
            model.CropDaily.crop_status == DailyCropStatusEnum.active
        )
    )
    daily_crop = result.scalar_one_or_none()

    if daily_crop:
        return {"exist": True, "daily_id": daily_crop.daily_id}
    else:
        return {"exist": False}

# ----------------------- CREATE new Daily Crop (after scanning) -----------------------
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

    # Step 2: Create the new Daily Crop record
    new_daily_crop = model.CropDaily(
        crop_id=crop.crop_id,
        nfc_code=daily_crop.nfc_code,
        crop_stage=daily_crop.crop_stage,
        stage_duration_day=daily_crop.stage_duration_day,
        crop_status=DailyCropStatusEnum.active
    )
    db.add(new_daily_crop)

    # Step 3: Update the parent CropDtl only if the stage is different
    if crop.crop_stage != daily_crop.crop_stage:
        crop.crop_stage = daily_crop.crop_stage
        crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 4: Commit all changes together
    await db.commit()
    await db.refresh(new_daily_crop)

    return new_daily_crop

# ----------------------- READ Today's Daily Crop by NFC Code -----------------------
@router.get("/get-today/{nfc_code}", response_model=cropDaily.OutDailyCrop)
async def get_today_daily_crop(
    nfc_code: str,
    db: AsyncSession = Depends(get_db)
):
    today = datetime.now(timezone.utc).date()

    result = await db.execute(
        select(model.CropDaily)
        .where(
            model.CropDaily.nfc_code == nfc_code,
            model.CropDaily.record_created_date.cast(Date) == today
        )
    )
    daily_crop = result.scalar_one_or_none()

    if not daily_crop:
        raise HTTPException(
            status_code=404, 
            detail=f"No today data for crop {nfc_code}"
        )

    return daily_crop

# ----------------------- UPDATE Daily Crop -----------------------
@router.put("/update/{daily_id}", response_model=cropDaily.OutDailyCrop)
async def update_daily_crop(
    daily_id: int,
    daily_crop_update: cropDaily.UpdateDailyCrop,
    db: AsyncSession = Depends(get_db)
):
    # Step 1: Find the existing daily crop record
    result = await db.execute(
        select(model.CropDaily).where(model.CropDaily.daily_id == daily_id)
    )
    daily_crop = result.scalar_one_or_none()
    if not daily_crop:
        raise HTTPException(status_code=404, detail="Daily Crop not found")

    # Step 2: Update fields from request
    update_data = daily_crop_update.model_dump(exclude_unset=True)
    crop_stage_updated = update_data.get("crop_stage")

    for key, value in update_data.items():
        setattr(daily_crop, key, value)

    # Step 3: Always update record_updated_date
    daily_crop.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 4: If crop_stage is updated, check parent CropDtl
    if crop_stage_updated is not None:
        # Fetch the parent CropDtl
        crop_result = await db.execute(
            select(model.CropDtl).where(
                model.CropDtl.crop_id == daily_crop.crop_id,
                model.CropDtl.crop_is_active == True
            )
        )
        crop = crop_result.scalar_one_or_none()
        if crop:
            if crop.crop_stage != crop_stage_updated:
                crop.crop_stage = crop_stage_updated
                crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # Step 5: Commit all changes together
    await db.commit()
    await db.refresh(daily_crop)

    return daily_crop

# ----------------------- DELETE (Soft Delete) Daily Crop -----------------------
@router.delete("/delete/{daily_id}")
async def soft_delete_daily_crop(
    daily_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(model.CropDaily).where(model.CropDaily.daily_id == daily_id)
    )
    daily_crop = result.scalar_one_or_none()
    if not daily_crop:
        raise HTTPException(status_code=404, detail="Daily Crop not found")

    daily_crop.crop_status = DailyCropStatusEnum.deleted
    daily_crop.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(daily_crop)

    return {"message": f"Daily Crop {daily_id} marked as deleted."}
