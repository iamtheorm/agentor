import asyncio
from app.core.database import engine, Base
from app.models.transaction import Account
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

async def init_models():
    async with engine.begin() as conn:
        # Drop and recreate tables for clean state
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def seed_data():
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        # Create a test account with $100
        test_account = Account(user_id="user_123", balance=100.0)
        session.add(test_account)
        await session.commit()

async def main():
    await init_models()
    await seed_data()
    print("Database initialized and seeded.")

if __name__ == "__main__":
    asyncio.run(main())
