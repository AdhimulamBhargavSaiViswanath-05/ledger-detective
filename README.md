# Ledger Detective 🔍

A grounded LLM chat assistant for SAP-style procurement data reconciliation. Built with a fixed pipeline architecture (not an autonomous agent) for predictability and safety.

Query purchase orders, goods receipts, and invoices using natural language - powered by three-way matching and comprehensive data validation.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python3 -c "from src.db import init_database; init_database()"

# 3. Run Streamlit UI
USE_MOCK_LLM=true streamlit run app.py
```

## Project Overview

**Goal**: Answer natural language questions about SAP-style procurement data by translating them to SQL queries with full data grounding.

**Database**: 5 interconnected tables with 900+ records representing real-world procurement scenarios:
- **PO Headers** (120 records) - Purchase order headers
- **PO Items** (242 records) - Purchase order line items  
- **Goods Receipts** (268 records) - Physical material receipts
- **Invoices** (101 records) - Vendor invoice headers
- **Invoice Items** (185 records) - Invoice line items

**Architecture**: Fixed sequential pipeline (no autonomous loops)
```
Question → Ambiguity Check → SQL Generation → Validation → Execution → Answer Composition
```

**Key Capabilities**:
- ✅ Three-way matching (PO → GR → Invoice)
- ✅ Price variance detection
- ✅ Quantity reconciliation
- ✅ Missing document identification
- ✅ Vendor performance analysis
- ✅ Multi-table joins and complex aggregations

## Features

✅ **Safety First**: Multi-layer validation prevents SQL injection and dangerous queries  
✅ **Explainable**: Every component is simple, testable, and auditable  
✅ **Mock LLM Included**: Develop and test without API keys  
✅ **Real LLM Ready**: Switch to OpenAI or Gemini anytime (see `SWITCHING_TO_REAL_LLM.md`)

## Running Tests

```bash
# All tests
USE_MOCK_LLM=true pytest

# Specific phase
USE_MOCK_LLM=true pytest tests/test_validation.py -v

# Evaluation harness
USE_MOCK_LLM=true python3 eval/run_eval.py
```

## Project Structure

```
ledger-detective/
├── app.py                  # Streamlit UI
├── src/
│   ├── db.py              # Database layer (5-table SAP schema)
│   ├── pipeline.py        # End-to-end orchestration
│   └── chains/
│       ├── sql_generation.py       # NL → SQL
│       ├── validation.py           # SQL safety checks
│       ├── execution.py            # Safe SQL execution
│       ├── answer_composition.py   # SQL results → NL
│       ├── ambiguity_check.py      # Underspecified question detection
│       ├── refusal.py              # Out-of-scope handling
│       └── mock_llm.py             # Development mock
├── scripts/
│   └── generate_enhanced_data.py   # Data generation script
├── tests/                  # Comprehensive test suite
├── eval/                   # Evaluation harness
├── data/                   # 5 CSV files (900+ records)
│   ├── po_headers.csv
│   ├── po_items.csv
│   ├── goods_receipts.csv
│   ├── invoices.csv
│   └── invoice_items.csv
└── docs/
    ├── DATABASE_SCHEMA.md          # Schema documentation
    └── EXAMPLE_QUERIES.md          # Query examples
```

## Documentation

- **`DATABASE_SCHEMA.md`** - Complete schema documentation with relationships and examples
- **`EXAMPLE_QUERIES.md`** - 50+ natural language queries with expected SQL
- **`SWITCHING_TO_REAL_LLM.md`** - How to use OpenAI or Gemini
- **`PLAN.md`** - Phase-by-phase implementation plan
- **`PROGRESS.md`** - Development log and blockers
- **`ProblemSelection_Process.md`** - Project rationale

## Tech Stack

- **LangChain**: SQL generation, answer composition  
- **SQLite**: Local database  
- **Streamlit**: Chat UI  
- **pytest**: Testing framework

## Example Questions

### Basic Queries
- "How many purchase orders are there?"
- "Which vendors have the most purchase orders?"
- "What is the total value of all invoices?"

### Reconciliation Queries
- "Which purchase orders have no goods receipts?"
- "Show me unmatched receipts over $100,000"
- "Which invoices have price variances from the PO?"

### Three-Way Match Analysis
- "Show me the three-way match status for all POs"
- "Which line items have quantity variances between receipt and invoice?"
- "Find over-invoiced items"

### Vendor Performance
- "Show me vendor performance summary"
- "Which vendors have the most delivery delays?"

**See `EXAMPLE_QUERIES.md` for 50+ more example queries with expected SQL output.**

## Development Notes

Currently using **Mock LLM** for development (no API costs). The mock enables:
- Unit testing without external dependencies
- Predictable SQL for specific questions
- Fast iteration

**For production**: Add real API key (see `SWITCHING_TO_REAL_LLM.md`)

## License

MIT

## Author

Developed as a portfolio project demonstrating:
- LangChain expertise
- SQL safety and validation
- Grounded LLM systems (vs. autonomous agents)
- Test-driven development
