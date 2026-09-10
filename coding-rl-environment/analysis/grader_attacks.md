# Grader Attack Vector Analysis

In a Reinforcement Learning environment, adversarial agents will attempt to bypass the intended solution space to achieve a positive reward (e.g., exit code 0). This document analyzes three attack vectors and the implemented countermeasures.

## Attack 1: Harness Short-Circuiting (Monkeypatching/Exit Hijacking)
**Attack:** The agent writes a script that imports the verifier, mocks out the failure conditions, or injects `sys.exit(0)` high up in the test suite execution.
**Defense:** The evaluation harness is launched from a monolithic Docker entrypoint (`runner.sh`). The verifier is executed in a fresh subprocess, and the agent does not control the entrypoint. The test directory is mounted read-only, preventing the agent from modifying the test files to return early. 

## Attack 2: External Exfiltration or Bypassing
**Attack:** The agent downloads a pre-written patch from a remote gist, or curls the test suite results to an external server to game the evaluation metrics.
**Defense:** The container is run with deterministic Network Isolation (`--network none`). Because all dependencies (PostgreSQL, Redis, Application) are internal to the monolithic container and communicate over loopback/sockets, the agent operates in an absolute vacuum.

## Attack 3: Test File Tampering (Checksum Defeat)
**Attack:** If the agent manages to gain root or write access to the `tests/verifier/` directory despite read-only mounts, it modifies `test_functional.py` to assert `True == True` instead of checking the race condition.
**Defense:** `evaluate.py` implements Checksum Validation. Before executing `pytest`, it computes the SHA256 hashes of all test files and compares them against hardcoded/expected hashes. If an agent modifies a test file, the verifier immediately exits with code 1 and outputs a `[CHEATING DETECTED]` flag.
