#!/usr/bin/env python3
"""
Main Entry Point for Financial Note Tagger
Assignment 1: Vertical Parsing & Tagging

Usage:
    python main.py <input_xml_path> <output_xml_path>
    
Example:
    python main.py data/note_1_input_v1_1.xml output/note_1_output.xml
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from xml_handler import XMLHandler


def main():
    """Main execution function"""
    
    print("="*80)
    print("Financial Note Tagger - Assignment 1")
    print("="*80)
    print()
    
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_xml> <output_xml>")
        print("\nExample:")
        print("  python main.py data/note_1_input_v1_1.xml output/note_1_output.xml")
        print()
        
        # Try to use default files if they exist
        input_file = "data/note_1_input_v1_1.xml"
        output_file = "output/note_1_output.xml"
        
        if os.path.exists(input_file):
            print(f"Using default input file: {input_file}")
        else:
            print(f"Error: Input file not found: {input_file}")
            sys.exit(1)
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    
    # Validate input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Process the file
    try:
        handler = XMLHandler()
        
        print(f"Extraction Mode: {handler.tagger.get_extraction_mode()}")
        print()
        
        handler.process_file(input_file, output_file)
        
        # Show statistics
        handler.tagger.print_stats()
        
        print()
        print("="*80)
        print("SUCCESS!")
        print("="*80)
        print(f"Input:  {input_file}")
        print(f"Output: {output_file}")
        
        # If expected output exists, compare
        expected_file = "data/note_1_expected_output_v1_1.xml"
        if os.path.exists(expected_file):
            print()
            print("Comparing with expected output...")
            handler.compare_with_expected(output_file, expected_file)
        
    except Exception as e:
        print()
        print("="*80)
        print("ERROR!")
        print("="*80)
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
