# Author: Ng Yee Von
# Created date: 29/04/2025
# CRUD routes for expense operations (uses JWT for user identity)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from src.models import model
from src.models.model import RecordStatusEnum, User, Expense, Farm
from src.schemas import expense
from src.database import get_db
from src.dependencies import get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])

# CREATE new expense
@router.post("/create/", response_model=expense.OutExpenses)
async def create_expense(
    expense_data: expense.CreateExpenses,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # current_user is the object returned by get_current_user
    print(f"Creating expense for user: {current_user.user_id}")

    # Check that the farm exists and belongs to the user
    farm = await db.execute(select(Farm).where(Farm.farm_id == expense_data.farm_id))
    farm_obj = farm.scalar_one_or_none()

    if not farm_obj:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    # Ensure the current user is associated with the farm
    if farm_obj.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not own this farm")

    # Create the new expense entry
    new_expense = Expense(
        farm_id=farm_obj.farm_id,
        category=expense_data.category,
        description=expense_data.description,
        amount=expense_data.amount,
        transaction_date=expense_data.transaction_date,
        record_status=RecordStatusEnum.active
    )

    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)

    return new_expense

# READ all expenses for the current user's farms (with pagination)
@router.get("/readAll/{farm_id}", response_model=list[expense.OutExpenses])
async def get_user_expenses(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0, limit: int = 100
):
    result = await db.execute(
        select(Expense).join(Farm).where(
            Farm.user_id == current_user.user_id,
            Farm.farm_id == farm_id,
            Expense.record_status == RecordStatusEnum.active
        ).offset(skip).limit(limit)
    )
    expenses = result.scalars().all()
    return expenses

# READ single expense by ID
@router.get("/readOne/{expense_id}", response_model=expense.OutExpenses)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Expense).join(Farm).where(
            Expense.expenses_id == expense_id,
            Expense.record_status == RecordStatusEnum.active,
            Farm.user_id == current_user.user_id
        )
    )
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

# UPDATE expense
@router.put("/{expense_id}", response_model=expense.OutExpenses)
async def update_expense(
    expense_id: int,
    update_data: expense.UpdateExpenses,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Expense).join(Farm).where(
            Expense.expenses_id == expense_id,
            Expense.record_status == RecordStatusEnum.active,
            Farm.user_id == current_user.user_id
        )
    )
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Update the expense fields
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)

    expense.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(expense)

    return expense

# DELETE (soft delete expense)
@router.delete("/del/{expense_id}")
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch the expense
    result = await db.execute(
        select(Expense).where(
            Expense.expenses_id == expense_id,
            Expense.record_status == RecordStatusEnum.active
        )
    )
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Verify that the farm owning this expense belongs to the current user
    farm_query = await db.execute(
        select(Farm).where(
            Farm.farm_id == expense.farm_id,
            Farm.user_id == current_user.user_id
        )
    )
    farm = farm_query.scalar_one_or_none()

    if not farm:
        raise HTTPException(status_code=403, detail="Access denied to this expense")

    # Perform soft delete
    expense.record_status = RecordStatusEnum.deleted
    expense.record_updated_date = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()

    return {"detail": "Expense soft deleted successfully"}
