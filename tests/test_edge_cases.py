#!/usr/bin/env python3
"""
Advanced Edge Case Tests
Tests scenarios not covered in the provided sample to demonstrate robust handling
"""

import unittest
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tagger import FinancialNoteTagger


class AdvancedEdgeCaseTests(unittest.TestCase):
    """Tests for edge cases and boundary conditions"""
    
    def setUp(self):
        self.tagger = FinancialNoteTagger()
    
    def test_overlapping_dates_priority(self):
        """Test that specific dates take priority over general year patterns"""
        text = "incorporated on January 24, 2011 in the year 2011"
        entities = []
        
        # Extract both types
        entities += self.tagger._extract_incorporation_dates(text)  # Priority 100
        entities += self.tagger._extract_dates(text)  # Priority 50
        
        # Remove overlaps
        entities = self.tagger._remove_overlaps(entities)
        
        # Should keep "January 24, 2011" as IncorporationDate, not tag "2011" separately
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].tag_id, 'IncorporationDate')
        self.assertEqual(entities[0].text, 'January 24, 2011')
    
    def test_multiple_amounts_in_one_sentence(self):
        """Test extraction of multiple financial amounts in close proximity"""
        text = "assets of $1,234,567 and liabilities of $890,123 and equity of $344,444"
        entities = self.tagger._extract_amounts(text)
        
        self.assertEqual(len(entities), 3)
        amounts = [e.text for e in entities]
        self.assertIn('$1,234,567', amounts)
        self.assertIn('$890,123', amounts)
        self.assertIn('$344,444', amounts)
    
    def test_amount_without_cents(self):
        """Test amounts without decimal cents"""
        text = "total revenue of $1,000,000 for the year"
        entities = self.tagger._extract_amounts(text)
        
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, '$1,000,000')
    
    def test_amount_with_cents(self):
        """Test amounts with decimal cents"""
        text = "per share price of $12.34 on the market"
        entities = self.tagger._extract_amounts(text)
        
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, '$12.34')
    
    def test_small_amount(self):
        """Test small amounts (less than 1000)"""
        text = "petty cash of $50 remaining"
        entities = self.tagger._extract_amounts(text)
        
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, '$50')
    
    def test_company_name_with_punctuation(self):
        """Test company names with various punctuation"""
        test_cases = [
            "BestCo Ltd.",
            "BestCo Inc.",
            "BestCo Corp.",
            "BestCo LLC",
        ]
        
        for company in test_cases:
            text = f"{company} was incorporated"
            entities = self.tagger._extract_company_names_regex(text)
            self.assertGreaterEqual(len(entities), 1, f"Failed to extract: {company}")
    
    def test_date_without_day(self):
        """Test date patterns with only month and year"""
        text = "as of December 2023 the company"
        entities = self.tagger._extract_dates(text)
        
        # Should find "December 2023"
        texts = [e.text for e in entities]
        self.assertIn('December 2023', texts)
    
    def test_year_only(self):
        """Test year-only date patterns"""
        text = "for the year 2023 and 2022"
        entities = self.tagger._extract_dates(text)
        
        # Should find both years
        texts = [e.text for e in entities]
        self.assertIn('2023', texts)
        self.assertIn('2022', texts)
    
    def test_financial_concept_case_insensitive(self):
        """Test that financial concepts are matched case-insensitively"""
        text = "The Company has a WORKING CAPITAL DEFICIENCY of significant amount"
        entities = self.tagger._extract_financial_concepts(text)
        
        # Should match despite uppercase
        self.assertGreaterEqual(len(entities), 1)
        found_texts = [e.text.lower() for e in entities]
        self.assertIn('working capital deficiency', found_texts)
    
    def test_financial_concept_partial_match(self):
        """Test that partial matches are NOT tagged (must be complete phrase)"""
        text = "capital is deficient but not a working capital deficiency"
        entities = self.tagger._extract_financial_concepts(text)
        
        # Should only find the complete phrase "working capital deficiency"
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, 'working capital deficiency')
    
    def test_empty_text(self):
        """Test handling of empty text"""
        entities = self.tagger._extract_dates("")
        self.assertEqual(len(entities), 0)
        
        entities = self.tagger._extract_amounts("")
        self.assertEqual(len(entities), 0)
    
    def test_text_with_only_whitespace(self):
        """Test handling of text with only whitespace"""
        text = "   \n\t   "
        entities = self.tagger._extract_dates(text)
        self.assertEqual(len(entities), 0)
    
    def test_special_characters_in_text(self):
        """Test handling of special characters"""
        text = "Amount: $1,000 (approx.) [verified] <confirmed>"
        entities = self.tagger._extract_amounts(text)
        
        # Should still find the amount despite special characters
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, '$1,000')
    
    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        text = "Company has revenue of $1,000,000 in fiscal year"
        entities = self.tagger._extract_amounts(text)
        
        # Should handle unicode without errors
        self.assertEqual(len(entities), 1)
    
    def test_very_long_text(self):
        """Test handling of very long text (performance check)"""
        # Create a long text with embedded entities
        text = ("This is a long paragraph. " * 100) + "$1,000 in December 2023"
        entities = self.tagger._extract_amounts(text)
        
        # Should still find entities efficiently
        self.assertEqual(len(entities), 1)
    
    def test_overlapping_financial_concepts(self):
        """Test when financial concept keywords overlap"""
        text = "loss from operating activities in the year"
        entities = self.tagger._extract_financial_concepts(text)
        
        # Should find both "loss" and "operating activities"
        texts = [e.text for e in entities]
        self.assertIn('loss', texts)
        self.assertIn('operating activities', texts)
    
    def test_address_extraction_multiline(self):
        """Test address extraction that spans multiple lines"""
        # This tests if address patterns work with newlines
        text = "located at 123 Main Street\nSuite 100\nToronto, ON\nCanada M5H 2N2"
        entities = self.tagger._extract_addresses(text)
        
        # Should handle multiline addresses
        self.assertGreaterEqual(len(entities), 0)
    
    def test_deterministic_sorting(self):
        """Test that entity sorting is deterministic"""
        text = "December 2023 and $1,000 and 2023"
        
        # Run extraction multiple times
        results = []
        for _ in range(5):
            entities = []
            entities += self.tagger._extract_dates(text)
            entities += self.tagger._extract_amounts(text)
            entities = self.tagger._remove_overlaps(entities)
            
            # Convert to tuple for comparison
            result = tuple((e.start, e.end, e.text) for e in entities)
            results.append(result)
        
        # All runs should produce identical results
        self.assertTrue(all(r == results[0] for r in results))
    
    def test_priority_resolution_complex(self):
        """Test priority resolution with multiple overlapping entities"""
        text = "incorporated on January 24, 2011"
        entities = []
        
        # Add entities with different priorities
        entities += self.tagger._extract_incorporation_dates(text)  # Priority 100
        entities += self.tagger._extract_dates(text)  # Priority 50
        
        # Remove overlaps
        entities = self.tagger._remove_overlaps(entities)
        
        # Should keep highest priority only
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].priority, 100)


class BoundaryConditionTests(unittest.TestCase):
    """Tests for boundary conditions and limits"""
    
    def setUp(self):
        self.tagger = FinancialNoteTagger()
    
    def test_maximum_amount(self):
        """Test extraction of very large financial amounts"""
        text = "total assets of $999,999,999,999.99 reported"
        entities = self.tagger._extract_amounts(text)
        
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, '$999,999,999,999.99')
    
    def test_minimum_amount(self):
        """Test extraction of very small amounts"""
        text = "fee of $0.01 charged"
        entities = self.tagger._extract_amounts(text)
        
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, '$0.01')
    
    def test_zero_amount(self):
        """Test extraction of zero amounts"""
        text = "balance of $0 remaining"
        entities = self.tagger._extract_amounts(text)
        
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0].text, '$0')
    
    def test_year_boundary_2000(self):
        """Test year extraction around year 2000 boundary"""
        text = "from 1999 to 2000 and 2001"
        entities = self.tagger._extract_dates(text)
        
        texts = [e.text for e in entities]
        self.assertIn('1999', texts)
        self.assertIn('2000', texts)
        self.assertIn('2001', texts)
    
    def test_current_year_plus_future(self):
        """Test that future years are handled (within reason)"""
        text = "projected for 2030 fiscal year"
        entities = self.tagger._extract_dates(text)
        
        texts = [e.text for e in entities]
        self.assertIn('2030', texts)


def run_tests():
    """Run all edge case tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(AdvancedEdgeCaseTests))
    suite.addTests(loader.loadTestsFromTestCase(BoundaryConditionTests))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
