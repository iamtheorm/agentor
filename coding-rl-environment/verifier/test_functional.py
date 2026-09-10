import pytest
import asyncio
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_race_condition_concurrency():
    """
    Sends multiple identical requests simultaneously to expose the check-then-set race condition.
    If the race condition exists, multiple requests will return 'success' instead of just one.
    """
    url = "http://localhost:8000/pay"
    headers = {"Idempotency-Key": "race_key_001"}
    payload = {"user_id": "user_123", "amount": 10.0}

    # Simulate 50 concurrent requests identically timed
    async with httpx.AsyncClient(app=app, base_url="http://localhost:8000") as client:
        tasks = [
            client.post("/pay", headers=headers, json=payload)
            for _ in range(50)
        ]
        
        responses = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in responses if r.json().get("status") == "success")
    
    # Assert exactly 1 success, and 49 'processing_or_completed'
    assert success_count == 1, f"Expected exactly 1 success, but got {success_count}. Race condition detected!"
