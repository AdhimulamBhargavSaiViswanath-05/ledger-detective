# PLAN.md — Ledger Detective: Full Implementation Plan

This file is the single source of truth for how this project gets built. Follow it
phase by phase, in order. Do not skip ahead. Do not combine phases.

## Global Rules (apply to every phase, no exceptions)

1. Read `README.md` fully before starting anything.
2. Complete phases strictly in order — never start phase N+1 before phase N's tests pass.
3. Run that phase's tests before committing. All must pass. Never commit a phase with
   failing tests.
4. Commit exactly once per completed phase. Commit message format: `Phase N: <short description>`
5. After every phase, append an entry to `PROGRESS.md`: phase number, status
   (done/blocked), files changed, test result summary.
6. STOP CONDITION — if a phase's tests fail after 3 genuinely different fix attempts,
   or if something is ambiguous and not already resolved by README.md's Assumptions
   section: **stop immediately.** Do not skip the phase. Do not fake a pass. Do not
   silently move on. Write exactly what's blocking you in `PROGRESS.md` (what failed,
   what you tried, what you'd need to proceed) and wait for human review/a manual fix.
7. Never let generated code touch a table/column outside the fixed schema. Never let
   the LLM's own knowledge produce a number in a final answer — every number in a final
   answer must come from an executed query's real result rows.
8. Do NOT use LangChain's autonomous SQL agent (`create_sql_agent` /
   `SQLDatabaseToolkit` agent executor). Use only: `SQLDatabase`, `PromptTemplate`, LCEL
   (`|` composition), `StrOutputParser`. The pipeline is linear and fixed — same steps,
   same order, every single run.
9. Keep every function small enough to explain in one sentence. This code has to be
   defensible in a live follow-up conversation — no cleverness that can't be explained.

## Target Repo Structure