#!/usr/bin/env python3
"""
Comprehensive Verification Suite
Runs all verification checks and generates a compliance report

This script verifies:
1. Accuracy >= 99%
2. Determinism (consistency across runs)
3. Completeness (no missing tags)
4. Performance (scalability to 20-30 notes)

Run from project root:
    python verification/run_all_verifications.py
"""

import subprocess
import sys
import os
import time


def run_check(name, script, args, required=True):
    """
    Run a verification check
    
    Args:
        name: Name of the check
        script: Python script to run
        args: Arguments for the script
        required: Whether this check is required to pass
    
    Returns:
        tuple: (passed, output)
    """
    print(f"\n{'='*70}")
    print(f"CHECK: {name}")
    print(f"{'='*70}\n")
    
    cmd = ['python', script] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        passed = result.returncode == 0
        
        if passed:
            print(f"\n{name}: PASSED")
        else:
            if required:
                print(f"\n{name}: FAILED (REQUIRED)")
            else:
                print(f"\n{name}: FAILED (OPTIONAL)")
        
        return passed, result.stdout
        
    except subprocess.TimeoutExpired:
        print(f"\n{name}: TIMEOUT")
        return False, "Timeout"
    except Exception as e:
        print(f"\n{name}: ERROR - {e}")
        return False, str(e)


def main():
    """Run comprehensive verification suite"""
    
    # Change to project root directory (parent of verification folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print("="*70)
    print("COMPREHENSIVE VERIFICATION SUITE")
    print("Assignment 1: Financial Note Tagger")
    print("="*70)
    print(f"\nWorking directory: {os.getcwd()}")
    
    start_time = time.time()
    
    # Configuration - paths relative to project root
    input_file = 'data/note_1_input_v1_1.xml'
    expected_file = 'data/note_1_expected_output_v1_1.xml'
    generated_file = 'output/verification_test.xml'
    
    # Verification scripts - in verification folder
    verify_accuracy_script = 'verification/verify_accuracy.py'
    verify_determinism_script = 'verification/verify_determinism.py'
    verify_completeness_script = 'verification/verify_completeness.py'
    benchmark_script = 'verification/benchmark_performance.py'
    
    # Check prerequisites
    if not os.path.exists(input_file):
        print(f"\nError: Input file not found: {input_file}")
        sys.exit(1)
    
    if not os.path.exists(expected_file):
        print(f"\nError: Expected output file not found: {expected_file}")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Generate output for testing
    print(f"\n{'='*70}")
    print("SETUP: Generating output for verification")
    print(f"{'='*70}\n")
    
    result = subprocess.run(
        ['python', 'main.py', input_file, generated_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Error: Failed to generate output")
        print(result.stderr)
        sys.exit(1)
    
    print("Output generated successfully")
    
    # Track results
    checks = {
        'accuracy': False,
        'determinism': False,
        'completeness': False,
        'performance': False
    }
    
    # CHECK 1: Accuracy (REQUIRED)
    passed, _ = run_check(
        "Accuracy Verification (>= 99%)",
        verify_accuracy_script,
        [generated_file, expected_file],
        required=True
    )
    checks['accuracy'] = passed
    
    # CHECK 2: Determinism (REQUIRED)
    passed, _ = run_check(
        "Determinism Verification",
        verify_determinism_script,
        [input_file, '5'],  # Run 5 times
        required=True
    )
    checks['determinism'] = passed
    
    # CHECK 3: Completeness (REQUIRED)
    passed, _ = run_check(
        "Completeness Verification",
        verify_completeness_script,
        [generated_file, expected_file],
        required=True
    )
    checks['completeness'] = passed
    
    # CHECK 4: Performance (OPTIONAL but important)
    passed, _ = run_check(
        "Performance Benchmark",
        benchmark_script,
        [input_file],
        required=False
    )
    checks['performance'] = passed
    
    # FINAL REPORT
    elapsed = time.time() - start_time
    
    print(f"\n{'='*70}")
    print("FINAL VERIFICATION REPORT")
    print(f"{'='*70}\n")
    
    print("RESULTS SUMMARY:")
    print("-"*70)
    
    for check_name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"{status:10} | {check_name.upper()}")
    
    print("-"*70)
    
    # Overall status
    required_checks = ['accuracy', 'determinism', 'completeness']
    all_required_passed = all(checks[c] for c in required_checks)
    
    print()
    if all_required_passed:
        print("OVERALL STATUS: READY")
        print()
        print("All required criteria met:")
        print("  Accuracy >= 99%")
        print("  Deterministic output")
        print("  Complete tag coverage")
        if checks['performance']:
            print("  Efficient performance")
        print()
        print("Solution is ready for submission!")
        exit_code = 0
    else:
        print("OVERALL STATUS: NEEDS WORK")
        print()
        print("Failed checks:")
        for check_name in required_checks:
            if not checks[check_name]:
                print(f"  {check_name.upper()}")
        print()
        print("Please address failing checks before submission.")
        exit_code = 1
    
    print(f"\nTotal verification time: {elapsed:.2f} seconds")
    print("="*70)
    
    # Cleanup
    if os.path.exists(generated_file):
        os.remove(generated_file)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
