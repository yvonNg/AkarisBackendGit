import asyncio
from src.database import SessionLocal
from src.models.model import User  # adjust path if needed

async def insert_user():
    async with SessionLocal() as session:
        new_user = User(
            username="testuser",
            email="test@example.com",
            password="hashedpassword",
            phone_number="1234567890"
        )
        session.add(new_user)
        await session.commit()
        print("Registered Successfully!")

if __name__ == "__main__":
    asyncio.run(insert_user())
