# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format of planting method

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum
from src.models.model import MethodStatusEnum

#---------Planting Method Schemas-----------

class CreatePlantMethod(BaseModel): 
    method: str
    other_method: Optional[str] = None
    record_created_by: int

class UpdatePlantMethod(BaseModel):
    method: Optional[str] = None
    other_method: Optional[str] = None

class OutPlantMethod(CreatePlantMethod):
    plant_method_id: int
    record_status: MethodStatusEnum
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True