# CRUD route for expenses
# created: 29/4/2025

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from src.schemas.expense import CreateExpenses, UpdateExpenses, OutExpenses
from src.models.model import Expense, RecordStatusEnum, Farm, User 
from src.database import get_db
from src.dependencies import get_current_user 

router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"]
)

# Create Expense
@router.post("/create/", response_model=OutExpenses)
def create_expense(expense: CreateExpenses, db: Session = Depends(get_db)):
    db_expense = Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

# Get All Expenses (only for current user's farms)
@router.get("/readAll/", response_model=List[OutExpenses])
def get_user_expenses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Step 1: Find user's farms
    user_farms = db.query(Farm.farm_id).filter(Farm.user_id == current_user.user_id).all()
    farm_ids = [farm.farm_id for farm in user_farms]

    # Step 2: Find expenses that belong to user's farms
    expenses = db.query(Expense).filter(
        Expense.farm_id.in_(farm_ids),
        Expense.record_status == RecordStatusEnum.active
    ).all()

    return expenses

# Get Single Expense by ID
@router.get("/readOne/{expense_id}", response_model=OutExpenses)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Extra: make sure user owns the expense
    expense = db.query(Expense).join(Farm).filter(
        Expense.expenses_id == expense_id,
        Expense.record_status == RecordStatusEnum.active,
        Farm.user_id == current_user.user_id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

# Update Expense
@router.put("/{expense_id}", response_model=OutExpenses)
def update_expense(expense_id: int, update_data: UpdateExpenses, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.query(Expense).join(Farm).filter(
        Expense.expenses_id == expense_id,
        Expense.record_status == RecordStatusEnum.active,
        Farm.user_id == current_user.user_id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)
    
    db.commit()
    db.refresh(expense)
    return expense

# Soft Delete Expense
@router.delete("/del/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.query(Expense).join(Farm).filter(
        Expense.expenses_id == expense_id,
        Expense.record_status == RecordStatusEnum.active,
        Farm.user_id == current_user.user_id
    ).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    expense.record_status = RecordStatusEnum.deleted
    db.commit()
    return {"detail": "Expense soft deleted successfully"}
