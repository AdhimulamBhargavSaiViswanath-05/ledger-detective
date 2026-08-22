# How to Run

## Quick Start (Mock LLM - No API Key Needed)
```bash
pip install -r requirements.txt
USE_MOCK_LLM=true streamlit run app.py
```

## With Real LLM (OpenAI or Gemini)
See SWITCHING_TO_REAL_LLM.md for instructions.

## Run All Tests
```bash
USE_MOCK_LLM=true pytest
```

## Run Evaluation
```bash
USE_MOCK_LLM=true python3 eval/run_eval.py
```

