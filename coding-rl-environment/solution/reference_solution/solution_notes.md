# Reference Solution Notes

This document explains the fixes applied in `patch.diff` to resolve the idempotency race condition and related bugs.

## 1. Idempotency Race Condition (`app/core/idempotency.py`)
**The Bug:** The original code used a check-then-set pattern:
```python
exists = await self.client.exists(...)
if exists: return False
await self.client.set(...)
```
This is not atomic. Multiple concurrent requests can pass the `exists` check before any of them reaches the `set` command.

**The Fix:** We replaced this with a single atomic Redis command `SET NX` (Not eXists). This guarantees that only the first request to execute the command will succeed in setting the key, and all subsequent concurrent requests will immediately fail.

## 2. Database Transaction Isolation (`app/services/ledger.py`)
**The Bug:** The original code read the account balance and then updated it without taking an exclusive lock. This can lead to a write skew if the idempotency lock fails.

**The Fix:** We added `.with_for_update()` to the SQLAlchemy query. This utilizes PostgreSQL's `SELECT ... FOR UPDATE` row-level locking, ensuring that no other transaction can modify (or even read, depending on isolation level) this row until the current transaction completes.

## 3. Lock Leak Error Handling (`app/api/endpoints.py`)
**The Bug:** The idempotency lock was only released at the end of the successful path. If `process_payment` raised an exception (like HTTP 400 Insufficient Funds), the release code was bypassed, leaving the key locked in Redis until its TTL expired.

**The Fix:** We wrapped the `process_payment` call in a `try...finally` block. This ensures that `release_lock` is always called, properly clearing the idempotency state regardless of whether the transaction succeeded or failed.
