5. Phase-Wise Implementation Plan (LangChain, sequential pipeline)
Phase	What Gets Built	LangChain Component Used
0	Repo scaffold: requirements.txt, .env.example, folder structure (data/, src/, eval/)	—
1	Mock data: two realistic CSVs (purchase_orders.csv, receipts.csv) loaded into SQLite	SQLDatabase.from_uri()
2	Schema-grounded SQL generation chain — takes the question + real schema (auto-pulled from the DB, not hand-typed) + a handful of few-shot examples, outputs SQL	SQLDatabase.get_table_info() + PromptTemplate + LCEL (prompt | llm | StrOutputParser())
3	Validation/guard layer (plain Python, not an LLM call) — rejects anything that isn't a read-only SELECT, or that references a table/column outside the whitelist	Custom code — this is the reliability layer, deliberately not LLM-based
4	Execute the validated query against real data	SQLDatabase.run()
5	Ambiguity-detection chain — a small classification step run before generation, flags underspecified terms (e.g. "pending") and returns a clarifying question instead of proceeding	Small LCEL classification chain
6	Answer-composition chain — takes only the returned rows + the question, and is explicitly instructed never to state a number not present in those rows	LCEL chain, strict prompt
7	Refusal path — no-match / out-of-schema questions get an honest "not available," not a guess	Extends phase 3+6 logic
8	Minimal chat UI wired to the pipeline	Streamlit
9	Accuracy evaluation harness — a fixed set of ~25-30 test questions (simple lookups, aggregates, ambiguous, out-of-schema, edge cases) with expected outcomes, run automatically, scored	Plain Python eval script, no LangChain needed here
10	Audit trail — every answer displayed with the exact SQL that produced it	UI layer
11	README finalization, assumptions section, demo script rehearsal, video recording	
12	Final submission checklist verification	
6. The 90% Accuracy Requirement — how we actually enforce it
"90% accuracy" needs a precise, testable definition or it's just a nice-sounding number. Here's how Phase 9 makes it real and non-negotiable:

Build a fixed evaluation set of ~25-30 questions covering every category (simple lookup, multi-condition aggregate, ambiguous, out-of-schema, edge case) with a known-correct expected answer for each.
Run the full pipeline against all of them automatically and score: did it return the correct grounded answer, correctly ask for clarification, or correctly refuse (as appropriate)?
The rule going forward: we do not move to UI polish, demo scripting, or README finalization until this eval script reports ≥90% pass rate. If it's below that, we go back and fix the prompt, the few-shot examples, or the validation rules — not skip ahead. I'll flag this explicitly every time we check progress so it doesn't get glossed over under time pressure.
One structural advantage you already have: because bad queries get rejected by the validation layer rather than executed, your realistic hallucination rate on wrong-answer cases should be near 0% by construction — the 90% target is really about query-translation correctness, which is the part actual prompt iteration improves.
7. What You Might Have Missed
.env handling — API key must never be committed. .env.example with a placeholder key, real .env gitignored.
eval_questions.json — check this into the repo. Showing your actual test set and pass-rate is a strong, concrete "here's how I know it's 90% accurate" artifact for the demo and for interview follow-ups.
LICENSE (MIT) — standard, expected on a public portfolio repo.
A short "Limitations" section in the README — explicitly listing what's out of scope (no real SAP integration, no auth, single-user). This directly satisfies the brief's "state your assumptions" ground rule and looks like maturity, not a gap.
Cost/latency note — one line in the README about which LLM/model you used and roughly why (cost, speed, or familiarity) — a common interview question you'll now have pre-answered.
8. README.md — Ready to Paste
# Ledger Detective
**A grounded, LLM-powered chat assistant for SAP-style purchase order / goods-receipt
reconciliation.** Every answer is traced to an executed database query against real data
— never guessed, never hallucinated.
Built for the Supervity Forward Deployed Engineer (FDE) technical screening assessment
(Problem 8 — SAP-Style Data Reconciliation Chatbot).
## The Problem
Given two mock exports resembling SAP tables — a purchase order header/line table and a
goods-receipt/invoice-receipt table — build a chat interface where a user can ask
natural-language questions and receive accurate, data-grounded answers.
Requirements:
- Load both mock tables into a queryable structure
- Translate natural-language questions into correct queries against the data
- Return answers grounded in the actual data, never hallucinated
- Handle at least one aggregate or multi-condition question
## Architecture — Why It's a Pipeline, Not an Agent
This project deliberately avoids LangChain's autonomous `create_sql_agent` pattern.
An agent loop re-plans and calls tools an unpredictable number of times, which makes it
harder to guarantee, inspect, or explain why an answer is correct. Instead, this system
is a single, fixed, sequential pipeline:
User question ↓ [1] Ambiguity check — is the question underspecified? If yes, ask for clarification and stop. ↓ [2] SQL generation — LLM generates SQL, grounded in the real schema (auto-pulled from the DB) ↓ [3] Validation (code, not LLM) — reject anything that isn't a read-only SELECT on known tables/columns ↓ [4] Execution — run the validated query against the real SQLite data ↓ [5] Answer composition — LLM phrases the answer using ONLY the returned rows ↓ Answer + the exact SQL used, shown to the user

Every run takes the same path, in the same order. Nothing is hidden.
## Tech Stack
- **Python** — application logic
- **LangChain** (`SQLDatabase`, `PromptTemplate`, LCEL chains) — schema introspection,
  prompt orchestration, and safe query execution
- **SQLite** — queryable store for the two mock tables
- **Streamlit** — minimal chat interface
- **[Your LLM provider of choice]** — question-to-SQL translation and answer composition
## Setup
```bash
git clone https://github.com/<your-username>/ledger-detective.git
cd ledger-detective
pip install -r requirements.txt
cp .env.example .env   # add your LLM API key
streamlit run src/app.py
Assumptions
Mock data is fully synthetic — no real customer or SAP data is used.
Single-user, single-session chat; no authentication is implemented.
"Queryable structure" is implemented as a local SQLite database rather than a live SAP connection.
Each question is handled independently (no multi-turn memory), unless noted otherwise.
Accuracy & Evaluation
Correctness is measured against a fixed set of test questions in eval/eval_questions.json, covering simple lookups, multi-condition aggregates, ambiguous questions, and out-of-schema questions. The pipeline targets ≥90% pass rate on this set before being considered demo-ready; results are logged in eval/results.md.

Limitations (out of scope for this assessment)
No real SAP/ERP integration
No authentication/authorization
No persistence or write-back to source systems
No production deployment — designed to run locally for demo purposes
About the Author
Adhimulam Bhargav Sai Viswanath B.Tech, Computer Science & Engineering (AI & ML) — VVIT, 2023–2027 (4th year), CGPA ~8.36 AI Engineer Intern @ Paytm (since June 2026) Lead, Con-VRAG (Vision-RAG research project) — VVIT-VisionRAG on GitHub & Hugging Face Member, AI-HUB@VVIT student community

License
MIT


Once this is pushed and Cursor has read it, tell it to summarize back to you per the first prompt above, confirm the plan matches what's here, and we'll start relaying Phase 0 and Phase 1 instructions into Cursor together.
