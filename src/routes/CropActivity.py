from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from src.models.model import Farm, CropDtl, CropActivity, User
from src.schemas import cropActivity
from src.dependencies import get_db, get_current_user

router = APIRouter(prefix="/activities", tags=["Activities"])

# Helper function to find farm and ensure it's active and owned by the user
async def get_farm_by_id(farm_id: int, current_user_id: int, db: AsyncSession) -> Farm:
    result = await db.execute(
        select(Farm).where(Farm.farm_id == farm_id)
    )
    farm = result.scalar_one_or_none()

    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or not authorized.")
    
    if farm.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this farm.")
    
    if not farm.farm_is_active:
        raise HTTPException(status_code=400, detail="Farm is inactive.")
    
    return farm

# Helper function to verify that the crop belongs to the same farm
async def verify_crop_belongs_to_farm(nfc_code: str, farm_id: int, db: AsyncSession):
    crop_result = await db.execute(
        select(CropDtl).where(CropDtl.nfc_code == nfc_code, CropDtl.farm_id == farm_id)
    )
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="NFC code does not belong to this farm.")
    return crop

# Helper function to create a new crop activity
async def create_new_activity(activity: cropActivity.CreateActivity, farm_id: int, current_user_id: int, db: AsyncSession) -> CropActivity:
    new_activity = CropActivity(
        farm_id=farm_id,
        nfc_code=activity.nfc_code,
        activity_name=activity.activity_name,
        other_activity=activity.other_activity,
        activity_details=activity.activity_details,
        record_created_by=current_user_id,
        record_created_date=datetime.now()
    )
    db.add(new_activity)
    await db.commit()
    await db.refresh(new_activity)
    return new_activity

# Helper function to get activity by id
async def get_activity_by_id(activity_id: int, db: AsyncSession) -> CropActivity:
    result = await db.execute(select(CropActivity).where(CropActivity.activity_id == activity_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

# Helper function to update activity details
async def update_activity_details(activity: CropActivity, activity_update: cropActivity.UpdateActivity, db: AsyncSession):
    for key, value in activity_update.model_dump(exclude_unset=True).items():
        setattr(activity, key, value)
    activity.record_updated_date = datetime.now()
    await db.commit()
    await db.refresh(activity)
    return activity

# CREATE new Activity
@router.post("/new", response_model=cropActivity.OutActivity)
async def create_activity(
    activity: cropActivity.CreateActivity,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    farm = await get_farm_by_id(activity.farm_id, current_user.user_id, db)

    if activity.nfc_code:
        await verify_crop_belongs_to_farm(activity.nfc_code, farm.farm_id, db)

    new_activity = await create_new_activity(activity, farm.farm_id, current_user.user_id, db)

    return new_activity

# READ activity by id
@router.get("/{activity_id}", response_model=cropActivity.OutActivity)
async def get_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    activity = await get_activity_by_id(activity_id, db)
    
    # Ensure that the user is the owner of the farm where this activity is linked
    farm = await get_farm_by_id(activity.farm_id, current_user.user_id, db)
    
    return activity

# UPDATE activity by id
@router.put("/update/{activity_id}", response_model=cropActivity.OutActivity)
async def update_activity(
    activity_id: int,
    activity_update: cropActivity.UpdateActivity,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    activity = await get_activity_by_id(activity_id, db)

    # Ensure the user owns the farm where this activity is linked
    farm = await get_farm_by_id(activity.farm_id, current_user.user_id, db)

    # Update the activity details
    updated_activity = await update_activity_details(activity, activity_update, db)

    return updated_activity

# DELETE (soft delete) activity by id
@router.delete("/delete/{activity_id}")
async def delete_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    activity = await get_activity_by_id(activity_id, db)

    # Ensure the user owns the farm where this activity is linked
    farm = await get_farm_by_id(activity.farm_id, current_user.user_id, db)

    # Soft delete the activity
    activity.record_is_active = False
    activity.record_updated_date = datetime.now()

    await db.commit()

    return {"message": "Activity deleted successfully."}
