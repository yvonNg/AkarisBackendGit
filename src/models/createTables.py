# Author: Ng Yee Von
# Created date: 21/04/2025
# createTables.py is to create tables having in model.py

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import engine, Base
from src.models.model import *

# Async function to create tables
async def create_tables():
    print("Connecting to the database...")
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Table creation complete.")

# Run the async function to create tables
async def main():
    await create_tables()

if __name__ == "__main__":
    asyncio.run(main())
