# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))
# this file holding format for expenses

from pydantic import BaseModel, condecimal
from datetime import datetime
from typing import Optional, Annotated
from enum import Enum
from src.models.model import RecordStatusEnum

dp4 = Annotated[condecimal(max_digits=10, decimal_places=4), ...]

#---------Expenses Schemas-----------

class CreateExpenses(BaseModel):
    farm_id: int
    category: str
    description: Optional[str] = None
    amount: dp4
    transaction_date: datetime

class UpdateExpenses(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[dp4] = None
    transaction_date: Optional[datetime] = None

#get farm_id by relation in crop_id
class OutExpenses(CreateExpenses):
    expenses_id: int
    record_status: RecordStatusEnum
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True