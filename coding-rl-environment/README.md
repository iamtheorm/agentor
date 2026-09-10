# RL Evaluation Environment: Distributed Idempotency

## 📖 Overview
This repository provides a production-grade, highly rigorous Reinforcement Learning (RL) coding evaluation environment. It is designed to benchmark an AI agent's ability to solve complex, multi-file engineering problems rather than simple algorithmic puzzles.

Specifically, it presents a vulnerable Python FastAPI service backed by Redis and PostgreSQL. The service suffers from a severe **Distributed Idempotency Race Condition** and a **Database Transaction Isolation Flaw** (Write Skew).

### What it Does & Its Effects
When a client sends a payment request, the system uses an `Idempotency-Key` to ensure the payment isn't processed twice. 
However, due to a check-then-set race condition in the Redis caching layer and missing row-level locking in PostgreSQL, a sudden burst of concurrent requests (e.g., from network retries or malicious actors) will bypass the idempotency guard. 

**The Effect:** A single payment request sent concurrently will result in multiple deductions from the user's account and duplicate transaction records—a catastrophic failure in a real-world financial system. Furthermore, any failed transaction permanently leaks the idempotency lock, permanently preventing legitimate retries.

---

## 🏗 Engineering Design Document (EDD)

### 1. Capability Mapping
This environment specifically measures **Multi-file Implementation**, **Concurrency Logic**, and **API/Service Integration**. The agent is evaluated on its ability to trace stateful logic across non-contiguous files (`endpoints.py`, `idempotency.py`, `ledger.py`) and successfully reason about Distributed Race Conditions and Database Transaction Isolation Levels. 

### 2. Environment Logic (Stochasticity)
To ensure high fidelity while handling stochasticity (e.g., race conditions manifesting inconsistently due to CPU timing differences), the environment uses concurrent stress testing via `httpx.AsyncClient` with `asyncio.gather`. Furthermore, `idempotency.py` features an artificial `asyncio.sleep(0.01)` inside the critical section to forcibly widen the race window, guaranteeing the bug triggers 100% of the time on a vulnerable codebase during evaluation.

### 3. Oracle Strategy (How We Are Testing & Why)
The verifier does not rely on text grepping or just parsing the `HTTP 200/400` status codes of the application. An agent could easily "hack" the API to always return 200 without actually fixing the database issue. 
Instead, we utilize **Oracle Validation** by connecting directly to the underlying systems:
- `test_oracle_state.py` connects directly to PostgreSQL to assert the exact account balance. If the balance doesn't match the expected single deduction, the write skew is detected.
- It also connects directly to Redis to ensure `exists("idemp:*")` is absolutely zero after processing, ensuring no locks were leaked.
This perfectly distinguishes between the application merely "returning success" vs the actual underlying system state being correct.

### 4. Adversarial Analysis
Agents often attempt to "game" the grader by short-circuiting test execution, exfiltrating the solution, or hacking the test framework. 
- **Grader-Hacking / Test Tampering**: The `evaluate.py` script automatically hashes all test files upon launch. If an agent tampers with `test_functional.py` to always pass, the checksum validation immediately halts execution with a cheating flag.
- **Network Bypassing**: The monolithic container runs all dependent services (Redis, PostgreSQL, Pytest) locally, allowing the runner to launch the environment with strictly enforced `--network none`. The agent operates in an absolute vacuum and cannot `curl` or download a solution from external services.

---

## 🚀 How to Setup and Test

This environment is containerized as a monolith to ensure perfect reproducibility and to allow complete network isolation during testing. 

### Step 1: Build the Environment
```bash
docker build -f environment/Dockerfile -t rl-eval-idempotency .
```

### Step 2: The Negative Run (Verify the Bug)
Run the evaluator against the unpatched, buggy codebase. The tests are designed to execute 50 concurrent requests identically timed.
```bash
docker run --rm --network none rl-eval-idempotency python /app/verifier/evaluate.py
```
**Expected Output:** The tests will FAIL. You will see an `IntegrityError` (due to the race condition inserting duplicates) and an `AssertionError: Lock Leak Detected`.

### Step 3: Apply the Reference Patch
The solution requires implementing a Redis `SET NX` atomic lock, adding `SELECT FOR UPDATE` to the database query, and using a `try/finally` block to prevent lock leaks.
```bash
cd repo
patch -p1 < ../solution/reference_solution/patch.diff
cd ..
```

### Step 4: The Positive Run (Verify the Fix)
Rebuild the container with the patched code and run the evaluator again.
```bash
docker build -f environment/Dockerfile -t rl-eval-idempotency .
docker run --rm --network none rl-eval-idempotency python /app/verifier/evaluate.py
```
**Expected Output:** All tests will PASS, and the Oracle State checks will confirm the database and Redis cache are perfectly clean.
