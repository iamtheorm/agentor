import pytest
import httpx
from app.main import app
from app.core.idempotency import redis_client

@pytest.mark.asyncio
async def test_error_handling_lock_leak():
    """
    Simulates a transaction failure (e.g., insufficient funds) and ensures 
    the idempotency lock is properly released so the user can retry later.
    """
    url = "http://localhost:8000/pay"
    headers = {"Idempotency-Key": "error_key_001"}
    
    # Request an absurd amount to trigger a 400 Insufficient Funds
    payload = {"user_id": "user_123", "amount": 999999.0}

    async with httpx.AsyncClient(app=app, base_url="http://localhost:8000") as client:
        response = await client.post("/pay", headers=headers, json=payload)
    
    assert response.status_code == 400
    
    # Check if lock was leaked in Redis
    is_locked = await redis_client.exists("idemp:error_key_001")
    assert not is_locked, "Lock Leak Detected: The idempotency lock was not released after an exception occurred!"
