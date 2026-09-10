from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transaction import Account, Transaction, TransactionStatus
from fastapi import HTTPException
import asyncio

async def process_payment(session: AsyncSession, user_id: str, amount: float, idempotency_key: str):
    # FIX: Use SELECT ... FOR UPDATE to lock the row
    result = await session.execute(select(Account).where(Account.user_id == user_id).with_for_update())
    account = result.scalars().first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # BUG: We are missing proper transaction isolation or row-level locking (SELECT FOR UPDATE)
    # Under high load, concurrent read of balance can result in write skew / double spend if
    # the idempotency lock fails.
    
    if account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Simulate processing time
    await asyncio.sleep(0.05)
    
    # Deduct balance
    account.balance -= amount
    
    # Record transaction
    transaction = Transaction(
        idempotency_key=idempotency_key,
        account_id=account.id,
        amount=amount,
        status=TransactionStatus.COMPLETED
    )
    
    session.add(transaction)
    await session.commit()
    
    return transaction
