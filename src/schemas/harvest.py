# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for harvest table

from pydantic import BaseModel, condecimal
from datetime import datetime
from typing import Optional, Annotated
from enum import Enum
from src.models.model import HarvestQualityEnum, HarvestUnitEnum, RecordStatusEnum

dp4 = Annotated[condecimal(max_digits=10, decimal_places=4), ...]

#---------Harvest Schemas-----------

class CreateHarvest(BaseModel):
    #farm_id: int
    nfc_code: str
    quantity: dp4
    harvest_unit: HarvestUnitEnum
    estimated_kg: Optional[dp4] = None
    harvest_avg_quality: HarvestQualityEnum
    earn: dp4
    harvest_date: datetime  

class UpdateHarvest(BaseModel):
    quantity: Optional[dp4] = None
    harvest_unit: Optional[HarvestUnitEnum] = None
    estimated_kg: Optional[dp4] = None
    harvest_avg_quality: Optional[HarvestQualityEnum] = None
    earn: Optional[dp4] = None
    harvest_date: Optional[datetime] = None

#get farm_id by relation in crop_id
class OutHarvest(CreateHarvest):
    harvest_id: int
    crop_id: int
    farm_id: int
    record_status: RecordStatusEnum
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True