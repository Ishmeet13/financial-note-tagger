"""
Main Financial Note Tagger Module
Handles entity extraction and tagging of financial disclosure notes

HYBRID APPROACH:
- Uses regex patterns for structured, deterministic extraction (dates, amounts)
- Uses NER (spaCy) for complex entity recognition (company names, locations)
- Combines results with priority-based conflict resolution
"""

import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from config import (
    Patterns, 
    FINANCIAL_CONCEPTS, 
    ENTITY_PRIORITIES, 
    TAG_IDS,
    SubsectionRules
)

# Import NER module (falls back gracefully if spaCy not available)
from ner_module import get_ner, NEREntity


@dataclass
class Entity:
    """Represents a tagged entity in the text"""
    start: int
    end: int
    tag_id: str
    text: str
    priority: int = 50
    
    def __repr__(self):
        return f"Entity({self.text!r}, {self.tag_id}, pos={self.start}-{self.end})"


class FinancialNoteTagger:
    """
    Main tagger class for extracting and tagging entities in financial notes
    
    HYBRID EXTRACTION STRATEGY:
    1. Regex patterns for structured data (dates, amounts, addresses)
    2. NER (spaCy) for complex entities (company names, locations)
    3. Dictionary matching for financial concepts
    4. Priority-based conflict resolution
    """
    
    def __init__(self, use_ner: bool = True):
        """
        Initialize tagger
        
        Args:
            use_ner: Whether to use NER for entity extraction (True = hybrid mode)
        """
        self.patterns = Patterns()
        self.use_ner = use_ner
        
        # Initialize NER module (lazy loaded)
        self.ner = get_ner() if use_ner else None
        
        # Track extraction statistics
        self.stats = {
            'regex_extractions': 0,
            'ner_extractions': 0,
            'dictionary_extractions': 0,
        }
        
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract all entities from a paragraph of text using HYBRID approach
        
        EXTRACTION LAYERS:
        1. High-priority regex patterns (incorporation dates, addresses, symbols)
        2. NER for organizations and locations (if available)
        3. Regex for financial amounts
        4. Dictionary matching for financial concepts
        5. General date patterns
        
        Returns a list of Entity objects with overlaps resolved
        """
        entities = []
        
        # Layer 1: High-priority, context-specific entities (REGEX)
        entities.extend(self._extract_incorporation_dates(text))
        entities.extend(self._extract_addresses(text))
        entities.extend(self._extract_trading_symbols(text))
        
        # Layer 1.5: Company names - HYBRID (NER + Regex fallback)
        entities.extend(self._extract_company_names_hybrid(text))
        
        # Layer 2: Financial amounts (REGEX)
        entities.extend(self._extract_amounts(text))
        
        # Layer 3: Financial concepts (DICTIONARY)
        entities.extend(self._extract_financial_concepts(text))
        
        # Layer 4: General dates (REGEX - lowest priority)
        entities.extend(self._extract_dates(text))
        
        # Remove overlapping entities (keep higher priority ones)
        entities = self._remove_overlaps(entities)
        
        # Sort by position for proper tagging
        entities.sort(key=lambda e: e.start)
        
        return entities
    
    def _extract_incorporation_dates(self, text: str) -> List[Entity]:
        """Extract incorporation date with context"""
        entities = []
        match = re.search(self.patterns.INCORPORATION_CONTEXT, text, re.IGNORECASE)
        if match:
            date_text = match.group(1)
            start = match.start(1)
            end = match.end(1)
            entities.append(Entity(
                start=start,
                end=end,
                tag_id=TAG_IDS['incorporation_date'],
                text=date_text,
                priority=ENTITY_PRIORITIES['IncorporationDate']
            ))
        return entities
    
    def _extract_addresses(self, text: str) -> List[Entity]:
        """Extract registered office addresses"""
        entities = []
        for match in re.finditer(self.patterns.ADDRESS_PATTERN, text):
            entities.append(Entity(
                start=match.start(),
                end=match.end(),
                tag_id=TAG_IDS['address'],
                text=match.group(),
                priority=ENTITY_PRIORITIES['AddressOfRegisteredOfficeOfEntity']
            ))
        return entities
    
    def _extract_trading_symbols(self, text: str) -> List[Entity]:
        """Extract trading symbols"""
        entities = []
        for match in re.finditer(self.patterns.TRADING_SYMBOL_PATTERN, text):
            symbol = match.group(1)
            entities.append(Entity(
                start=match.start(1),
                end=match.end(1),
                tag_id=TAG_IDS['trading_symbol'],
                text=symbol,
                priority=ENTITY_PRIORITIES['EntityPrimaryTradingSymbol']
            ))
        return entities
    
    def _extract_company_names_hybrid(self, text: str) -> List[Entity]:
        """
        HYBRID: Extract company names using NER + regex fallback
        
        Strategy:
        1. Try NER first (if available) - better at handling variations
        2. Fallback to regex for specific known patterns
        3. Combine and deduplicate results
        
        Args:
            text: Input text
            
        Returns:
            List of company name entities
        """
        entities = []
        
        # Try NER first (more sophisticated)
        if self.use_ner and self.ner and self.ner.is_available():
            ner_entities = self._extract_company_names_ner(text)
            entities.extend(ner_entities)
            if ner_entities:
                self.stats['ner_extractions'] += len(ner_entities)
        
        # Always try regex as well (catches specific patterns NER might miss)
        regex_entities = self._extract_company_names_regex(text)
        entities.extend(regex_entities)
        if regex_entities:
            self.stats['regex_extractions'] += len(regex_entities)
        
        # Note: Overlaps will be resolved in _remove_overlaps()
        return entities
    
    def _extract_company_names_ner(self, text: str) -> List[Entity]:
        """
        Extract company names using NER (spaCy)
        
        More sophisticated than regex - understands context and variations
        """
        entities = []
        
        if not self.ner or not self.ner.is_available():
            return entities
        
        # Get organizations from NER
        orgs = self.ner.extract_organizations(text)
        
        for org in orgs:
            # Filter for company-like organizations (have Ltd., Inc., Corp., etc.)
            if any(suffix in org.text for suffix in ['Ltd.', 'Inc.', 'Corp.', 'Limited', 'Corporation']):
                entities.append(Entity(
                    start=org.start,
                    end=org.end,
                    tag_id=TAG_IDS['company_name'],
                    text=org.text,
                    priority=ENTITY_PRIORITIES['NameOfReportingEntityOrOtherMeansOfIdentification']
                ))
        
        return entities
    
    def _extract_company_names_regex(self, text: str) -> List[Entity]:
        """
        Extract company names using regex patterns (FALLBACK)
        
        Fast and deterministic for known patterns at start of paragraph
        """
        entities = []
        
        # Look for specific pattern at start of paragraph
        # "BestCo Ltd. (formerly GoodCo Ltd.)"
        match = re.match(r'^([A-Z][a-zA-Z]+\s+Ltd\.)', text)
        if match:
            entities.append(Entity(
                start=match.start(1),
                end=match.end(1),
                tag_id=TAG_IDS['company_name'],
                text=match.group(1),
                priority=ENTITY_PRIORITIES['NameOfReportingEntityOrOtherMeansOfIdentification']
            ))
        
        return entities
    
    def _extract_company_names(self, text: str) -> List[Entity]:
        """
        DEPRECATED: Use _extract_company_names_hybrid instead
        Kept for backward compatibility
        """
        return self._extract_company_names_regex(text)
    
    def _extract_amounts(self, text: str) -> List[Entity]:
        """Extract financial amounts like $19,821"""
        entities = []
        for match in re.finditer(self.patterns.AMOUNT_PATTERN, text):
            entities.append(Entity(
                start=match.start(),
                end=match.end(),
                tag_id=TAG_IDS['financial_amount'],
                text=match.group(),
                priority=ENTITY_PRIORITIES['Financial_Amount_Placeholder']
            ))
        return entities
    
    def _extract_financial_concepts(self, text: str) -> List[Entity]:
        """Extract financial concepts from dictionary"""
        entities = []
        
        for concept, tag_id in FINANCIAL_CONCEPTS.items():
            # Use word boundaries and case-insensitive matching
            pattern = r'\b' + re.escape(concept) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(Entity(
                    start=match.start(),
                    end=match.end(),
                    tag_id=TAG_IDS['financial_concept'],
                    text=match.group(),
                    priority=ENTITY_PRIORITIES['Financial_Concept_Placeholder']
                ))
        
        if entities:
            self.stats['dictionary_extractions'] += len(entities)
        
        return entities
    
    def _extract_dates(self, text: str) -> List[Entity]:
        """Extract dates - most general, lowest priority"""
        entities = []
        
        for pattern in self.patterns.DATE_PATTERNS:
            for match in re.finditer(pattern, text):
                entities.append(Entity(
                    start=match.start(),
                    end=match.end(),
                    tag_id=TAG_IDS['date'],
                    text=match.group(),
                    priority=ENTITY_PRIORITIES['Date_Placeholder']
                ))
        
        return entities
    
    def _remove_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """
        Remove overlapping entities, keeping higher priority ones
        If same priority, keep longer match
        """
        if not entities:
            return []
        
        # Sort by start position, then priority (descending), then length (descending)
        sorted_entities = sorted(
            entities, 
            key=lambda e: (e.start, -e.priority, -(e.end - e.start))
        )
        
        result = []
        last_end = -1
        
        for entity in sorted_entities:
            # Check if this entity overlaps with the last accepted one
            if entity.start >= last_end:
                result.append(entity)
                last_end = entity.end
        
        return result
    
    def tag_text(self, text: str, entities: List[Entity]) -> str:
        """
        Apply XML tags to text based on extracted entities
        """
        if not entities:
            return text
        
        # Sort entities by position
        entities = sorted(entities, key=lambda e: e.start)
        
        result = []
        last_pos = 0
        
        for entity in entities:
            # Add untagged text before this entity
            result.append(text[last_pos:entity.start])
            
            # Add tagged entity
            result.append(f'<Tag id="{entity.tag_id}">{entity.text}</Tag>')
            
            last_pos = entity.end
        
        # Add remaining text after last entity
        result.append(text[last_pos:])
        
        return ''.join(result)
    
    def tag_paragraph(self, text: str) -> str:
        """
        Main method to tag a single paragraph
        """
        entities = self.extract_entities(text)
        tagged_text = self.tag_text(text, entities)
        return tagged_text
    
    def detect_subsections(self, paragraphs: List[Dict]) -> List[Dict]:
        """
        Detect subsections in the note based on content and structure
        
        Args:
            paragraphs: List of dicts with 'text' and 'block_index'
            
        Returns:
            List of dicts with subsection info
        """
        subsections = []
        current_section = None
        
        for i, para in enumerate(paragraphs):
            text = para['text']
            
            if SubsectionRules.is_header(text):
                # Save previous section if exists
                if current_section:
                    subsections.append(current_section)
                
                # Header gets its own section with ONLY the header paragraph
                subsections.append({
                    'tag_id': TAG_IDS['header'],
                    'paragraphs': [para],
                    'skip_tagging': True  # Don't tag entities in headers
                })
                current_section = None
            else:
                # Determine which subsection this belongs to based on content
                # Check if this paragraph should start a new "going concern" section
                should_start_going_concern = (
                    'going concern' in text.lower() or
                    'material uncertainty' in text.lower() or
                    'These consolidated financial statements' in text
                )
                
                if should_start_going_concern and (not current_section or current_section['tag_id'] != TAG_IDS['going_concern_description']):
                    # Save previous section
                    if current_section:
                        subsections.append(current_section)
                    # Start going concern section
                    current_section = {
                        'tag_id': TAG_IDS['going_concern_description'],
                        'paragraphs': [para]
                    }
                elif not current_section:
                    # Start operations description section
                    current_section = {
                        'tag_id': TAG_IDS['operations_description'],
                        'paragraphs': [para]
                    }
                else:
                    # Continue current section
                    current_section['paragraphs'].append(para)
        
        # Add last section
        if current_section:
            subsections.append(current_section)
        
        return subsections

    def get_extraction_mode(self) -> str:
        """
        Get current extraction mode description
        
        Returns:
            String describing the extraction mode
        """
        if self.use_ner and self.ner and self.ner.is_available():
            return "HYBRID (Regex + NER + Dictionary)"
        else:
            return "FALLBACK (Regex + Dictionary only)"
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get extraction statistics
        
        Returns:
            Dictionary with extraction counts by method
        """
        return self.stats.copy()
    
    def print_stats(self):
        """Print extraction statistics"""
        print("\n" + "="*60)
        print("Extraction Statistics")
        print("="*60)
        print(f"Mode: {self.get_extraction_mode()}")
        print(f"Regex extractions:      {self.stats['regex_extractions']}")
        print(f"NER extractions:        {self.stats['ner_extractions']}")
        print(f"Dictionary extractions: {self.stats['dictionary_extractions']}")
        total = sum(self.stats.values())
        print(f"Total:                  {total}")
        print("="*60)


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_tagger():
    """Quick test of the tagger"""
    tagger = FinancialNoteTagger()
    
    # Test paragraph
    text = ("BestCo Ltd. (formerly GoodCo Ltd.) was incorporated on January 24, 2011. "
            "As at December 31, 2023, the Company has a working capital deficiency of $19,821.")
    
    print("="*80)
    print("Testing Financial Note Tagger")
    print("="*80)
    print(f"\nMode: {tagger.get_extraction_mode()}")
    print("\nOriginal text:")
    print(text)
    print("\n" + "="*80 + "\n")
    
    # Extract entities
    entities = tagger.extract_entities(text)
    print(f"Found {len(entities)} entities:")
    for entity in entities:
        print(f"  {entity}")
    print("\n" + "="*80 + "\n")
    
    # Tag text
    tagged = tagger.tag_paragraph(text)
    print("Tagged text:")
    print(tagged)
    
    # Show stats
    tagger.print_stats()


if __name__ == "__main__":
    test_tagger()
