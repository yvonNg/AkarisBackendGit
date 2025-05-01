# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for core crop details

from pydantic import BaseModel, condecimal
from datetime import datetime, date
from typing import Optional, Annotated
from enum import Enum
from src.models.model import CropStatusEnum, CropGrowingStageEnum

DecimalPlace2 = Annotated[condecimal(max_digits=10, decimal_places=2), ...]

#---------Crop Detail Schemas-----------

class CropBase(BaseModel):
    nfc_code: str
    farm_abbrev: str
    crop_type: str
    crop_subtype: str
    plantation_date: date
    method_id: int
    last_harvest_date: Optional[datetime] = None

# For Create API (only input fields)
class CreateCrop(CropBase):
    other_method: Optional[str] = None

# For Update API (partial update)
class UpdateCrop(BaseModel):
    method_id: Optional[int] = None
    crop_subtype: Optional[str] = None
    last_harvest_date: Optional[datetime] = None
    plantation_date: Optional[date] = None

class UpdateCropM(UpdateCrop):
    other_method: Optional[str] = None

# For Output (response model, includes extra fields from database)
class CropOut(CropBase):
    crop_id: int
    crop_yrs: DecimalPlace2
    crop_stage: Optional[CropGrowingStageEnum] = None
    record_created_date: datetime
    crop_modified_date: Optional[datetime] = None
    crop_status: CropStatusEnum
    crop_is_active: bool

    class Config:
        orm_mode = True 