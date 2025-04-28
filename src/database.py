# Author: Ng Yee Von
# Created date: 21/04/2025
# database.py establish connection to the PostgreSQL server

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres:Back%40dmin25@localhost/akaris_db"

# Async engine for PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)

# Create a session maker for database interaction
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base for model definitions
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session

