# LLM-Driven Design Philosophy

## Core Principle

**The scope is the scope of the datasets.**

There are NO hardcoded restrictions on what questions can be answered. The LLM makes ALL decisions based on:
1. Available database schema
2. User question intent
3. Its own intelligence

---

## Design Changes

### ❌ Removed (Hardcoded Rules)

1. **Refusal Check** (`src/chains/refusal.py`)
   - No hardcoded keyword lists
   - No pre-filtering before LLM sees the question
   
2. **SQL Lookup Dictionary** (`MockSQLGenerationLLM._sql_map`)
   - No predefined question→SQL mappings
   - LLM generates SQL dynamically

3. **Ambiguity Keywords List** (`AMBIGUOUS_TERMS`)
   - No hardcoded list of ambiguous terms
   - LLM decides if clarification is needed

### ✅ Kept (LLM Intelligence)

1. **Schema Context**
   - LLM receives full database schema
   - Understands available tables/columns
   
2. **Three-Way Decision**
   - Generate SQL (answerable)
   - Ask clarification (ambiguous)
   - Refuse gracefully (out of scope)

3. **Validation Layer** (Security Only)
   - SQL injection prevention
   - Dangerous keyword blocking
   - Table/column whitelisting
   - **This is NOT about business logic, only security**

---

## How It Works

### LLM Prompt Structure

```
Available Database Schema:
- purchase_orders (po_number, vendor_name, po_value, ...)
- receipts (gr_number, invoice_amount, ...)

User Question: {question}

Your task:
1. Can this be answered from available data?
2. Is the question clear or ambiguous?
3. Respond with:
   - SQL query (if answerable)
   - NEEDS_CLARIFICATION: ... (if ambiguous)
   - OUT_OF_SCOPE: ... (if not answerable)
```

### Example Scenarios

#### ✅ Answerable (Generate SQL)
- "How many purchase orders?" → `SELECT COUNT(*) FROM purchase_orders;`
- "Which vendors supplied materials?" → `SELECT DISTINCT vendor_name FROM purchase_orders;`
- "Show receipts for PO 4500124" → `SELECT * FROM receipts WHERE po_number = 4500124;`

#### ⚠️ Ambiguous (Ask Clarification)
- "Show me pending ones" → `NEEDS_CLARIFICATION: Do you mean pending receipts or pending invoices?`
- "What's the total?" → `NEEDS_CLARIFICATION: Total of what? PO values or invoice amounts?`

#### ❌ Out of Scope (Refuse Gracefully)
- "What's the weather?" → `OUT_OF_SCOPE: I only have purchase orders and receipts data, not weather information.`
- "Tell me a joke" → `OUT_OF_SCOPE: I can help with PO values, vendors, invoices, and receipt information.`

---

## Why This Design?

### 1. Flexibility
- User can ask questions in any form
- No artificial restrictions
- LLM adapts to query patterns

### 2. Intelligence
- LLM understands context
- Semantic reasoning (not keyword matching)
- Can handle typos, variations, natural phrasing

### 3. Scalability
- Add new tables → LLM auto-discovers them
- Add new columns → LLM auto-uses them
- No code changes needed

### 4. Explainability
- LLM decisions are transparent
- Prompt can be inspected
- No "magic" black boxes

---

## Mock LLM vs Real LLM

### Mock LLM (Current - Development)
- Uses pattern matching as a fallback
- Limited to common query patterns
- Good enough for development/testing
- **~50% accuracy on eval**

### Real LLM (Production - OpenAI/Gemini)
- True semantic understanding
- Handles any query variation
- Learns from examples in prompt
- **≥90% expected accuracy**

---

## Migration Path

To switch to real LLM:

1. Add API key to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   # OR
   GEMINI_API_KEY=AQ...
   ```

2. Remove mock flag:
   ```bash
   # Comment out or remove:
   # USE_MOCK_LLM=true
   ```

3. Restart app:
   ```bash
   streamlit run app.py
   ```

That's it! The LLM-driven architecture stays the same.

---

## Key Takeaway

**This is an LLM system.** The LLM has full autonomy to decide what can be answered based on available data. No hardcoded restrictions. The scope is defined by the database schema, not by rules.
