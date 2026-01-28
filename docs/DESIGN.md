# Assignment 1: Vertical Parsing & Tagging
## System Design Document

---

## Executive Summary

This document walks through the design and implementation of a financial note tagger—a system that reads unstructured financial disclosure notes and automatically identifies and tags key entities like dates, company names, financial amounts, and important concepts.

The challenge? Financial documents are messy. The same date might appear in different contexts (an incorporation date vs. a reporting period), amounts need to be distinguished from regular numbers, and company names come in various formats. Our solution tackles this with a **hybrid approach** that combines the speed of regex patterns with the intelligence of NER (Named Entity Recognition) and the precision of dictionary matching.

### What We Achieved

| Metric | Result | Requirement | Status |
|--------|--------|-------------|--------|
| Accuracy | 100% | ≥ 99% | ✓ Exceeded |
| Determinism | 100% | Consistent output | ✓ Passed |
| Completeness | 0 missing tags | Full coverage | ✓ Passed |
| Speed | 352 notes/sec | Handle 20-30 notes | ✓ Exceeded |

---

## Table of Contents

1. [Understanding the Problem](#1-understanding-the-problem)
2. [Our Approach](#2-our-approach)
3. [System Design & Diagrams](#3-system-design--diagrams)
4. [How the Algorithms Work](#4-how-the-algorithms-work)
5. [Project Structure](#5-project-structure)
6. [Testing & Verification](#6-testing--verification)
7. [Performance Deep Dive](#7-performance-deep-dive)

---

## 1. Understanding the Problem

### 1.1 What We Need to Find

Financial notes contain several types of information that need to be tagged:

| Category | Examples | Why It Matters |
|----------|----------|----------------|
| **Dates** | "January 24, 2011", "December 31, 2023" | Track incorporation, reporting periods, fiscal years |
| **Company Info** | "BestCo Ltd.", "BCL", office addresses | Identify the reporting entity |
| **Financial Data** | "$19,821", "working capital deficiency" | Highlight key financial metrics and concepts |
| **Document Structure** | Headers, sections | Organize the note logically |

### 1.2 The Tricky Parts

Building this system wasn't straightforward. Here are the challenges we had to solve:

**Overlapping Matches**: When we see "January 24, 2011", our date pattern finds it—but so does our year pattern matching "2011". We can't tag both; we need to pick the right one.

**Context Matters**: The date "January 24, 2011" means different things in different places:
- In "was incorporated on January 24, 2011" → It's an **Incorporation Date**
- In "as at January 24, 2011" → It's just a **general date**

**Special Characters**: Real documents use smart quotes ("), em dashes, and other characters that can trip up simple pattern matching.

**Knowing When to Stop**: Some financial terms like "going concern" appear in the text but shouldn't always be tagged—context determines whether it's a concept or just part of a sentence.

---

## 2. Our Approach

### 2.1 The Hybrid Strategy

Rather than relying on a single technique, we combine three complementary methods:

| Method | What It's Good At | Where We Use It |
|--------|-------------------|-----------------|
| **Regex Patterns** | Fast, predictable, great for structured data | Dates, amounts, addresses, symbols |
| **NER (spaCy)** | Understanding context, handling variations | Company names, locations |
| **Dictionary Matching** | Domain-specific terms | Financial concepts like "accumulated deficit" |

### 2.2 The Priority System

When multiple patterns match the same text, we use a priority system to pick the winner:

| Priority | Entity Type | Why This Ranking |
|----------|-------------|------------------|
| 100 | Incorporation Date | Most specific—requires context |
| 90 | Registered Address | Complex pattern, rarely conflicts |
| 85 | Trading Symbol | Specific format in quotes |
| 80 | Company Name | Important but may overlap with other text |
| 70 | Financial Amount | Clear $ pattern |
| 60 | Financial Concept | Dictionary match |
| 50 | General Date | Broadest pattern, lowest priority |

This means if "January 24, 2011" matches both as an incorporation date (priority 100) and a general date (priority 50), the incorporation date wins.

---

## 3. System Design & Diagrams

### 3.1 System Architecture

![System Architecture](../diagrams/System%20Architecture.png)

*Figure 1: The complete processing pipeline from input to output*

The system flows through six main stages:

1. **XML Parser** reads the input file and extracts paragraphs
2. **Subsection Detector** groups paragraphs into logical sections (headers, operations, going concern)
3. **Entity Extraction** runs our hybrid pipeline to find all entities
4. **Overlap Resolution** applies priority rules to handle conflicts
5. **Tag Application** inserts XML tags while preserving the original structure
6. **XML Generator** produces the final formatted output

---

### 3.2 Class Diagram

![Class Diagram](../diagrams/Class%20Diagram.png)

*Figure 2: The main classes and how they relate to each other*

The core classes are:

- **Entity**: A simple data class holding what we found (text, position, tag type, priority)
- **FinancialNoteTagger**: The brain of the operation—handles all extraction and tagging logic
- **XMLHandler**: Manages reading input XML and writing tagged output
- **FinancialNER**: Optional spaCy integration that gracefully falls back if not available
- **Patterns & Config**: All our regex patterns and configuration constants

---

### 3.3 Sequence Diagram

![Sequence Diagram](../diagrams/Sequence%20Diagram.png)

*Figure 3: How components interact during processing*

The sequence shows the typical flow:
1. User runs `python main.py input.xml output.xml`
2. XMLHandler initializes the tagger (which sets up NER if available)
3. For each paragraph, we extract entities and apply tags
4. The final XML is written to the output file

Notice the **HYBRID vs FALLBACK** decision point—if spaCy isn't installed, we automatically fall back to regex-only mode without crashing.

---

### 3.4 Entity Extraction Pipeline

![Entity Extraction Pipeline](../diagrams/Entity%20Extraction%20Pipeline.png)

*Figure 4: The layered extraction process with priorities*

Extraction happens in layers, from highest to lowest priority:

- **Layer 1 (P100-85)**: Context-specific patterns that need to be checked first
- **Layer 2 (P80)**: Company names using our hybrid NER + regex approach
- **Layer 3 (P70-60)**: Financial amounts and concepts
- **Layer 4 (P50)**: General dates as a catch-all

This ordering ensures specific matches aren't overwritten by general ones.

---

### 3.5 Overlap Resolution Algorithm

![Overlap Resolution Algorithm](../diagrams/Overlap%20Resolution%20Algorithm.png)

*Figure 5: How we handle conflicting matches*

The algorithm is straightforward but effective:

1. Sort all entities by position, then by priority (highest first), then by length (longest first)
2. Walk through the sorted list
3. If an entity doesn't overlap with what we've already accepted, keep it
4. If it overlaps, skip it (a higher-priority entity already claimed that text)

**Real Example**:
```
Text: "incorporated on January 24, 2011"

Found entities:
- "January 24, 2011" as IncorporationDate (P:100)
- "January 24, 2011" as Date_Placeholder (P:50)
- "2011" as Date_Placeholder (P:50)

After resolution:
- "January 24, 2011" as IncorporationDate ← Only this survives
```

---

### 3.6 Subsection Detection

![Subsection Detection Algorithm](../diagrams/Subsection%20Detection%20Algorithm.png)

*Figure 6: How paragraphs get grouped into sections*

The detector looks for patterns to classify paragraphs:

- **Headers**: Start with a number and period, mostly uppercase (e.g., "1. NATURE OF OPERATIONS")
- **Going Concern**: Contains phrases like "going concern" or "material uncertainty"
- **Operations**: Everything else in the main content area

Headers get a special flag (`skip_tagging = True`) because we don't want to tag entities inside section titles.

---

### 3.7 Component Architecture

![Component Architecture](../diagrams/Component%20Architecture.png)

*Figure 7: Module dependencies and project organization*

The project is organized into clear layers:
- **Entry Point**: `main.py` ties everything together
- **Core (src/)**: The actual processing logic
- **Tests**: Unit tests and edge case coverage
- **Verification**: Scripts to validate accuracy, determinism, and performance

The optional spaCy dependency is shown with a dashed line—the system works fine without it.

---

### 3.8 Extraction Mode Selection

![Extraction Mode Selection](../diagrams/Extraction%20Mode%20Selection.png)

*Figure 8: HYBRID vs FALLBACK mode decision tree*

When the tagger initializes:
1. Check if NER is enabled in configuration
2. If yes, try to load the spaCy model
3. Success → **HYBRID mode** (best accuracy, handles variations)
4. Failure → **FALLBACK mode** (still accurate, zero dependencies)

Both modes produce correct results for our test cases. HYBRID mode is better at handling company name variations that weren't explicitly programmed.

---

## 4. How the Algorithms Work

### 4.1 Entity Extraction

Here's the core extraction logic in pseudocode:

```python
def extract_entities(text):
    entities = []
    
    # Layer 1: High-priority patterns
    entities += find_incorporation_dates(text)   # P:100
    entities += find_addresses(text)             # P:90
    entities += find_trading_symbols(text)       # P:85
    
    # Layer 2: Company names (hybrid approach)
    entities += find_company_names(text)         # P:80
    
    # Layer 3: Financial data
    entities += find_amounts(text)               # P:70
    entities += find_financial_concepts(text)    # P:60
    
    # Layer 4: General dates
    entities += find_dates(text)                 # P:50
    
    # Remove overlaps, keeping highest priority
    entities = resolve_overlaps(entities)
    
    return sorted(entities, by=position)
```

### 4.2 Overlap Resolution

```python
def resolve_overlaps(entities):
    # Sort by: position, then priority (desc), then length (desc)
    sorted_entities = sort(entities, key=(start, -priority, -length))
    
    result = []
    last_end = -1
    
    for entity in sorted_entities:
        if entity.start >= last_end:
            # No overlap—accept this entity
            result.append(entity)
            last_end = entity.end
        # Otherwise, skip (it overlaps with a higher-priority match)
    
    return result
```

### 4.3 Key Regex Patterns

```python
# Full date: "January 24, 2011"
FULL_DATE = r'(January|February|...|December)\s+\d{1,2},\s+\d{4}'

# Financial amount: "$19,821" or "$1,234.56"
AMOUNT = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?'

# Incorporation context: captures the date after "incorporated...on"
INCORPORATION = r'was incorporated.*?on\s+(' + FULL_DATE + ')'

# Trading symbol: "BCL" in quotes
SYMBOL = r'under the symbol\s+["\u201C]([A-Z]{2,5})["\u201D]'
```

---

## 5. Project Structure

```
assignment1/
├── main.py                    # Entry point - run this
├── requirements.txt           # Dependencies (minimal!)
├── README.md                  # Quick start guide
│
├── src/                       # Core source code
│   ├── __init__.py
│   ├── config.py              # Patterns, priorities, tag IDs
│   ├── ner_module.py          # spaCy integration
│   ├── tagger.py              # Main extraction logic
│   └── xml_handler.py         # XML parsing and generation
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_tagger.py         # Unit tests
│   └── test_edge_cases.py     # Edge case coverage
│
├── verification/              # Verification scripts
│   ├── verify_accuracy.py     # Compare with expected output
│   ├── verify_determinism.py  # Ensure consistent results
│   ├── verify_completeness.py # Check for missing tags
│   ├── benchmark_performance.py
│   └── run_all_verifications.py
│
├── data/                      # Input and expected output
│   ├── note_1_input_v1_1.xml
│   └── note_1_expected_output_v1_1.xml
│
├── diagrams/                  # System design diagrams
│   └── *.png
│
├── docs/                      # Documentation
│   ├── DESIGN.md              # This file
│   ├── ENGINEERING.md
│   └── PERFORMANCE.md
│
└── output/                    # Generated output files
```

---

## 6. Testing & Verification

### 6.1 Test Coverage

We have comprehensive tests covering all functionality:

| Category | Test Count | What's Covered |
|----------|------------|----------------|
| Entity Extraction | 8 tests | Each entity type |
| Overlap Resolution | 3 tests | Priority handling, edge cases |
| Subsection Detection | 4 tests | Headers, grouping logic |
| XML Handling | 4 tests | Parse, generate, round-trip |
| Edge Cases | 25+ tests | Unicode, empty input, boundaries |
| **Total** | **44+ tests** | **100% coverage** |

### 6.2 Verification Suite

Run all verifications with one command:

```bash
python verification/run_all_verifications.py
```

This checks:
- **Accuracy**: Do our tags match the expected output? (Target: ≥99%)
- **Determinism**: Same input → same output, every time
- **Completeness**: No expected tags missing from our output
- **Performance**: Can we handle 30 notes efficiently?

### 6.3 Sample Verification Output

```
================================================================================
FINAL VERIFICATION REPORT
================================================================================

RESULTS SUMMARY:
----------------------------------------------------------------------
PASS       | ACCURACY (100%)
PASS       | DETERMINISM (5 identical runs)
PASS       | COMPLETENESS (0 missing tags)
PASS       | PERFORMANCE (352 notes/sec)
----------------------------------------------------------------------

OVERALL STATUS: READY FOR SUBMISSION ✓
================================================================================
```

---

## 7. Performance Deep Dive

### 7.1 Where Time Goes

| Component | Complexity | Typical Time |
|-----------|------------|--------------|
| XML Parsing | O(n) | ~5ms |
| Subsection Detection | O(m) | <0.1ms |
| Entity Extraction | O(m × p) | ~1ms |
| Overlap Resolution | O(e log e) | <0.1ms |
| XML Generation | O(m + e) | <0.1ms |
| **Total per note** | - | **~8ms** |

*Where: n = file size, m = paragraphs, p = patterns, e = entities*

### 7.2 Scalability Results

| Notes | Time | Throughput |
|-------|------|------------|
| 10 | 0.03s | 378 notes/sec |
| 20 | 0.05s | 377 notes/sec |
| 30 | 0.09s | 352 notes/sec |

The requirement was to handle 20-30 notes efficiently. We can process **352 notes per second**—that's over 21,000 notes per minute if needed.

### 7.3 Why It's Fast

1. **Compiled Regex**: Patterns are compiled once at startup, not on every match
2. **Early Exit**: High-priority patterns are checked first; if found, we don't need to check overlapping lower-priority ones
3. **Efficient Sorting**: O(e log e) overlap resolution instead of O(e²) pairwise comparison
4. **Minimal Dependencies**: Core functionality uses only Python standard library

---

## Appendix A: Tag Reference

| Tag Type | Tag ID | When Used |
|----------|--------|-----------|
| Note Root | `NatureOfOperationsAndGoingConcernNote` | Wraps entire note |
| Header | `NatureOfOperationsAndGoingConcernHeader` | Section titles |
| Operations | `DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities` | Business description |
| Going Concern | `DescriptionOfUncertaintiesOfEntitysAbilityToContinueAsGoingConcern` | Risk disclosures |
| Company Name | `NameOfReportingEntityOrOtherMeansOfIdentification` | "BestCo Ltd." |
| Inc. Date | `IncorporationDate` | Date of incorporation |
| Address | `AddressOfRegisteredOfficeOfEntity` | Office location |
| Symbol | `EntityPrimaryTradingSymbol` | "BCL" |
| Date | `Date_Placeholder` | General dates |
| Amount | `Financial_Amount_Placeholder` | "$19,821" |
| Concept | `Financial_Concept_Placeholder` | "working capital deficiency" |

---

## Appendix B: Example Transformation

**Input:**
```xml
<paragraph block_index="15">
BestCo Ltd. was incorporated on January 24, 2011.
The Company has a working capital deficiency of $19,821.
</paragraph>
```

**Output:**
```xml
<paragraph block_index="15">
<Tag id="NameOfReportingEntityOrOtherMeansOfIdentification">BestCo Ltd.</Tag>
was incorporated on
<Tag id="IncorporationDate">January 24, 2011</Tag>.
The Company has a
<Tag id="Financial_Concept_Placeholder">working capital deficiency</Tag>
of <Tag id="Financial_Amount_Placeholder">$19,821</Tag>.
</paragraph>
```

---

**Author:** Ishmeet Singh Arora  
**Date:** January 2025  
**Assignment:** 1 - Vertical Parsing & Tagging
