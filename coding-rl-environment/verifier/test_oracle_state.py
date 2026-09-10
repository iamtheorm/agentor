import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.models.transaction import Account, Transaction
from app.core.idempotency import redis_client

@pytest.mark.asyncio
async def test_oracle_db_state_after_race():
    """
    Verifies that the database state is perfectly consistent after the functional tests run.
    Bypasses the application layer and checks the actual DB and Redis state.
    """
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Check Account balance
        result = await session.execute(select(Account).where(Account.user_id == "user_123"))
        account = result.scalars().first()
        
        # Initial was 100, we subtracted 10. Exactly one transaction should have succeeded.
        assert account.balance == 90.0, f"Oracle Error: Account balance is {account.balance}, expected 90.0. Write skew or double spend detected."
        
        # Check Transaction table
        result = await session.execute(select(Transaction).where(Transaction.idempotency_key == "race_key_001"))
        transactions = result.scalars().all()
        
        assert len(transactions) == 1, f"Oracle Error: Found {len(transactions)} transactions in DB. Expected exactly 1."

@pytest.mark.asyncio
async def test_oracle_redis_lock_released():
    """
    Oracle check to ensure no locks are leaked in Redis.
    """
    keys = await redis_client.keys("idemp:*")
    # By the end of processing, all locks should be deleted
    assert len(keys) == 0, f"Oracle Error: Found dangling idempotency locks in Redis: {keys}"
