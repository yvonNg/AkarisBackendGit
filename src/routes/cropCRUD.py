# Author: Ng Yee Von
# Created date: 27/04/2025
# CRUD route for CropDtl

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.model import CropDtl, CropStatusEnum
from src.schemas import cropDtl
from src.database import get_db
from datetime import datetime, timezone

router = APIRouter(prefix="/crops", tags=["Crops"])

# Helper function: get crop by NFC code
async def get_crop_by_nfc_code(nfc_code: str, db: AsyncSession) -> CropDtl:
    result = await db.execute(select(CropDtl).where(CropDtl.nfc_code == nfc_code))
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    return crop

# CREATE new crop
@router.post("/new", response_model=cropDtl.CropOut)
async def create_crop(crop: cropDtl.CreateCrop, db: AsyncSession = Depends(get_db)):
    # Check if NFC code already exists
    existing_crop = await db.execute(select(CropDtl).where(CropDtl.nfc_code == crop.nfc_code))
    if existing_crop.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="NFC code already exists, cannot create duplicate crop.")

    new_crop = CropDtl(
        farm_id=crop.farm_id,
        nfc_code=crop.nfc_code,
        farm_abbrev=crop.farm_abbrev,
        crop_type=crop.crop_type,
        crop_subtype=crop.crop_subtype,
        plantation_date=crop.plantation_date,
        method_id=crop.method_id,
        crop_yrs=crop.crop_yrs,
        #crop_stage=crop.crop_stage,
        last_harvest_date=crop.last_harvest_date,
        crop_status=CropStatusEnum.active,
        crop_is_active=True
    )

    db.add(new_crop)
    await db.commit()
    await db.refresh(new_crop)

    return new_crop

# READ crop by NFC code
@router.get("/get-by-nfc/{nfc_code}", response_model=cropDtl.CropOut)
async def get_crop(nfc_code: str, db: AsyncSession = Depends(get_db)):
    crop = await get_crop_by_nfc_code(nfc_code, db)
    return crop

# UPDATE crop by NFC code
@router.put("/update-by-nfc/{nfc_code}", response_model=cropDtl.CropOut)
async def update_crop(nfc_code: str, crop_update: cropDtl.UpdateCrop, db: AsyncSession = Depends(get_db)):
    crop = await get_crop_by_nfc_code(nfc_code, db)

    for key, value in crop_update.model_dump(exclude_unset=True).items():
        setattr(crop, key, value)

    crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(crop)

    return crop

# DELETE (soft delete crop by NFC code)
@router.delete("/delete-by-nfc/{nfc_code}")
async def soft_delete_crop(nfc_code: str, db: AsyncSession = Depends(get_db)):
    crop = await get_crop_by_nfc_code(nfc_code, db)

    crop.crop_is_active = False
    crop.crop_status = CropStatusEnum.terminated
    crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(crop)

    return {"message": f"Crop with NFC code {nfc_code} marked as terminated."}
