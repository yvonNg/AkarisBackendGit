from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database import get_db
from src.dependencies import get_current_user
from typing import List
from src.models.model import MethodStatusEnum, PlantMethod, User
from src.schemas.plantMethod import OutPlantMethod

# Define the router for methods (separate from crops)
router = APIRouter(prefix="/methods", tags=["Methods"])

@router.get("/", response_model=List[OutPlantMethod])  # Adjusted to "/"
async def get_available_methods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Query to get all active methods that are either global or created by the current user
    query = select(PlantMethod).where(
        (PlantMethod.record_status == MethodStatusEnum.active) & 
        ((PlantMethod.record_created_by == None) | (PlantMethod.record_created_by == current_user.user_id))
    ).order_by(PlantMethod.method)

    result = await db.execute(query)
    methods = result.scalars().all()

    return methods
