# Author: Ng Yee Von
# Created date: 25/04/2025
# Schemas file (to define how data should look when it comes in (from frontend) and goes out (to frontend))

from pydantic import BaseModel, condecimal
from datetime import datetime, date
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
    transaction_date: date

class UpdateExpenses(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[dp4] = None
    transaction_date: Optional[date] = None

class OutExpenses(CreateExpenses):
    expenses_id: int
    record_status: RecordStatusEnum
    record_created_date: datetime
    record_updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True