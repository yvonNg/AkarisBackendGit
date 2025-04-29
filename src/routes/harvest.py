from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.dependencies import get_current_user
from src.models.model import Harvest, CropDtl, Farm, RecordStatusEnum
from src.schemas.harvest import CreateHarvest, UpdateHarvest, OutHarvest
from src.models.model import User

router = APIRouter(prefix="/harvest", tags=["Harvest"])

# ---------- Utility ----------
def update_crop_last_harvest_date(db: Session, crop_id: int):
    """Recalculate and update the last_harvest_date for a given crop."""
    latest_harvest = db.query(Harvest).filter(
        Harvest.crop_id == crop_id,
        Harvest.record_status == RecordStatusEnum.active
    ).order_by(Harvest.harvest_date.desc()).first()

    crop = db.query(CropDtl).filter(CropDtl.crop_id == crop_id).first()
    crop.last_harvest_date = latest_harvest.harvest_date if latest_harvest else None
    db.commit()

# ---------- Create ----------
@router.post("/", response_model=OutHarvest)
def create_harvest(
    data: CreateHarvest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    crop = db.query(CropDtl).join(Farm).filter(
        CropDtl.nfc_code == data.nfc_code,
        CropDtl.record_status == RecordStatusEnum.active,
        Farm.user_id == current_user.user_id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found or not owned by user")

    new_harvest = Harvest(
        crop_id=crop.crop_id,
        nfc_code=data.nfc_code,
        quantity=data.quantity,
        harvest_unit=data.harvest_unit,
        estimated_kg=data.estimated_kg,
        harvest_avg_quality=data.harvest_avg_quality,
        earn=data.earn,
        harvest_date=data.harvest_date
    )

    db.add(new_harvest)

    if not crop.last_harvest_date or data.harvest_date > crop.last_harvest_date:
        crop.last_harvest_date = data.harvest_date

    db.commit()
    db.refresh(new_harvest)
    return new_harvest

# ---------- Read ----------
@router.get("/", response_model=List[OutHarvest])
def get_user_harvests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    harvests = db.query(Harvest).join(CropDtl).join(Farm).filter(
        Farm.user_id == current_user.user_id,
        Harvest.record_status == RecordStatusEnum.active
    ).all()
    return harvests

# ---------- Update ----------
@router.put("/{harvest_id}", response_model=OutHarvest)
def update_harvest(
    harvest_id: int,
    update_data: UpdateHarvest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    harvest = db.query(Harvest).join(CropDtl).join(Farm).filter(
        Harvest.harvest_id == harvest_id,
        Harvest.record_status == RecordStatusEnum.active,
        Farm.user_id == current_user.user_id
    ).first()

    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(harvest, key, value)

    db.commit()
    db.refresh(harvest)

    # If harvest_date is changed, recalculate crop's latest harvest
    if "harvest_date" in update_data.model_fields_set:
        update_crop_last_harvest_date(db, harvest.crop_id)

    return harvest

# ---------- Delete ----------
@router.delete("/{nfc_code}", response_model=dict)
def soft_delete_harvest_by_nfc(
    nfc_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    harvest = db.query(Harvest).join(CropDtl).join(Farm).filter(
        Harvest.nfc_code == nfc_code,
        Harvest.record_status == RecordStatusEnum.active,
        Farm.user_id == current_user.user_id
    ).first()

    if not harvest:
        raise HTTPException(status_code=404, detail="Harvest not found")

    crop = db.query(CropDtl).filter(CropDtl.crop_id == harvest.crop_id).first()
    should_update = crop.last_harvest_date == harvest.harvest_date

    harvest.record_status = RecordStatusEnum.deleted
    db.commit()

    if should_update:
        update_crop_last_harvest_date(db, harvest.crop_id)

    return {"message": "Harvest deleted successfully"}
