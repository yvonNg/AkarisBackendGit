# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for farm expect details

from pydantic import BaseModel, EmailStr, condecimal
from datetime import date, datetime
from typing import Optional, Annotated
from enum import Enum
from src.models.model import FarmExpectationEnum

DecimalPlace2 = Annotated[condecimal(max_digits=10, decimal_places=2), ...]

#---------Farm Expectation Schemas-----------

#Input from frontend
class FarmExpectCreate(BaseModel):
    expected_harvest_date: date
    expected_harvest_base_uom: DecimalPlace2
    expected_income: DecimalPlace2

class FarmExpectUpdate(BaseModel):
    expected_harvest_date: Optional[date] = None
    expected_harvest_base_uom: Optional[DecimalPlace2] = None
    expected_income: Optional[DecimalPlace2] = None

class FarmExpectOut(FarmExpectCreate):
    farm_expect_id: int
    farm_id: int
    farm_abbrev: str
    record_status: FarmExpectationEnum
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True