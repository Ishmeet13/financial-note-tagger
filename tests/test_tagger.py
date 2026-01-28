"""
Test Suite for Financial Note Tagger
Tests all components: entity extraction, subsection detection, XML handling
"""

import unittest
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tagger import FinancialNoteTagger, Entity
from xml_handler import XMLHandler
from config import TAG_IDS


class TestEntityExtraction(unittest.TestCase):
    """Test entity extraction functionality"""
    
    def setUp(self):
        self.tagger = FinancialNoteTagger()
    
    def test_date_extraction_full_date(self):
        """Test extraction of full dates like 'January 24, 2011'"""
        text = "The company was incorporated on January 24, 2011."
        entities = self.tagger.extract_entities(text)
        
        date_entities = [e for e in entities if 'Date' in e.tag_id]
        self.assertGreater(len(date_entities), 0, "Should find at least one date")
        
        # Check that we found the correct date
        date_texts = [e.text for e in date_entities]
        self.assertIn("January 24, 2011", date_texts, "Should find the full date")
    
    def test_date_extraction_year_only(self):
        """Test extraction of year-only dates like '2023'"""
        text = "For the year ended December 31, 2023, the Company incurred a loss."
        entities = self.tagger.extract_entities(text)
        
        date_entities = [e for e in entities if 'Date' in e.tag_id]
        date_texts = [e.text for e in date_entities]
        
        self.assertTrue(
            "2023" in date_texts or "December 31, 2023" in date_texts,
            "Should find date in text"
        )
    
    def test_amount_extraction(self):
        """Test extraction of financial amounts"""
        text = "The Company has a deficit of $19,821 and loans of $7,166."
        entities = self.tagger.extract_entities(text)
        
        amount_entities = [e for e in entities if e.tag_id == TAG_IDS['financial_amount']]
        amount_texts = [e.text for e in amount_entities]
        
        self.assertIn("$19,821", amount_texts, "Should find first amount")
        self.assertIn("$7,166", amount_texts, "Should find second amount")
    
    def test_company_name_extraction(self):
        """Test extraction of company names"""
        text = "BestCo Ltd. was incorporated in 2011."
        entities = self.tagger.extract_entities(text)
        
        company_entities = [e for e in entities if e.tag_id == TAG_IDS['company_name']]
        
        self.assertGreater(len(company_entities), 0, "Should find company name")
        self.assertEqual(company_entities[0].text, "BestCo Ltd.", "Should extract correct company name")
    
    def test_financial_concept_extraction(self):
        """Test extraction of financial concepts"""
        text = "The Company has a working capital deficiency and accumulated deficit."
        entities = self.tagger.extract_entities(text)
        
        concept_entities = [e for e in entities if e.tag_id == TAG_IDS['financial_concept']]
        concept_texts = [e.text.lower() for e in concept_entities]
        
        self.assertTrue(
            any('working capital deficiency' in t for t in concept_texts),
            "Should find 'working capital deficiency'"
        )
        self.assertTrue(
            any('accumulated deficit' in t for t in concept_texts),
            "Should find 'accumulated deficit'"
        )
    
    def test_incorporation_date_priority(self):
        """Test that incorporation date gets higher priority than general date"""
        text = "BestCo Ltd. was incorporated on January 24, 2011."
        entities = self.tagger.extract_entities(text)
        
        date_entities = [e for e in entities if 'January 24, 2011' in e.text]
        
        # Should have exactly one entity for this date (after overlap removal)
        self.assertEqual(len(date_entities), 1, "Should have one date entity")
        
        # It should be tagged as incorporation date
        self.assertEqual(
            date_entities[0].tag_id, 
            TAG_IDS['incorporation_date'],
            "Should be tagged as incorporation date, not general date"
        )
    
    def test_address_extraction(self):
        """Test extraction of addresses"""
        text = "The office is at 13th Floor, 1313 Lucky Street, Vancouver, British Columbia, Canada, V1C 2D3."
        entities = self.tagger.extract_entities(text)
        
        address_entities = [e for e in entities if e.tag_id == TAG_IDS['address']]
        
        self.assertGreater(len(address_entities), 0, "Should find address")
    
    def test_trading_symbol_extraction(self):
        """Test extraction of trading symbols"""
        text = 'The Company is listed under the symbol "BCL".'
        entities = self.tagger.extract_entities(text)
        
        symbol_entities = [e for e in entities if e.tag_id == TAG_IDS['trading_symbol']]
        
        self.assertGreater(len(symbol_entities), 0, "Should find trading symbol")
        self.assertEqual(symbol_entities[0].text, "BCL", "Should extract correct symbol")


class TestOverlapResolution(unittest.TestCase):
    """Test overlap resolution logic"""
    
    def setUp(self):
        self.tagger = FinancialNoteTagger()
    
    def test_no_duplicate_entities(self):
        """Ensure no overlapping entities in output"""
        text = "As at December 31, 2023, the Company has a working capital deficiency of $19,821."
        entities = self.tagger.extract_entities(text)
        
        # Check that no entities overlap
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                # Entities should not overlap
                overlap = not (e1.end <= e2.start or e2.end <= e1.start)
                self.assertFalse(
                    overlap,
                    f"Entities should not overlap: {e1} and {e2}"
                )
    
    def test_priority_resolution(self):
        """Test that higher priority entities are kept when overlapping"""
        text = "incorporated on January 24, 2011"
        entities = self.tagger.extract_entities(text)
        
        # Find entities containing the date
        date_entities = [e for e in entities if 'January 24, 2011' in e.text]
        
        # Should only have one (the highest priority one)
        self.assertEqual(len(date_entities), 1)


class TestSubsectionDetection(unittest.TestCase):
    """Test subsection detection logic"""
    
    def setUp(self):
        self.tagger = FinancialNoteTagger()
    
    def test_header_detection(self):
        """Test identification of section headers"""
        from config import SubsectionRules
        
        header = "1. NATURE OF OPERATIONS AND GOING CONCERN"
        not_header = "The Company was incorporated in 2011."
        
        self.assertTrue(
            SubsectionRules.is_header(header),
            "Should identify header"
        )
        self.assertFalse(
            SubsectionRules.is_header(not_header),
            "Should not identify normal text as header"
        )
    
    def test_subsection_grouping(self):
        """Test grouping of paragraphs into subsections"""
        paragraphs = [
            {'text': '1. NATURE OF OPERATIONS', 'block_index': '1'},
            {'text': 'BestCo Ltd. was incorporated in 2011.', 'block_index': '2'},
            {'text': 'The Company operates in mining.', 'block_index': '3'},
        ]
        
        subsections = self.tagger.detect_subsections(paragraphs)
        
        self.assertGreater(len(subsections), 0, "Should create subsections")
        self.assertEqual(
            subsections[0]['tag_id'],
            TAG_IDS['header'],
            "First subsection should be header"
        )


class TestTagApplication(unittest.TestCase):
    """Test XML tag application"""
    
    def setUp(self):
        self.tagger = FinancialNoteTagger()
    
    def test_tag_paragraph_simple(self):
        """Test tagging a simple paragraph"""
        text = "The deficit is $19,821."
        tagged = self.tagger.tag_paragraph(text)
        
        self.assertIn('<Tag id="Financial_Amount_Placeholder">$19,821</Tag>', tagged)
        self.assertIn('The deficit is', tagged)
    
    def test_tag_paragraph_multiple_entities(self):
        """Test tagging with multiple entities"""
        text = "As at December 31, 2023, the loss was $11,459."
        tagged = self.tagger.tag_paragraph(text)
        
        # Should have both date and amount tagged
        self.assertIn('<Tag id=', tagged)
        self.assertIn('$11,459', tagged)
        self.assertTrue('2023' in tagged or 'December 31, 2023' in tagged)
    
    def test_preserves_untagged_text(self):
        """Test that untagged text is preserved"""
        text = "The Company operates in mining."
        tagged = self.tagger.tag_paragraph(text)
        
        # If no entities found, text should be unchanged
        # or only minimally tagged
        self.assertIn("The Company operates in mining", tagged)


class TestXMLHandling(unittest.TestCase):
    """Test XML parsing and generation"""
    
    def setUp(self):
        self.handler = XMLHandler()
        
        # Create a simple test XML
        self.test_xml = """<?xml version="1.0" ?>
<Note start_block="1" end_block="2">
  <paragraph block_index="1">1. TEST HEADER</paragraph>
  <paragraph block_index="2">BestCo Ltd. has a deficit of $19,821 at December 31, 2023.</paragraph>
</Note>
"""
        self.test_file = '/tmp/test_input.xml'
        with open(self.test_file, 'w') as f:
            f.write(self.test_xml)
    
    def test_parse_input_xml(self):
        """Test parsing of input XML"""
        note_info = self.handler.parse_input_xml(self.test_file)
        
        self.assertEqual(note_info['start_block'], '1')
        self.assertEqual(note_info['end_block'], '2')
        self.assertEqual(len(note_info['paragraphs']), 2)
    
    def test_generate_output_xml(self):
        """Test generation of output XML"""
        note_info = self.handler.parse_input_xml(self.test_file)
        output_root = self.handler.generate_output_xml(note_info)
        
        self.assertIsNotNone(output_root)
        self.assertEqual(output_root.tag, 'Tag')
        self.assertEqual(output_root.get('id'), TAG_IDS['note_root'])
    
    def test_end_to_end_processing(self):
        """Test complete processing pipeline"""
        output_file = '/tmp/test_output.xml'
        
        try:
            self.handler.process_file(self.test_file, output_file)
            
            # Check that output file was created
            self.assertTrue(os.path.exists(output_file))
            
            # Check that output is valid XML
            with open(output_file, 'r') as f:
                content = f.read()
                self.assertIn('<?xml', content)
                self.assertIn('<Tag id=', content)
        finally:
            # Cleanup
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def tearDown(self):
        """Cleanup test files"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)


class TestIntegration(unittest.TestCase):
    """Integration tests with real data"""
    
    def setUp(self):
        self.handler = XMLHandler()
        # Updated path for reorganized structure (run from root)
        self.input_file = 'data/note_1_input_v1_1.xml'
        self.output_file = '/tmp/integration_test_output.xml'
    
    def test_process_real_file(self):
        """Test processing the actual assignment input file"""
        if not os.path.exists(self.input_file):
            self.skipTest(f"Input file not found: {self.input_file}")
        
        try:
            self.handler.process_file(self.input_file, self.output_file)
            
            # Verify output exists
            self.assertTrue(os.path.exists(self.output_file))
            
            # Verify it's valid XML
            with open(self.output_file, 'r') as f:
                content = f.read()
                self.assertIn('<?xml', content)
                self.assertIn('NatureOfOperationsAndGoingConcernNote', content)
        finally:
            if os.path.exists(self.output_file):
                os.remove(self.output_file)


def run_tests():
    """Run all tests with detailed output"""
    
    print("="*80)
    print("Running Financial Note Tagger Test Suite")
    print("="*80)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEntityExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestOverlapResolution))
    suite.addTests(loader.loadTestsFromTestCase(TestSubsectionDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestTagApplication))
    suite.addTests(loader.loadTestsFromTestCase(TestXMLHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("="*80)
    print("Test Summary")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n  All tests passed!")
    else:
        print("\n  Some tests failed. See details above.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Change to project root directory
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    success = run_tests()
    sys.exit(0 if success else 1)
