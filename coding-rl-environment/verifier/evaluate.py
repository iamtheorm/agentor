import os
import sys
import hashlib
import subprocess

def hash_file(filepath):
    """Compute SHA256 of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

# Expected hashes for anti-tampering (hardcoded post-generation in a real harness)
# For this evaluation environment, we check that they haven't been modified since runner startup.
VERIFIER_DIR = os.path.dirname(os.path.abspath(__file__))
EXPECTED_HASHES = {}

def initialize_hashes():
    for f in os.listdir(VERIFIER_DIR):
        if f.startswith("test_") and f.endswith(".py"):
            EXPECTED_HASHES[f] = hash_file(os.path.join(VERIFIER_DIR, f))

def verify_integrity():
    """Ensure agent hasn't tampered with test files."""
    for f, expected_hash in EXPECTED_HASHES.items():
        current_hash = hash_file(os.path.join(VERIFIER_DIR, f))
        if current_hash != expected_hash:
            print(f"[CHEATING DETECTED] File {f} has been tampered with!")
            sys.exit(1)

def run_tests():
    print("Running evaluation suite...")
    
    # Run pytest, capturing output.
    # Note: In a real sandboxed RL environment, --network none is applied to the container.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", VERIFIER_DIR, "-v", "--disable-warnings"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
        
    if result.returncode == 0:
        print("\n[EVALUATION PASSED] All tests green.")
        sys.exit(0)
    else:
        print("\n[EVALUATION FAILED] Tests failed or race condition detected.")
        sys.exit(1)

if __name__ == "__main__":
    initialize_hashes() # In reality, these would be hardcoded in the runner image
    verify_integrity()
    run_tests()
