# Switching from Mock LLM to Real LLM

## Current Setup (Mock LLM)

The project currently uses a **MockSQLGenerationLLM** for development and testing. This mock returns predefined SQL queries for common questions, allowing the system to function without requiring API keys or credits.

## Why Mock LLM?

- ✅ No API costs during development/testing
- ✅ Consistent, predictable responses
- ✅ Fast execution (no network calls)
- ✅ All tests pass reliably
- ❌ Limited to predefined questions only
- ❌ Not suitable for production use

## How to Switch to Real LLM

### Option 1: OpenAI (Recommended for Production)

1. **Get API Key:**
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Add billing/credits to your account

2. **Update `.env` file:**
   ```bash
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Install dependencies:**
   ```bash
   pip install langchain-openai
   ```

4. **The system auto-detects** - No code changes needed!
   - `sql_generation.py` checks for `OPENAI_API_KEY`
   - If present, uses `ChatOpenAI` automatically
   - Priority: OpenAI > Gemini > Mock

### Option 2: Google Gemini

1. **Get API Key:**
   - Visit https://aistudio.google.com/api-keys
   - Create a new API key

2. **Update `.env` file:**
   ```bash
   GEMINI_API_KEY=your-actual-key-here
   ```

3. **Install dependencies:**
   ```bash
   pip install langchain-google-genai
   ```

4. **System auto-switches** when it detects the key

### Option 3: Force Mock (for Testing)

To explicitly use mock LLM even when API keys are present:

```bash
# In .env file
USE_MOCK_LLM=true
```

## LLM Selection Priority

The system checks in this order:

1. **`USE_MOCK_LLM=true`** → Always use mock
2. **`OPENAI_API_KEY` present** → Use OpenAI GPT-4o-mini
3. **`GEMINI_API_KEY` present** → Use Google Gemini
4. **No keys** → Fallback to mock (with warning)

## Verification

To confirm which LLM is being used:

```python
from src.chains.sql_generation import get_sql_generation_chain

chain = get_sql_generation_chain()
print(f"Using LLM: {chain.middle[0]._llm_type}")  
# Output: "openai" or "google-genai" or "mock-sql-generation"
```

## Code Location

All LLM selection logic is in:
- `src/chains/sql_generation.py` - Lines 72-95 (LLM selection)
- `src/chains/mock_llm.py` - Mock implementation

## Production Deployment

**Before deploying to production:**

1. ✅ Add valid OpenAI or Gemini API key to `.env`
2. ✅ Verify tests pass with real LLM: `pytest tests/test_sql_generation.py -v`
3. ✅ Remove or set `USE_MOCK_LLM=false`
4. ✅ Test with real user questions in Streamlit UI

## Troubleshooting

**Tests fail with real LLM:**
- Check API key is valid and has credits
- Verify model name is correct (`gpt-4o-mini` or `models/gemini-1.5-flash-latest`)
- Check network access is allowed

**Mock LLM not producing good SQL:**
- Edit `src/chains/mock_llm.py`
- Add your question to `_sql_map` dictionary
- Map it to the correct SQL query

**Want to use different model:**
- Edit `src/chains/sql_generation.py`
- Change model name in `ChatOpenAI()` or `ChatGoogleGenerativeAI()`
- Example: `model="gpt-4"` for GPT-4

---

**Last Updated:** Phase 3 Implementation  
**Status:** Using Mock LLM (no API key required)
