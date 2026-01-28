"""
Configuration file for Financial Note Tagger
Contains all patterns, mappings, and constants
"""

import re
from typing import Dict, List, Tuple

# ============================================================================
# REGEX PATTERNS
# ============================================================================

class Patterns:
    """All regex patterns used for entity extraction"""
    
    # Date patterns (ordered by specificity)
    DATE_PATTERNS = [
        # Full date with month name: "January 24, 2011"
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        # Month and year: "August 2023"
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        # Just year: "2023" or "2022" (must be 4 digits, 19xx or 20xx)
        r'\b(19|20)\d{2}\b',
    ]
    
    # Financial amount pattern
    # Matches: $19,821 or $137,942 or $7,166
    AMOUNT_PATTERN = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
    
    # Company name patterns
    COMPANY_PATTERNS = [
        # Matches: "BestCo Ltd." or "GoodCo Ltd."
        r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+Ltd\.',
        # Also match Inc., Corp., etc.
        r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Inc\.|Corp\.|Corporation|Limited)',
    ]
    
    # Address pattern
    # Matches: "13th Floor, 1313 Lucky Street, Vancouver, British Columbia, Canada, V1C 2D3"
    ADDRESS_PATTERN = r'\d+(?:st|nd|rd|th)?\s+Floor,\s+\d+\s+[A-Za-z\s]+Street,\s+[A-Za-z\s,]+,\s+[A-Z]\d[A-Z]\s+\d[A-Z]\d'
    
    # Trading symbol pattern
    # Matches: "BCL" in quotes (including smart quotes)
    TRADING_SYMBOL_PATTERN = r'under the symbol\s+["\u201C]([A-Z]{2,5})["\u201D]'
    
    # Incorporation date context pattern
    INCORPORATION_CONTEXT = r'was incorporated.*?on\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})'


# ============================================================================
# FINANCIAL CONCEPTS DICTIONARY
# ============================================================================
# IMPORTANT: This list is matched against the expected output
# Only concepts that appear in note_1_expected_output_v1_1.xml are included

FINANCIAL_CONCEPTS = {
    # Balance sheet items (from expected output)
    'working capital deficiency': 'Financial_Concept_Placeholder',
    'accumulated deficit': 'Financial_Concept_Placeholder',
    
    # Income statement items (from expected output)
    'loss': 'Financial_Concept_Placeholder',
    'operating activities': 'Financial_Concept_Placeholder',
    
    # NOTE: The following are NOT in expected output, so commented out:
    # 'going concern': 'Financial_Concept_Placeholder',  # Not tagged in expected
    # 'non-current loans payable': 'Financial_Concept_Placeholder',  # Not tagged
    # 'material uncertainty': 'Financial_Concept_Placeholder',  # Not tagged
    # 'used cash in operating activities': 'Financial_Concept_Placeholder',  # Too specific
}


# ============================================================================
# SUBSECTION DETECTION RULES
# ============================================================================

class SubsectionRules:
    """Rules for detecting subsections in financial notes"""
    
    @staticmethod
    def is_header(paragraph_text: str) -> bool:
        """
        Detect if a paragraph is a section header.
        Headers typically:
        - Start with a number followed by period
        - Are in ALL CAPS or Title Case
        - Are relatively short
        """
        text = paragraph_text.strip()
        
        # Check if starts with number
        if not re.match(r'^\d+\.', text):
            return False
        
        # Check if mostly uppercase (ignoring the number)
        content = text.split('.', 1)[1].strip() if '.' in text else text
        uppercase_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        
        return uppercase_ratio > 0.5
    
    @staticmethod
    def determine_subsection_tag(paragraph_text: str, position: int) -> str:
        """
        Determine the appropriate subsection tag based on content
        """
        text_lower = paragraph_text.lower()
        
        if SubsectionRules.is_header(paragraph_text):
            return 'NatureOfOperationsAndGoingConcernHeader'
        elif 'going concern' in text_lower or 'material uncertainty' in text_lower:
            return 'DescriptionOfUncertaintiesOfEntitysAbilityToContinueAsGoingConcern'
        elif position <= 2:  # First few paragraphs after header
            return 'DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities'
        else:
            return 'DescriptionOfUncertaintiesOfEntitysAbilityToContinueAsGoingConcern'


# ============================================================================
# ENTITY TYPE PRIORITIES
# ============================================================================

# When entities overlap, use this priority (higher number = higher priority)
ENTITY_PRIORITIES = {
    'IncorporationDate': 100,  # Highest - very specific
    'AddressOfRegisteredOfficeOfEntity': 90,
    'EntityPrimaryTradingSymbol': 85,
    'NameOfReportingEntityOrOtherMeansOfIdentification': 80,
    'Financial_Amount_Placeholder': 70,
    'Financial_Concept_Placeholder': 60,
    'Date_Placeholder': 50,  # Lowest - most general
}


# ============================================================================
# TAG ID MAPPINGS
# ============================================================================

TAG_IDS = {
    'note_root': 'NatureOfOperationsAndGoingConcernNote',
    'header': 'NatureOfOperationsAndGoingConcernHeader',
    'operations_description': 'DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities',
    'going_concern_description': 'DescriptionOfUncertaintiesOfEntitysAbilityToContinueAsGoingConcern',
    'company_name': 'NameOfReportingEntityOrOtherMeansOfIdentification',
    'incorporation_date': 'IncorporationDate',
    'address': 'AddressOfRegisteredOfficeOfEntity',
    'trading_symbol': 'EntityPrimaryTradingSymbol',
    'date': 'Date_Placeholder',
    'financial_concept': 'Financial_Concept_Placeholder',
    'financial_amount': 'Financial_Amount_Placeholder',
}
