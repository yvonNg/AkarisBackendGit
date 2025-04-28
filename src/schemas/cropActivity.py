# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for farming activity

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum
from src.models.model import CropActivityEnum

#---------Crop Activity Schemas-----------

class CreateActivity(BaseModel):
    nfc_code: str
    activity_name: CropActivityEnum
    other_activity: Optional[str] = None
    activity_details: Optional[str] = None
    record_created_by: int

class UpdateActiviy(BaseModel):
    activity_name: Optional[CropActivityEnum] = None
    other_activity: Optional[str] = None
    activity_details: Optional[str] = None

#get farm_id by relation in crop_id
class OutActivity(CreateActivity):
    activity_id: int
    farm_id: int
    crop_id: int
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None
    record_is_active: bool

    class Config:
        orm_mode = True