"""
NER (Named Entity Recognition) Module
Provides advanced entity extraction using spaCy for company names, locations, and organizations
Falls back gracefully if spaCy is not available
"""

import re
from typing import List, Optional
from dataclasses import dataclass

# Try to import spaCy, but don't fail if it's not installed
try:
    import spacy
    from spacy.language import Language
    from spacy.tokens import Doc, Span
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("   spaCy not available. NER features will be disabled.")
    print("   Install with: pip install spacy && python -m spacy download en_core_web_sm")


@dataclass
class NEREntity:
    """Represents an entity found by NER"""
    text: str
    label: str
    start: int
    end: int
    confidence: float = 1.0
    
    def __repr__(self):
        return f"NEREntity({self.text!r}, {self.label}, confidence={self.confidence:.2f})"


class FinancialNER:
    """
    Advanced Named Entity Recognition for financial documents
    Uses spaCy with custom rules for financial domain
    """
    
    def __init__(self, model_name: str = "en_core_web_sm", use_ner: bool = True):
        """
        Initialize NER system
        
        Args:
            model_name: spaCy model to load
            use_ner: Whether to use NER (False = fallback to regex only)
        """
        self.nlp: Optional[Language] = None
        self.use_ner = use_ner and SPACY_AVAILABLE
        
        if self.use_ner:
            try:
                self.nlp = spacy.load(model_name)
                self._setup_custom_patterns()
                print(f"  Loaded spaCy model: {model_name}")
            except OSError:
                print(f"  spaCy model '{model_name}' not found.")
                print(f"   Download with: python -m spacy download {model_name}")
                self.use_ner = False
                self.nlp = None
    
    def _setup_custom_patterns(self):
        """
        Add custom entity patterns for financial domain
        """
        if not self.nlp:
            return
        
        # Add entity ruler for custom patterns
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        else:
            ruler = self.nlp.get_pipe("entity_ruler")
        
        # Custom patterns for financial entities
        patterns = [
            # Company patterns (various legal structures)
            {"label": "ORG", "pattern": [{"TEXT": {"REGEX": r"[A-Z][a-z]+"}}, {"LOWER": "ltd"}, {"TEXT": "."}]},
            {"label": "ORG", "pattern": [{"TEXT": {"REGEX": r"[A-Z][a-z]+"}}, {"LOWER": "inc"}, {"TEXT": "."}]},
            {"label": "ORG", "pattern": [{"TEXT": {"REGEX": r"[A-Z][a-z]+"}}, {"LOWER": "corp"}, {"TEXT": "."}]},
            
            # Stock exchange symbols
            {"label": "STOCK_SYMBOL", "pattern": [{"LOWER": "symbol"}, {"TEXT": {"REGEX": r'["\u201C]'}}, {"IS_UPPER": True, "LENGTH": {">=": 2, "<=": 5}}, {"TEXT": {"REGEX": r'["\u201D]'}}]},
            
            # Financial concepts (will be caught by dictionary but NER provides confidence)
            {"label": "FINANCIAL_CONCEPT", "pattern": [{"LOWER": "working"}, {"LOWER": "capital"}, {"LOWER": "deficiency"}]},
            {"label": "FINANCIAL_CONCEPT", "pattern": [{"LOWER": "accumulated"}, {"LOWER": "deficit"}]},
        ]
        
        ruler.add_patterns(patterns)
    
    def extract_entities(self, text: str) -> List[NEREntity]:
        """
        Extract entities using NER
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of NEREntity objects
        """
        if not self.use_ner or not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Filter for relevant entity types
            if ent.label_ in ["ORG", "GPE", "LOC", "PERSON", "STOCK_SYMBOL", "FINANCIAL_CONCEPT"]:
                entities.append(NEREntity(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=1.0  # spaCy doesn't provide confidence by default
                ))
        
        return entities
    
    def extract_organizations(self, text: str) -> List[NEREntity]:
        """
        Extract only organization entities (companies)
        
        Args:
            text: Input text
            
        Returns:
            List of organization entities
        """
        entities = self.extract_entities(text)
        return [e for e in entities if e.label_ == "ORG"]
    
    def extract_locations(self, text: str) -> List[NEREntity]:
        """
        Extract location entities (GPE = Geo-Political Entity, LOC = Location)
        
        Args:
            text: Input text
            
        Returns:
            List of location entities
        """
        entities = self.extract_entities(text)
        return [e for e in entities if e.label_ in ["GPE", "LOC"]]
    
    def is_available(self) -> bool:
        """Check if NER is available and working"""
        return self.use_ner and self.nlp is not None


# Singleton instance (lazy loaded)
_ner_instance: Optional[FinancialNER] = None


def get_ner() -> FinancialNER:
    """
    Get or create the NER singleton instance
    
    Returns:
        FinancialNER instance
    """
    global _ner_instance
    if _ner_instance is None:
        _ner_instance = FinancialNER()
    return _ner_instance


# ============================================================================
# TESTING
# ============================================================================

def test_ner():
    """Test NER functionality"""
    print("="*80)
    print("Testing Financial NER Module")
    print("="*80)
    print()
    
    ner = get_ner()
    
    if not ner.is_available():
        print("  NER not available. Skipping tests.")
        return
    
    # Test cases
    test_texts = [
        "BestCo Ltd. was incorporated in British Columbia.",
        "The company is listed on the TSX Venture Exchange under the symbol \"BCL\".",
        "The registered office is in Vancouver, British Columbia, Canada.",
        "GoodCo Inc. has a working capital deficiency.",
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"Test {i}: {text}")
        entities = ner.extract_entities(text)
        
        if entities:
            print(f"  Found {len(entities)} entities:")
            for ent in entities:
                print(f"    - {ent}")
        else:
            print("  No entities found")
        print()
    
    print("="*80)
    print("  NER testing complete!")


if __name__ == "__main__":
    test_ner()
