# Benchmark: Distributed Idempotency Race Condition

This document outlines the benchmarking schemas and theoretical results for evaluating top-tier LLM agents against this environment.

## Metrics Definition
- **Pass@1**: Percentage of times the agent successfully identifies and patches all three bugs (Race Condition, DB Isolation, Lock Leak) in a single attempt, passing all oracle state tests.
- **Pass@k**: Percentage of times the agent solves the environment within `k` rollout attempts (allowing for intermediate test failures and self-correction).
- **Stump Rate**: Percentage of runs where the agent exhausts the time limit or iteration budget without finding a valid solution.

## Simulated Results (N=100 episodes per model)

### GPT-4o
- **Pass@1**: 32%
- **Pass@5**: 68%
- **Stump Rate**: 21%
- **Analysis**: GPT-4o frequently identifies the check-then-set race condition and applies a Redis `SET NX` fix. However, it often misses the PostgreSQL transaction isolation bug (`SELECT FOR UPDATE`), leading to test failures in `test_oracle_db_state_after_race`. It usually self-corrects after seeing the oracle failure trace, resulting in a strong Pass@5.

### Claude 3.5 Sonnet
- **Pass@1**: 45%
- **Pass@5**: 76%
- **Stump Rate**: 12%
- **Analysis**: Claude 3.5 Sonnet exhibits excellent holistic reasoning across multiple files. It frequently patches both the Redis atomic issue and the DB isolation issue simultaneously. The primary cause of its stump rate is failing to properly implement the `try/finally` block to clear the lock leak, getting stuck modifying the test file (which triggers the cheating detector) rather than fixing the application logic.

## Run Log Trace Schema
An example JSON schema for recording rollout traces:
```json
{
  "episode_id": "ep_001",
  "model": "claude-3-5-sonnet",
  "result": "success",
  "iterations": 3,
  "time_elapsed_seconds": 340,
  "tool_calls": [
    {"tool": "bash_shell", "command": "grep -rn 'idemp' app/"},
    {"tool": "file_reader", "file": "app/core/idempotency.py"},
    {"tool": "file_writer", "file": "app/core/idempotency.py", "patch": "..."},
    {"tool": "bash_shell", "command": "python tests/verifier/evaluate.py"}
  ],
  "oracle_state_diff": {
    "expected_balance": 90.0,
    "actual_balance": 90.0
  }
}
```
