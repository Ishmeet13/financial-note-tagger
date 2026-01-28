# Assignment 1: Vertical Parsing & Tagging

**Financial Note Disclosure Tagger - Hybrid Approach**

A production-grade Python solution for parsing and tagging financial statement notes with structured XML tags. Uses a hybrid methodology combining regex patterns, NER (Named Entity Recognition), and dictionary matching to identify dates, company information, financial concepts, and numeric values.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Design Approach](#design-approach)
- [Testing & Verification](#testing--verification)
- [Performance](#performance)
- [Documentation](#documentation)

---

## Overview

This solution addresses the core requirements of Assignment 1 using a hybrid approach:

- **Subsection Detection**: Identifies headers and logical sections within financial notes
- **Entity Extraction**: Detects and tags dates, company names, financial amounts, and concepts
- **Structured Output**: Generates properly formatted XML with semantic tags
- **Accurate Tagging**: Uses regex + NER + dictionary matching with priority-based resolution

### Key Results

| Metric | Result | Requirement |
|--------|--------|-------------|
| Accuracy | 100% | >= 99% |
| Throughput | 1,337 notes/sec | Handle 20-30 notes |
| Determinism | 100% identical | Consistent output |
| Completeness | 0 missing tags | Full coverage |

---

## Features

### Entity Types Detected

1. **Dates** (Regex)
   - Full dates: "January 24, 2011"
   - Month-Year: "December 31, 2023"
   - Special: Incorporation dates with context

2. **Company Information** (Hybrid: NER + Regex)
   - Company names: "BestCo Ltd."
   - Addresses: "13th Floor, 1313 Lucky Street, Vancouver, BC..."
   - Trading symbols: "BCL"

3. **Financial Data**
   - Amounts (Regex): "$19,821", "$137,942"
   - Concepts (Dictionary): "working capital deficiency", "accumulated deficit"

4. **Subsections**
   - Nature of Operations
   - Going Concern disclosures
   - Headers and organizational structure

### Extraction Modes

**HYBRID Mode** (with spaCy installed):
```
Extraction Mode: HYBRID (Regex + NER + Dictionary)
```
- Uses all three extraction methods
- Best accuracy and flexibility

**FALLBACK Mode** (without spaCy):
```
Extraction Mode: FALLBACK (Regex + Dictionary only)
```
- Zero external dependencies
- Faster execution
- Still excellent accuracy

---

## Project Structure

```
assignment1/
|-- main.py                    # Entry point
|-- requirements.txt           # Dependencies
|-- README.md                  # This file
|
|-- src/                       # Source code
|   |-- __init__.py
|   |-- config.py              # Patterns & configuration
|   |-- ner_module.py          # NER integration
|   |-- tagger.py              # Core tagging logic
|   |-- xml_handler.py         # XML parsing & generation
|
|-- tests/                     # Test suite
|   |-- __init__.py
|   |-- test_tagger.py         # Unit tests
|   |-- test_edge_cases.py     # Edge case tests
|
|-- verification/              # Verification scripts
|   |-- verify_accuracy.py     # Accuracy verification
|   |-- verify_determinism.py  # Determinism verification
|   |-- verify_completeness.py # Completeness check
|   |-- benchmark_performance.py
|   |-- run_all_verifications.py
|
|-- data/                      # Input files
|   |-- note_1_input_v1_1.xml
|   |-- note_1_expected_output_v1_1.xml
|
|-- diagrams/                  # UML diagrams
|   |-- System Architecture.png
|   |-- Class Diagram.png
|   |-- Sequence Diagram.png
|   |-- Entity Extraction Pipeline.png
|   |-- Overlap Resolution Algorithm.png
|   |-- Subsection Detection Algorithm.png
|   |-- Component Architecture.png
|   |-- Extraction Mode Selection.png
|
|-- docs/                      # Documentation
|   |-- DESIGN.md              # System design document
|   |-- ENGINEERING.md         # Engineering decision log
|   |-- PERFORMANCE.md         # Performance analysis
|
|-- output/                    # Generated outputs
    |-- note_1_output.xml
```

---

## Installation

### Option 1: Full Installation (Recommended)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (optional, for HYBRID mode)
python -m spacy download en_core_web_sm
```

### Option 2: Minimal Installation (No Dependencies)

```bash
# Just run it - uses FALLBACK mode automatically
python main.py data/note_1_input_v1_1.xml output/note_1_output.xml
```

The system automatically detects available features and adapts accordingly.

---

## Usage

### Basic Usage

```bash
python main.py <input_xml> <output_xml>
```

### Examples

**Process the provided sample note:**
```bash
python main.py data/note_1_input_v1_1.xml output/note_1_output.xml
```

**Sample Output:**
```
================================================================================
Financial Note Tagger - Assignment 1
================================================================================

Extraction Mode: FALLBACK (Regex + Dictionary only)

Processing: data/note_1_input_v1_1.xml
  Found 6 paragraphs
  Output saved to: output/note_1_output.xml
[OK] Processing complete!

================================================================================
STATISTICS
================================================================================
Extraction Mode: FALLBACK
Regex extractions:      15
NER extractions:        0
Dictionary extractions: 4
Total entities:         19
```

---

## Design Approach

### Hybrid Extraction Strategy

| Method | Strengths | When Used |
|--------|-----------|-----------|
| **Regex** | Fast, deterministic | Structured patterns (dates, amounts) |
| **NER** | Context-aware | Complex entities (company names) |
| **Dictionary** | Domain-specific | Financial concepts |

### Priority Hierarchy

```
Priority 100: Incorporation Date (context-specific)   [Regex]
Priority 90:  Registered Address (complex pattern)    [Regex]
Priority 85:  Trading Symbol (specific context)       [Regex]
Priority 80:  Company Name (hybrid approach)          [NER + Regex]
Priority 70:  Financial Amount ($ pattern)            [Regex]
Priority 60:  Financial Concept (dictionary)          [Dictionary]
Priority 50:  General Date (broad pattern)            [Regex]
```

**Why priority matters:**
When "January 24, 2011" appears in "incorporated on January 24, 2011":
- Priority 50: `<Tag id="Date_Placeholder">January 24, 2011</Tag>`
- Priority 100: `<Tag id="IncorporationDate">January 24, 2011</Tag>` (wins!)

---

## Testing & Verification

### Run All Tests

```bash
# Run unit tests
python -m pytest tests/ -v

# Or run directly
python tests/test_tagger.py
```

### Run Verification Suite

```bash
python verification/run_all_verifications.py
```

**Expected Output:**
```
======================================================================
FINAL VERIFICATION REPORT
======================================================================
RESULTS SUMMARY:
----------------------------------------------------------------------
PASS       | ACCURACY
PASS       | DETERMINISM
PASS       | COMPLETENESS
PASS       | PERFORMANCE
----------------------------------------------------------------------
```

### Individual Verification Scripts

```bash
# Check accuracy
python verification/verify_accuracy.py

# Check determinism
python verification/verify_determinism.py

# Check completeness
python verification/verify_completeness.py

# Benchmark performance
python verification/benchmark_performance.py data/note_1_input_v1_1.xml
```

---

## Performance

### Benchmark Results

| Notes | Total Time | Avg/Note | Throughput |
|-------|-----------|----------|------------|
| 10 | 0.01s | 0.66ms | 1,505 notes/sec |
| 20 | 0.01s | 0.66ms | 1,511 notes/sec |
| 30 | 0.02s | 0.75ms | 1,337 notes/sec |

### Why It's Fast

1. **Compiled Regex**: Patterns compiled once at startup
2. **Efficient Sorting**: O(e log e) overlap resolution
3. **Minimal Dependencies**: Uses Python standard library
4. **Streaming Processing**: Constant memory usage

---

## Documentation

Comprehensive documentation is available in the `docs/` folder:

| Document | Description |
|----------|-------------|
| [DESIGN.md](docs/DESIGN.md) | System architecture, algorithms, UML diagrams |
| [ENGINEERING.md](docs/ENGINEERING.md) | Engineering decisions, challenges, iterations |
| [PERFORMANCE.md](docs/PERFORMANCE.md) | Complexity analysis, benchmarks, scalability |

---

## Output Example

### Input:
```xml
<paragraph block_index="15">
BestCo Ltd. was incorporated on January 24, 2011.
The Company has a working capital deficiency of $19,821.
</paragraph>
```

### Output:
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

## Author

**Ishmeet Singh Arora**

Assignment 1: Vertical Parsing & Tagging  
January 2025

---

## License

This code is submitted as part of a technical assessment and is intended for evaluation purposes only.
