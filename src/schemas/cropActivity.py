# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# This file is for farming activities

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --------- Crop Activity Schemas -----------

class CreateActivity(BaseModel):
    farm_id: int                      
    nfc_code: Optional[str] = None     
    activity_name: str
    other_activity: Optional[str] = None
    activity_details: Optional[str] = None
    record_created_by: int            

class UpdateActivity(BaseModel):        
    activity_name: Optional[str] = None
    other_activity: Optional[str] = None
    activity_details: Optional[str] = None

class OutActivity(CreateActivity):
    activity_id: int
    crop_id: Optional[int] = None        
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None
    record_is_active: bool

    class Config:
        orm_mode = True
