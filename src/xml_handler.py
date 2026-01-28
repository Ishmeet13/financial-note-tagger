"""
XML Handler Module
Handles parsing input XML and generating output XML in the required format
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict
from tagger import FinancialNoteTagger
from config import TAG_IDS


class XMLHandler:
    """
    Handles XML parsing and generation for financial notes
    """
    
    def __init__(self):
        self.tagger = FinancialNoteTagger()
    
    def parse_input_xml(self, filepath: str) -> Dict:
        """
        Parse the input XML file and extract paragraphs
        
        Returns:
            Dict with note info and paragraphs
        """
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Extract note metadata
        note_info = {
            'start_block': root.get('start_block'),
            'end_block': root.get('end_block'),
            'paragraphs': []
        }
        
        # Extract all paragraphs
        for para in root.findall('paragraph'):
            note_info['paragraphs'].append({
                'text': para.text,
                'block_index': para.get('block_index')
            })
        
        return note_info
    
    def generate_output_xml(self, note_info: Dict) -> ET.Element:
        """
        Generate the output XML structure with tagged entities
        
        Args:
            note_info: Dict containing paragraphs and metadata
            
        Returns:
            XML Element tree
        """
        # Create root element
        root = ET.Element('Tag', {'id': TAG_IDS['note_root']})
        note = ET.SubElement(root, 'note')
        
        # Detect subsections
        subsections = self.tagger.detect_subsections(note_info['paragraphs'])
        
        # Process each subsection
        for subsection in subsections:
            # Create subsection tag
            section_tag = ET.SubElement(note, 'Tag', {'id': subsection['tag_id']})
            
            # Check if we should skip tagging for this subsection (e.g., headers)
            skip_tagging = subsection.get('skip_tagging', False)
            
            # Process each paragraph in the subsection
            for para in subsection['paragraphs']:
                # Tag the paragraph text (unless skip_tagging is True)
                if skip_tagging:
                    tagged_text = para['text']  # Don't tag headers
                else:
                    tagged_text = self.tagger.tag_paragraph(para['text'])
                
                # Create paragraph element
                para_elem = ET.SubElement(
                    section_tag, 
                    'paragraph', 
                    {'block_index': para['block_index']}
                )
                
                # Parse the tagged text to properly handle nested tags
                # We need to manually build the element with mixed content
                self._set_paragraph_content(para_elem, tagged_text)
        
        return root
    
    def _set_paragraph_content(self, para_elem: ET.Element, tagged_text: str):
        """
        Set paragraph content with proper handling of nested Tag elements
        
        This is tricky because we need to handle mixed content (text + tags)
        """
        # Parse the tagged text
        # Split by <Tag> and </Tag>
        parts = []
        current_pos = 0
        
        while True:
            # Find next <Tag>
            tag_start = tagged_text.find('<Tag id="', current_pos)
            
            if tag_start == -1:
                # No more tags, add remaining text
                if current_pos < len(tagged_text):
                    parts.append(('text', tagged_text[current_pos:]))
                break
            
            # Add text before tag
            if tag_start > current_pos:
                parts.append(('text', tagged_text[current_pos:tag_start]))
            
            # Find end of opening tag
            tag_open_end = tagged_text.find('>', tag_start)
            if tag_open_end == -1:
                break
            
            # Extract tag_id
            tag_id_start = tag_start + 9  # len('<Tag id="')
            tag_id_end = tagged_text.find('"', tag_id_start)
            tag_id = tagged_text[tag_id_start:tag_id_end]
            
            # Find closing tag
            tag_close = tagged_text.find('</Tag>', tag_open_end)
            if tag_close == -1:
                break
            
            # Extract tag content
            tag_content = tagged_text[tag_open_end + 1:tag_close]
            
            parts.append(('tag', tag_id, tag_content))
            
            current_pos = tag_close + 6  # len('</Tag>')
        
        # Build the element
        if not parts:
            para_elem.text = tagged_text
            return
        
        # Set initial text
        if parts and parts[0][0] == 'text':
            para_elem.text = parts[0][1]
            parts = parts[1:]
        else:
            para_elem.text = ''
        
        # Add tags and text
        last_elem = None
        for part in parts:
            if part[0] == 'tag':
                # Create Tag subelement
                tag_elem = ET.SubElement(para_elem, 'Tag', {'id': part[1]})
                tag_elem.text = part[2]
                tag_elem.tail = ''
                last_elem = tag_elem
            elif part[0] == 'text':
                # Add as tail of previous tag
                if last_elem is not None:
                    last_elem.tail = part[1]
                else:
                    # Should not happen, but handle gracefully
                    if para_elem.text:
                        para_elem.text += part[1]
                    else:
                        para_elem.text = part[1]
    
    def prettify_xml(self, elem: ET.Element) -> str:
        """
        Return a pretty-printed XML string
        """
        rough_string = ET.tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def process_file(self, input_path: str, output_path: str):
        """
        Main processing pipeline: input XML -> tagged output XML
        
        Args:
            input_path: Path to input XML file
            output_path: Path to save output XML file
        """
        print(f"Processing: {input_path}")
        
        # Parse input
        note_info = self.parse_input_xml(input_path)
        print(f"  Found {len(note_info['paragraphs'])} paragraphs")
        
        # Generate tagged output
        output_root = self.generate_output_xml(note_info)
        
        # Save to file
        pretty_xml = self.prettify_xml(output_root)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"  Output saved to: {output_path}")
        print("   Processing complete!")
        
        return output_path
    
    def compare_with_expected(self, generated_path: str, expected_path: str):
        """
        Compare generated output with expected output
        (Helper for testing)
        """
        with open(generated_path, 'r', encoding='utf-8') as f:
            generated = f.read()
        
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected = f.read()
        
        # Simple comparison
        if generated.strip() == expected.strip():
            print("   Output matches expected!")
            return True
        else:
            print("   Output differs from expected")
            print("\nShowing first 500 characters of each:\n")
            print("GENERATED:")
            print(generated[:500])
            print("\nEXPECTED:")
            print(expected[:500])
            return False


# ============================================================================
# TESTING
# ============================================================================

def test_xml_handler():
    """Test the XML handler"""
    handler = XMLHandler()
    
    # Test with sample data
    test_input = """<?xml version="1.0" ?>
<Note start_block="14" end_block="20">
  <paragraph block_index="14">1. NATURE OF OPERATIONS</paragraph>
  <paragraph block_index="15">BestCo Ltd. was incorporated on January 24, 2011. The Company has a working capital deficiency of $19,821 as at December 31, 2023.</paragraph>
</Note>
"""
    
    # Save test input
    with open('/tmp/test_input.xml', 'w') as f:
        f.write(test_input)
    
    # Process
    handler.process_file('/tmp/test_input.xml', '/tmp/test_output.xml')
    
    # Show output
    with open('/tmp/test_output.xml', 'r') as f:
        print("\n" + "="*80)
        print("OUTPUT:")
        print("="*80)
        print(f.read())


if __name__ == "__main__":
    test_xml_handler()
