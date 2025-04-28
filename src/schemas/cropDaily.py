# Author: Ng Yee Von
# Created date: 25/04/2025
# Refined Schemas for CropDaily (Daily Crop Updates)

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.models.model import DailyCropStatusEnum, CropGrowingStageEnum

# --------- Daily Crop Schemas ---------

class CreateDailyCrop(BaseModel):
    nfc_code: str
    crop_stage: CropGrowingStageEnum
    stage_duration_day: int

class UpdateDailyCrop(BaseModel):
    crop_stage: Optional[CropGrowingStageEnum] = None
    stage_duration_day: Optional[int] = None

class OutDailyCrop(BaseModel):
    daily_id: int
    crop_id: int
    nfc_code: str
    crop_stage: CropGrowingStageEnum
    stage_duration_day: int
    crop_status: DailyCropStatusEnum
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True