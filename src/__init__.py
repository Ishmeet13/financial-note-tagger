"""
Financial Note Tagger - Source Package
Assignment 1: Vertical Parsing & Tagging
"""

from .tagger import FinancialNoteTagger, Entity
from .xml_handler import XMLHandler
from .config import Patterns, FINANCIAL_CONCEPTS, ENTITY_PRIORITIES, TAG_IDS, SubsectionRules
from .ner_module import FinancialNER, get_ner, NEREntity

__all__ = [
    'FinancialNoteTagger',
    'Entity',
    'XMLHandler',
    'Patterns',
    'FINANCIAL_CONCEPTS',
    'ENTITY_PRIORITIES',
    'TAG_IDS',
    'SubsectionRules',
    'FinancialNER',
    'get_ner',
    'NEREntity',
]

__version__ = '1.0.0'
__author__ = 'Ishmeet Singh Arora'
