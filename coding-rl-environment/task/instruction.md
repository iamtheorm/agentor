# Task Instruction

You are tasked with fixing a severe race condition in our distributed payment ledger system.

## Background
Our FastAPI service processes financial transactions. To ensure a payment is not processed twice (e.g., if a client retries a request due to a network timeout), we rely on an `Idempotency-Key` header provided by the client. We use Redis to lock and check these keys. Once a key is validated, the transaction is inserted into a PostgreSQL database.

## The Problem
We are observing double-spending and duplicated transactions in production during high-concurrency spikes. When a client sends multiple identical requests within a very tight window (e.g., 10-50ms), the system occasionally processes the transaction twice.

Additionally, when a database transaction fails (e.g., due to a constraint violation), the idempotency lock in Redis is not always released correctly, permanently blocking future legitimate retries of that key.

## Your Objective
1. **Fix the Idempotency Race Condition**: The current Redis implementation in `app/core/idempotency.py` has a non-atomic check-then-set vulnerability. You must implement an atomic acquisition mechanism (e.g., using a Lua script or proper `SET NX`).
2. **Fix the Database Transaction Isolation**: The ledger logic in `app/services/ledger.py` may be suffering from read phenomena under high concurrency. Ensure the correct isolation level is used to prevent phantom reads or write skews.
3. **Fix the Error Handling Leak**: The transaction model and lifecycle in `app/models/transaction.py` or the API endpoint does not properly clear the idempotency lock on failed transactions. Ensure proper `try/finally` patterns so locks don't leak.

## Constraints
- Do not modify the existing tests. A test suite is provided in `tests/verifier/` to validate your solution.
- The environment uses PostgreSQL and Redis.
- You must ensure your fix does not introduce performance bottlenecks (e.g., do not use long-lived global locks).

Good luck!
