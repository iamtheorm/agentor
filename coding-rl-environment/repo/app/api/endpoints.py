from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.idempotency import idempotency_manager
from app.services.ledger import process_payment
from pydantic import BaseModel

router = APIRouter()

class PaymentRequest(BaseModel):
    user_id: str
    amount: float

@router.post("/pay")
async def make_payment(
    request: PaymentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db)
):
    # Acquire lock
    locked = await idempotency_manager.acquire_lock(idempotency_key)
    if not locked:
        return {"status": "processing_or_completed"}

    # BUG: If `process_payment` raises an exception (e.g., HTTP 400 for insufficient funds),
    # the lock is never released because there is no try/finally block. 
    # This leads to a permanent lock for this idempotency_key if an error occurs!
    
    try:
        transaction = await process_payment(db, request.user_id, request.amount, idempotency_key)
    finally:
        # Always clear the lock when done, whether successful or failed,
        # so the transaction can be retried if it failed, or idempotency state can be updated correctly
        await idempotency_manager.release_lock(idempotency_key)
    
    return {"status": "success", "transaction_id": transaction.id}
