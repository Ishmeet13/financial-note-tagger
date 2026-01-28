#!/usr/bin/env python3
"""
Determinism Verification Script
Runs the tagger multiple times and verifies output is identical

Run from project root:
    python verification/verify_determinism.py data/note_1_input_v1_1.xml 5
"""

import subprocess
import hashlib
import sys
import os


def get_file_hash(filepath):
    """Calculate MD5 hash of a file"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def verify_determinism(input_file, num_runs=10):
    """
    Run tagger multiple times and verify outputs are identical
    
    Args:
        input_file: Input XML file path
        num_runs: Number of times to run (default: 10)
    
    Returns:
        bool: True if all outputs are identical
    """
    print("="*70)
    print(f"DETERMINISM VERIFICATION - {num_runs} RUNS")
    print("="*70)
    print()
    
    # Get the project root (parent of verification folder if run from there)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) if 'verification' in script_dir else os.getcwd()
    main_py = os.path.join(project_root, 'main.py')
    
    # Resolve input file path
    if not os.path.isabs(input_file):
        input_file = os.path.join(project_root, input_file)
    
    hashes = []
    outputs = []
    
    for i in range(num_runs):
        output_file = f'/tmp/determinism_test_run_{i}.xml'
        outputs.append(output_file)
        
        # Run the tagger
        result = subprocess.run(
            ['python', main_py, input_file, output_file],
            capture_output=True,
            text=True,
            cwd=project_root  # Run from project root
        )
        
        if result.returncode != 0:
            print(f"Run {i+1} failed with error")
            print(result.stderr)
            return False
        
        # Calculate hash
        file_hash = get_file_hash(output_file)
        hashes.append(file_hash)
        
        print(f"Run {i+1:2d}: {file_hash[:16]}... ", end="")
        
        if i == 0:
            print("(baseline)")
        elif file_hash == hashes[0]:
            print("Match")
        else:
            print("MISMATCH!")
    
    print()
    print("-"*70)
    
    # Check if all hashes are identical
    all_identical = len(set(hashes)) == 1
    
    if all_identical:
        print(f"   PASS: All {num_runs} runs produced IDENTICAL output")
        print(f"   Hash: {hashes[0]}")
        print()
        print("Determinism: GUARANTEED")
    else:
        print(f"   FAIL: Outputs differ across runs")
        print(f"   Unique hashes: {len(set(hashes))}")
        print()
        print("Determinism: NOT GUARANTEED")
    
    print("="*70)
    
    # Cleanup
    for output_file in outputs:
        if os.path.exists(output_file):
            os.remove(output_file)
    
    return all_identical


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_determinism.py <input_xml> [num_runs]")
        print("\nExample (run from project root):")
        print("  python verification/verify_determinism.py data/note_1_input_v1_1.xml 5")
        sys.exit(1)
    
    input_file = sys.argv[1]
    num_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    try:
        is_deterministic = verify_determinism(input_file, num_runs)
        sys.exit(0 if is_deterministic else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
