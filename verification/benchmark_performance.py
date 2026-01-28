#!/usr/bin/env python3
"""
Performance Benchmark Script
Tests speed and scalability of the tagger
"""

import time
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xml_handler import XMLHandler


def benchmark_single_note(input_file, iterations=10):
    """
    Benchmark processing time for a single note
    
    Args:
        input_file: Path to input XML
        iterations: Number of times to run
    
    Returns:
        dict with timing statistics
    """
    handler = XMLHandler()
    times = []
    
    print("="*70)
    print(f"PERFORMANCE BENCHMARK - Single Note")
    print("="*70)
    print(f"Input: {input_file}")
    print(f"Iterations: {iterations}")
    print()
    
    print("Running benchmark...")
    
    for i in range(iterations):
        start = time.time()
        handler.process_file(input_file, f'/tmp/bench_output_{i}.xml')
        elapsed = time.time() - start
        times.append(elapsed)
        
        if i % 10 == 0:
            print(f"  Iteration {i+1}/{iterations}... {elapsed*1000:.2f}ms")
        
        # Cleanup
        if os.path.exists(f'/tmp/bench_output_{i}.xml'):
            os.remove(f'/tmp/bench_output_{i}.xml')
    
    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print()
    print("="*70)
    print("TIMING STATISTICS")
    print("="*70)
    print(f"Average Time: {avg_time*1000:.2f} ms")
    print(f"Min Time:     {min_time*1000:.2f} ms")
    print(f"Max Time:     {max_time*1000:.2f} ms")
    print()
    
    return {
        'average': avg_time,
        'min': min_time,
        'max': max_time,
        'times': times
    }


def benchmark_multiple_notes(input_file, num_notes_list=[10, 20, 30]):
    """
    Benchmark processing time for multiple notes
    
    Args:
        input_file: Path to input XML
        num_notes_list: List of note counts to test
    
    Returns:
        dict with scalability metrics
    """
    handler = XMLHandler()
    
    print("="*70)
    print("SCALABILITY BENCHMARK - Multiple Notes")
    print("="*70)
    print()
    
    results = {}
    
    for num_notes in num_notes_list:
        print(f"Processing {num_notes} notes...")
        
        start = time.time()
        
        for i in range(num_notes):
            output_file = f'/tmp/multi_bench_{i}.xml'
            handler.process_file(input_file, output_file)
            
            # Cleanup
            if os.path.exists(output_file):
                os.remove(output_file)
        
        elapsed = time.time() - start
        avg_per_note = elapsed / num_notes
        
        results[num_notes] = {
            'total_time': elapsed,
            'avg_per_note': avg_per_note,
            'notes_per_second': num_notes / elapsed
        }
        
        print(f"  Total Time: {elapsed:.2f}s")
        print(f"  Avg per Note: {avg_per_note*1000:.2f}ms")
        print(f"  Throughput: {results[num_notes]['notes_per_second']:.1f} notes/sec")
        print()
    
    return results


def print_scalability_report(results):
    """Print scalability analysis"""
    print("="*70)
    print("SCALABILITY ANALYSIS")
    print("="*70)
    print()
    
    print("Notes | Total Time | Avg/Note | Throughput")
    print("-"*70)
    
    for num_notes, data in sorted(results.items()):
        print(f"{num_notes:5d} | {data['total_time']:9.2f}s | "
              f"{data['avg_per_note']*1000:7.2f}ms | "
              f"{data['notes_per_second']:5.1f} notes/sec")
    
    print()
    
    # Check if meets requirements
    if 30 in results:
        time_30_notes = results[30]['total_time']
        avg_per_note = results[30]['avg_per_note']
        
        print("REQUIREMENTS CHECK:")
        print(f"  Time to process 30 notes: {time_30_notes:.2f}s")
        print(f"  Average per note: {avg_per_note*1000:.2f}ms")
        
        # Reasonable requirement: < 10 seconds for 30 notes
        if time_30_notes < 10:
            print(f"    PASS: Can process 30 notes in under 10 seconds")
        else:
            print(f"     WARNING: Takes > 10 seconds for 30 notes")
    
    print("="*70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_performance.py <input_xml>")
        print("\nExample (run from project root):")
        print("  python verification/benchmark_performance.py data/note_1_input_v1_1.xml")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    print()
    print("Starting Performance Benchmarks...")
    print()
    
    # Benchmark 1: Single note performance
    single_results = benchmark_single_note(input_file, iterations=50)
    
    print()
    
    # Benchmark 2: Multiple notes scalability
    multi_results = benchmark_multiple_notes(input_file, [10, 20, 30])
    
    print()
    
    # Print final report
    print_scalability_report(multi_results)
    
    print()
    print("Benchmark Complete!")
    print()


if __name__ == "__main__":
    main()
