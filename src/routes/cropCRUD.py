# Author: Ng Yee Von
# Created date: 27/04/2025
# Full CRUD route for CropDtl

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
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

# CREATE new Crop
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

    # 2. Look up farm_id from farm_abbrev and ensure ownership
    result = await db.execute(
        select(Farm).where(
        Farm.farm_abbrev == crop.farm_abbrev,
        Farm.user_id == current_user.user_id,
        Farm.farm_is_active == True  # Optional: skip inactive farms
        )
    )
    farm = result.scalar_one_or_none()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found or not authorized.")

    # Check if the farm belongs to the current user
    if farm.user_id != current_user.user_id:
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

    # 4. Calculate crop age based on plantation_date and record_created_date
    if crop.plantation_date:
        plantation_date = crop.plantation_date
        record_created_date = datetime.utcnow().now()  # Or use the actual record creation date if available

        # Calculate the difference between plantation_date and the current date (or record creation date)
        delta = relativedelta(record_created_date, plantation_date)
        crop_yrs = round(delta.years + delta.months / 12, 2)

    # 5. Create new crop with the correct farm_id and method_id
    new_crop = CropDtl(
        farm_id=farm.farm_id,  # Use the farm_id from the lookup
        nfc_code=crop.nfc_code,
        farm_abbrev=crop.farm_abbrev,
        crop_type=crop.crop_type,
        crop_subtype=crop.crop_subtype,
        plantation_date=crop.plantation_date,
        method_id=method_id_to_use,
        crop_yrs=crop_yrs,  # Use the calculated crop years
        last_harvest_date=crop.last_harvest_date,
        crop_status=CropStatusEnum.active,
        crop_is_active=True
    )

    db.add(new_crop)
    await db.commit()
    await db.refresh(new_crop)

    return new_crop

# READ crop by NFC code
@router.get("/get/{nfc_code}", response_model=cropDtl.CropOut)
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
    crop_update: cropDtl.UpdateCropM,  # Use model that includes `other_method`
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crop = await get_crop_by_nfc_code(nfc_code, db)
    await verify_farm_ownership(crop, current_user, db)

    updates = crop_update.model_dump(exclude_unset=True)

    # Handle other_method first (create new method)
    if "other_method" in updates and updates["other_method"]:
        new_method = PlantMethod(
            method=updates["other_method"],
            other_method=updates["other_method"],
            record_created_by=current_user.user_id,
            record_status=MethodStatusEnum.active
        )
        db.add(new_method)
        await db.flush()  # Get new method ID
        updates["method_id"] = new_method.plant_method_id

    # Method authorization (skip admin methods)
    if "method_id" in updates:
        method_id = updates["method_id"]
        result = await db.execute(
            select(PlantMethod).where(PlantMethod.plant_method_id == method_id)
        )
        method = result.scalar_one_or_none()
        if not method:
            raise HTTPException(status_code=404, detail="Method not found.")
        if method.record_created_by is not None and method.record_created_by != current_user.user_id:
            raise HTTPException(status_code=403, detail="You are not authorized to use this method.")

    # Apply updates
    for key, value in updates.items():
        setattr(crop, key, value)

    # Recalculate crop_yrs if plantation_date was updated
    if "plantation_date" in updates:
        today = datetime.now().date()
        delta = relativedelta(today, crop.plantation_date)
        crop.crop_yrs = round(delta.years + delta.months / 12, 2)

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
