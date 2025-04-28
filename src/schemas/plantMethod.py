# src/schemas/plantMethod.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum
from src.models.model import MethodStatusEnum

#---------Planting Method Schemas-----------

class CreatePlantMethod(BaseModel): 
    method: str
    other_method: Optional[str] = None

class UpdatePlantMethod(BaseModel):
    method: Optional[str] = None
    other_method: Optional[str] = None

class OutPlantMethod(BaseModel):
    plant_method_id: int
    method: str
    other_method: Optional[str]
    record_created_by: Optional[int]
    record_status: MethodStatusEnum
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True
