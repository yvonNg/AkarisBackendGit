# Author: Ng Yee Von
# Created date: 27/04/2025
# Full CRUD route for CropDtl

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone

from src.models.model import CropDtl, CropStatusEnum, Farm, User, PlantMethod, MethodStatusEnum
from src.schemas import cropDtl
from src.database import get_db
from src.dependencies import get_current_user

router = APIRouter(prefix="/crops", tags=["Crops"])

# Helper: get crop by NFC code
async def get_crop_by_nfc_code(nfc_code: str, db: AsyncSession) -> CropDtl:
    result = await db.execute(select(CropDtl).where(CropDtl.nfc_code == nfc_code))
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    return crop

# Helper: verify crop belongs to user's farm
async def verify_farm_ownership(crop: CropDtl, current_user: User, db: AsyncSession):
    query = select(Farm).where(Farm.farm_id == crop.farm_id, Farm.user_id == current_user.user_id)
    result = await db.execute(query)
    farm = result.scalar_one_or_none()

    if farm is None:
        raise HTTPException(status_code=403, detail="You are not authorized to access this crop.")

# CREATE new crop
@router.post("/new", response_model=cropDtl.CropOut)
async def create_crop(
    crop: cropDtl.CreateCrop,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check if NFC code already exists
    existing_crop = await db.execute(select(CropDtl).where(CropDtl.nfc_code == crop.nfc_code))
    if existing_crop.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="NFC code already exists, cannot create duplicate crop.")

    # 2. Check if farm_id belongs to current_user
    query = select(Farm).where(Farm.farm_id == crop.farm_id, Farm.user_id == current_user.user_id)
    result = await db.execute(query)
    farm = result.scalar_one_or_none()
    if farm is None:
        raise HTTPException(status_code=403, detail="You are not authorized to create crop in this farm.")

    # 3. Handle other_method (if provided)
    method_id_to_use = crop.method_id  # Default to provided method_id

    if crop.other_method:
        new_method = PlantMethod(
            method=crop.other_method,
            other_method=crop.other_method,
            record_created_by=current_user.user_id,
            record_status=MethodStatusEnum.active
        )
        db.add(new_method)
        await db.flush()  # Flush to get new method id

        method_id_to_use = new_method.plant_method_id

    # 4. Now create new crop with correct method_id
    new_crop = CropDtl(
        farm_id=crop.farm_id,
        nfc_code=crop.nfc_code,
        farm_abbrev=crop.farm_abbrev,
        crop_type=crop.crop_type,
        crop_subtype=crop.crop_subtype,
        plantation_date=crop.plantation_date,
        method_id=method_id_to_use,
        crop_yrs=crop.crop_yrs,
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
async def get_crop(
    nfc_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crop = await get_crop_by_nfc_code(nfc_code, db)
    await verify_farm_ownership(crop, current_user, db)
    return crop

# UPDATE crop by NFC code
@router.put("/update-by-nfc/{nfc_code}", response_model=cropDtl.CropOut)
async def update_crop(
    nfc_code: str,
    crop_update: cropDtl.UpdateCrop,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crop = await get_crop_by_nfc_code(nfc_code, db)
    await verify_farm_ownership(crop, current_user, db)

    for key, value in crop_update.model_dump(exclude_unset=True).items():
        setattr(crop, key, value)

    crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(crop)

    return crop

# DELETE (soft delete crop by NFC code, and check method)
@router.delete("/delete-by-nfc/{nfc_code}")
async def soft_delete_crop(
    nfc_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crop = await get_crop_by_nfc_code(nfc_code, db)
    await verify_farm_ownership(crop, current_user, db)

    # 1. Soft delete the crop
    crop.crop_is_active = False
    crop.crop_status = CropStatusEnum.terminated
    crop.crop_modified_date = datetime.now(timezone.utc).replace(tzinfo=None)

    # 2. Handle PlantMethod soft delete if needed
    method_id = crop.method_id
    if method_id:
        # Check if any other active crops are using this method
        other_crops_query = await db.execute(
            select(CropDtl)
            .where(CropDtl.method_id == method_id)
            .where(CropDtl.crop_is_active == True)
            .where(CropDtl.nfc_code != nfc_code)
        )
        other_crops = other_crops_query.scalars().all()

        if not other_crops:
            # No other active crops using the method → soft delete the method
            method_query = await db.execute(
                select(PlantMethod).where(PlantMethod.plant_method_id == method_id)
            )
            method = method_query.scalar_one_or_none()

            if method:
                method.record_status = MethodStatusEnum.deleted
                method.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()

    return {"message": "Crop has been soft deleted successfully."}
