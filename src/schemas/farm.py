# Author: Ng Yee Von
# Created date: 22/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for farm details

from pydantic import BaseModel, EmailStr, condecimal
from datetime import datetime
from typing import Optional, Annotated
from enum import Enum

DecimalPlace2 = Annotated[condecimal(max_digits=10, decimal_places=2), ...]
#---------Farm Schemas-----------

class FarmStatus(str, Enum):
    active ="active"
    inactive = "inactive"
    terminated = "terminated"

#Input from frontend

class FarmCreate(BaseModel):
    farm_abbrev: str
    crop_type: str
    farm_size: DecimalPlace2
    farm_location: str

class FarmCreateNUpdate(BaseModel):
    farm_abbrev: Optional[str] = None
    crop_type: Optional[str] = None
    farm_size: Optional[DecimalPlace2] = None
    farm_location: Optional[str] = None

class FarmOut(FarmCreate):
    farm_id: int
    user_id: int
    farm_status: FarmStatus
    farm_is_active: bool
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True