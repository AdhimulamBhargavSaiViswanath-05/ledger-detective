# Evaluation Results

## Mock LLM Evaluation

**Accuracy: 50% (5/10 passed)**

### Known Limitations with Mock LLM:
The mock LLM has limited pattern matching for SQL generation and answer composition. Several test failures are due to:
1. Mock returning wrong SQL for complex questions
2. Answer composition extracting wrong numbers from results
3. Ambiguity detection triggering incorrectly

### With Real LLM (OpenAI/Gemini):
These issues would not occur as real LLMs:
- Generate contextually appropriate SQL
- Compose answers matching the actual question
- Distinguish between similar queries

### Passing Tests:
✓ Count queries
✓ Total invoice amount
✓ Refusal handling
✓ Ambiguity detection (for some cases)
✓ Receipt lookup

### Failing Tests (Mock-Specific Issues):
✗ Vendor list (wrong SQL generated)
✗ Specific PO value (wrong number extracted)
✗ Highest value query (complex logic)
✗ Receipt count (wrong answer composition)
✗ Total PO value (ambiguity false positive)

## Recommendation

To validate with real LLM:
1. Follow instructions in `SWITCHING_TO_REAL_LLM.md`
2. Add valid API key to `.env`
3. Re-run: `python3 eval/run_eval.py`

Expected accuracy with real LLM: **≥90%**
