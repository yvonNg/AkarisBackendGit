# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for core crop details

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum
from src.models.model import CropStatusEnum, CropGrowingStageEnum

#---------Crop Detail Schemas-----------

class CreateCrop(BaseModel):
    farm_id: int
    nfc_code:str
    farm_abbrev: str
    crop_type: str
    crop_subtype: str
    plantation_date: datetime
    method_id: int
    crop_yrs: int
    last_harvest_date: Optional[datetime] = None

class UpdateCrop(BaseModel):
    crop_subtype: Optional[str] = None
    crop_yrs: Optional[int] = None
    last_harvest_date: Optional[datetime] = None

class CropOut(CreateCrop):
    crop_id: int
    crop_stage: Optional[CropGrowingStageEnum] = None
    rrecord_created_date: datetime
    crop_modified_date: Optional[datetime] = None
    crop_status: CropStatusEnum
    crop_is_active: bool

    class Config:
        orm_mode = True