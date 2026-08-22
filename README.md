# Ledger Detective 🔍

A grounded LLM chat assistant for querying purchase orders and receipts data. Built with a fixed pipeline architecture (not an autonomous agent) for predictability and safety.

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

**Goal**: Answer natural language questions about purchase orders and receipts by translating them to SQL queries.

**Architecture**: Fixed sequential pipeline (no autonomous loops)
```
Question → Ambiguity Check → SQL Generation → Validation → Execution → Answer Composition
```

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
│   ├── db.py              # Database layer
│   ├── pipeline.py        # End-to-end orchestration
│   └── chains/
│       ├── sql_generation.py       # NL → SQL
│       ├── validation.py           # SQL safety checks
│       ├── execution.py            # Safe SQL execution
│       ├── answer_composition.py   # SQL results → NL
│       ├── ambiguity_check.py      # Underspecified question detection
│       ├── refusal.py              # Out-of-scope handling
│       └── mock_llm.py             # Development mock
├── tests/                  # Comprehensive test suite
├── eval/                   # Evaluation harness
└── data/                   # Mock SAP-style data
```

## Documentation

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

- "How many purchase orders are there?"
- "What is the value of PO 4500123?"
- "What is the total amount invoiced?"
- "Which vendors have supplied materials?"

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
