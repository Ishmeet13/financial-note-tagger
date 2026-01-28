#!/usr/bin/env python3
"""
Accuracy Verification Script
Compares generated output with expected output and calculates accuracy metrics
"""

import xml.etree.ElementTree as ET
from collections import Counter
import sys


def calculate_accuracy(generated_xml, expected_xml):
    """
    Calculate tag accuracy metrics
    
    Returns:
        dict with accuracy metrics
    """
    # Parse both files
    gen_tree = ET.parse(generated_xml)
    exp_tree = ET.parse(expected_xml)
    
    # Extract all tags
    gen_tags = [e.get('id') for e in gen_tree.iter('Tag') if e.get('id')]
    exp_tags = [e.get('id') for e in exp_tree.iter('Tag') if e.get('id')]
    
    # Count occurrences
    gen_counter = Counter(gen_tags)
    exp_counter = Counter(exp_tags)
    
    # Calculate metrics
    all_tag_types = set(gen_tags + exp_tags)
    
    correct_counts = 0
    total_expected = 0
    
    results = {
        'tag_types': {},
        'overall': {}
    }
    
    print("="*70)
    print("ACCURACY VERIFICATION REPORT")
    print("="*70)
    print()
    
    # Per-tag-type accuracy
    print("Tag-by-Tag Accuracy:")
    print("-"*70)
    
    for tag_type in sorted(all_tag_types):
        gen_count = gen_counter[tag_type]
        exp_count = exp_counter[tag_type]
        
        if exp_count > 0:
            # Calculate accuracy for this tag type
            correct = min(gen_count, exp_count)
            accuracy = (correct / exp_count) * 100
            
            correct_counts += correct
            total_expected += exp_count
            
            status = "Approved" if gen_count == exp_count else "Not Approved"
            print(f"{status} {tag_type[:50]}")
            print(f"   Expected: {exp_count}, Generated: {gen_count}, Accuracy: {accuracy:.1f}%")
            
            results['tag_types'][tag_type] = {
                'expected': exp_count,
                'generated': gen_count,
                'accuracy': accuracy
            }
    
    # Overall accuracy
    overall_accuracy = (correct_counts / total_expected * 100) if total_expected > 0 else 0
    
    print()
    print("="*70)
    print("OVERALL ACCURACY METRICS")
    print("="*70)
    print(f"Total Expected Tags: {total_expected}")
    print(f"Total Generated Tags: {len(gen_tags)}")
    print(f"Correct Tags: {correct_counts}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    print()
    
    # Pass/Fail criteria
    if overall_accuracy >= 99.0:
        print("  PASS: Accuracy >= 99%")
        status = "PASS"
    else:
        print(f"  FAIL: Accuracy {overall_accuracy:.2f}% < 99%")
        status = "FAIL"
    
    print("="*70)
    
    results['overall'] = {
        'total_expected': total_expected,
        'total_generated': len(gen_tags),
        'correct': correct_counts,
        'accuracy': overall_accuracy,
        'status': status
    }
    
    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: python verify_accuracy.py <generated_xml> <expected_xml>")
        sys.exit(1)
    
    generated = sys.argv[1]
    expected = sys.argv[2]
    
    try:
        results = calculate_accuracy(generated, expected)
        sys.exit(0 if results['overall']['status'] == 'PASS' else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
