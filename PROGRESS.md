# Ledger Detective - Implementation Progress

## Phase 0: Repo Scaffold and Dependencies
**Status:** ✅ Done  
**Commit:** 23d00d8

**Files Created:**
- `.gitignore` - Ignore patterns for .env, __pycache__, *.db, venv/
- `.env.example` - Template for OpenAI API key
- `requirements.txt` - LangChain, pandas, streamlit, sqlparse, python-dotenv, pytest
- `src/__init__.py`, `src/chains/__init__.py` - Python package structure
- `tests/__init__.py` - Test package
- `eval/__init__.py` - Evaluation harness package
- `data/.gitkeep` - Placeholder for data directory

**Tests:**
- ✅ `pip install -r requirements.txt` succeeded (all dependencies installed)
- ✅ `pytest` runs cleanly (exit code 5 - no tests collected, as expected)

**Notes:**
- Used flexible version constraints (>=) in requirements.txt to avoid build issues with exact versions
- Used `--prefer-binary` flag to install pre-built wheels where available
- All directories created and Python packages initialized with __init__.py files

---

## Phase 1: Mock PO and Receipt Datasets
**Status:** ✅ Done  
**Commit:** fc3eca5

**Files Created:**
- `data/purchase_orders.csv` - 10 purchase orders with realistic SAP-style data
- `data/receipts.csv` - 8 receipt records covering various scenarios
- `tests/test_data.py` - 8 tests validating data structure and scenarios

**Test Scenarios Included:**
- PO 4500123: Partially received (80 of 100 units) ✅
- PO 4500124: Fully received (200 of 200 units) ✅
- PO 4500125: No receipt at all ✅
- PO 4500126: Over-invoiced (160 received vs 150 ordered) ✅
- PO 4500132: No receipt (second no-receipt case) ✅

**Tests:**
- ✅ All 8 tests passed (purchase_orders.csv loads, receipts.csv loads, columns correct, scenarios present)

**Notes:**
- Schema matches SAP EKKO/EKPO (PO) and MSEG/RBKP (receipts) structure
- Data includes INR currency, Indian vendor names, realistic material descriptions
- Each scenario needed for eval questions is represented in the data

---

## Phase 2: SQLite Loading + LangChain SQLDatabase Wrapper
**Status:** ✅ Done  
**Commit:** 49d2791

**Files Created:**
- `src/db.py` - Database initialization and access layer
- `tests/test_db.py` - 8 tests validating database functionality

**Functions:**
- `init_database()` - Loads CSVs into SQLite (creates ledger.db)
- `get_database()` - Returns configured LangChain SQLDatabase instance

**Tests:**
- ✅ All 8 tests passed
- Database file created successfully
- Both tables (purchase_orders, receipts) present
- All expected columns exist
- Row counts match source CSVs (10 POs, 8 receipts)

**Notes:**
- Uses LangChain's SQLDatabase.from_uri() for schema introspection
- Database auto-initializes on first get_database() call
- SQLDatabase wrapper provides get_table_info() and run() methods
- One deprecation warning from langchain-community (non-blocking)

---

## Phase 3: Schema-Grounded NL-to-SQL Generation Chain
**Status:** 🛑 BLOCKED - Requires API Key  
**Commit:** 15952b4

**Files Created:**
- `src/chains/sql_generation.py` - LCEL chain for Q→SQL translation
- `tests/test_sql_generation.py` - 17 tests (5 parameterized questions × 3 checks + 2 additional)

**Implementation:**
- LCEL chain: `PromptTemplate | ChatOpenAI | StrOutputParser`
- Schema auto-pulled via `db.get_table_info()` (never hand-typed)
- 5 few-shot examples in prompt template
- Temperature=0 for deterministic output
- Markdown formatting cleanup in post-processing

**Tests:**
- ⚠️ 17 tests SKIPPED (not PASSED)
- Reason: OPENAI_API_KEY environment variable not set
- Tests validate: valid SQL syntax, whitelisted tables only, SELECT-only queries
- Tests cover: 5 known questions, dangerous keywords check, aggregate handling

**BLOCKING ISSUE:**
Per PLAN.md: "Write and run the tests specified for that phase. All of them must pass."

Tests are currently SKIPPED, not PASSING. Cannot proceed to Phase 4 until:
1. User creates `.env` file in project root
2. Adds valid `OPENAI_API_KEY=sk-...` to `.env`
3. Re-runs tests: `python3 -m pytest tests/test_sql_generation.py -v`
4. All 17 tests must show PASSED status

**What I tried:**
- Checked for OPENAI_API_KEY in environment variables (not present)
- Checked for .env file (does not exist)
- Tests are correctly structured to skip when API key missing

**Waiting for:**
User to provide OpenAI API key before continuing to Phase 4.

---
