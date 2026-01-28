#!/usr/bin/env python3
"""
Completeness Verification Script
Checks for missing tags compared to expected output
"""

import xml.etree.ElementTree as ET
from collections import Counter
import sys


def verify_completeness(generated_xml, expected_xml):
    """
    Verify no tags are missing compared to expected output
    
    Returns:
        dict with completeness metrics
    """
    # Parse both files
    gen_tree = ET.parse(generated_xml)
    exp_tree = ET.parse(expected_xml)
    
    # Extract all tags with their text content
    def extract_tags_with_content(tree):
        tags = []
        for elem in tree.iter('Tag'):
            tag_id = elem.get('id')
            if tag_id and tag_id not in [
                'NatureOfOperationsAndGoingConcernNote',
                'NatureOfOperationsAndGoingConcernHeader',
                'DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities',
                'DescriptionOfUncertaintiesOfEntitysAbilityToContinueAsGoingConcern'
            ]:  # Exclude structural tags
                text = elem.text or ''
                tags.append((tag_id, text.strip()))
        return tags
    
    gen_tags = extract_tags_with_content(gen_tree)
    exp_tags = extract_tags_with_content(exp_tree)
    
    print("="*70)
    print("COMPLETENESS VERIFICATION REPORT")
    print("="*70)
    print()
    
    # Count by tag type
    gen_counter = Counter([tag_id for tag_id, _ in gen_tags])
    exp_counter = Counter([tag_id for tag_id, _ in exp_tags])
    
    # Check for missing tags
    all_tag_types = set(exp_counter.keys())
    missing_tags = {}
    extra_tags = {}
    
    print("Tag Type Completeness:")
    print("-"*70)
    
    for tag_type in sorted(all_tag_types):
        exp_count = exp_counter[tag_type]
        gen_count = gen_counter[tag_type]
        
        if gen_count < exp_count:
            missing = exp_count - gen_count
            missing_tags[tag_type] = missing
            print(f"  {tag_type[:50]}")
            print(f"   Expected: {exp_count}, Generated: {gen_count}, Missing: {missing}")
        elif gen_count > exp_count:
            extra = gen_count - exp_count
            extra_tags[tag_type] = extra
            print(f"   {tag_type[:50]}")
            print(f"   Expected: {exp_count}, Generated: {gen_count}, Extra: {extra}")
        else:
            print(f"   {tag_type[:50]}")
            print(f"   Expected: {exp_count}, Generated: {gen_count}")
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total Expected Tags: {len(exp_tags)}")
    print(f"Total Generated Tags: {len(gen_tags)}")
    print(f"Missing Tags: {sum(missing_tags.values())}")
    print(f"Extra Tags: {sum(extra_tags.values())}")
    print()
    
    # Completeness percentage
    if len(exp_tags) > 0:
        completeness = (min(len(gen_tags), len(exp_tags)) / len(exp_tags)) * 100
    else:
        completeness = 100.0
    
    print(f"Completeness: {completeness:.1f}%")
    print()
    
    # Pass/Fail
    if not missing_tags and not extra_tags:
        print(" PASS: No missing or extra tags")
        print("Completeness: 100%")
        status = "PASS"
    else:
        if missing_tags:
            print(f" FAIL: {sum(missing_tags.values())} missing tags")
        if extra_tags:
            print(f" WARNING: {sum(extra_tags.values())} extra tags")
        status = "FAIL" if missing_tags else "WARNING"
    
    print("="*70)
    
    return {
        'expected_count': len(exp_tags),
        'generated_count': len(gen_tags),
        'missing': missing_tags,
        'extra': extra_tags,
        'completeness': completeness,
        'status': status
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python verify_completeness.py <generated_xml> <expected_xml>")
        sys.exit(1)
    
    generated = sys.argv[1]
    expected = sys.argv[2]
    
    try:
        results = verify_completeness(generated, expected)
        sys.exit(0 if results['status'] == 'PASS' else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
