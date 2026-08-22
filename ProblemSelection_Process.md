This is the one to build. Here's the airtight version of "why," written the way you'd actually say it if someone asked — structured so that each sentence closes off the obvious next question instead of opening one.

"I picked the SAP-style reconciliation chatbot because it was the only one of the ten where the LLM's role is structurally necessary rather than decorative — it has to translate an open-ended English question into a real query against two enterprise-style tables, and the answer has to come from executing that query, never from the model narrating a guess. I deliberately avoided the invoice-extraction problems, because OCR robustness on real documents is genuinely unreliable to get right in the time available, and a shaky extraction layer would undermine the exact thing those problems are graded on. This one has almost no such dependency — the risk is contained to the query-translation logic, which I could actually validate and harden. It's also the closest match to what an FDE at a company like Supervity does day one: sit in front of enterprise data that looks exactly like this and answer a business user's question with a number they can trust, not a plausible-sounding one."

Notice what that answer already preempts: it explains the AI-necessity, it explains why you didn't pick the CV-heavy option despite having CV background (turning a possible weakness into a demonstration of judgment), and it ties directly to the role. A good interviewer's natural next move is to probe exactly the things you've already pre-answered — so their follow-up lands on ground you've already covered, which reads as depth, not luck.

The follow-up questions this will actually provoke — and the answers that close each one off
Likely follow-up	Answer that leaves no opening
"Why not the invoice-extraction one, given your CV background?"	"Because the grading criteria for that problem is explicitly the quality of extraction, and PDF/image extraction has high, unpredictable failure variance in a scoped build. I chose the problem where my time went into logic I could fully control and verify, not into a step whose reliability I couldn't guarantee in the time given. That's a scope decision, not an avoidance of difficulty."
"Isn't this just a database with a chat wrapper?"	"The hard part isn't the wrapper, it's guaranteeing the wrapper never lies. Any question I can't confidently translate into a correct query, the system says so explicitly instead of guessing — that refusal path is the actual engineering, not the chat UI."
"What happens if the LLM generates a wrong or malformed query?"	"I constrain the LLM to generate queries only against a known, whitelisted schema, and I validate the generated query before executing it — if it references a column that doesn't exist or the result set looks structurally wrong, the system reports uncertainty instead of returning a number. I don't let raw, unvalidated LLM output touch the data layer directly."
"How would you handle an ambiguous question, like 'show me the pending ones'?"	"That's actually one of the required test cases I built in — the system detects that 'pending' is underspecified between 'pending receipt' and 'pending payment' and asks a clarifying question rather than picking one interpretation silently. I can show that live."
"Why this over the support-triage RAG bot, which is literally your research area?"	"Because building the one thing I already study doesn't prove I can generalize the underlying principle — grounding an answer in verified evidence instead of surface similarity — to something new. Applying that same principle to structured enterprise data instead of vision data is a stronger demonstration that I understand the idea, not just the implementation I already had."
"How would this scale or move to production?"	"Right now the schema is small and fits in context; at scale I'd cache the schema description, restrict generated queries to a safe query DSL instead of raw SQL to remove injection risk, add row-level access control, and log every generated query alongside the question for auditability — since in a real deployment, being able to show why a number was returned matters as much as the number itself."
"What's the one design tradeoff you'd highlight?"	"I chose to constrain the LLM to a restricted, schema-validated query pattern rather than letting it write free-form SQL directly — I gave up some flexibility on more creative questions in exchange for eliminating the risk of hallucinated columns or injection-style failures. For a system whose entire value proposition is 'never wrong,' I judged that tradeoff worth making."
Example Scenarios to Actually Build and Demo
Use these four, in this order, in your live walkthrough — they map directly onto the brief's stated grading criteria:

Simple grounded lookup — "What is the total value of PO 4500123?" → shows basic query translation + correct execution.
Required multi-condition/aggregate case (the brief explicitly requires this) — "Which POs above ₹50,000 have not been fully received?" → join across both mock tables, filter on two conditions, return real matching rows.
Ambiguity-handling case (also explicitly graded) — "Show me the pending ones" → system asks "pending receipt or pending payment?" instead of guessing. This is your single most valuable demo moment.
Out-of-schema / impossible question (your own "break it live" moment) — "What's the vendor's phone number?" → system responds "that data isn't present in the provided tables" instead of inventing an answer. This is the moment that proves the "never hallucinated" claim isn't just a README sentence.
That sequence gives you: a working baseline, proof you satisfied the stated requirements, proof of judgment under ambiguity, and a live falsifiability test — in under two minutes of demo time.

Say the word and we'll move into Phase 1 (deeply understanding the requirements and locking the MVP scope) for Problem 8 — still no implementation yet, just requirements and architecture framing.



Problem 8 it is. Here's the complete picture — the real problem statement, what it actually means, how it maps to you, and a full PRD to work from. No code yet, just understanding and planning, as agreed.

1. The Actual Problem Statement (verbatim from the assessment)
PROBLEM 8 — SAP-Style Data Reconciliation Chatbot

Scenario: Given two mock exports resembling SAP tables — a purchase order header/line table and a goods-receipt/invoice-receipt table — build a chat interface where a user can ask natural-language questions and receive accurate, data-grounded answers.

Requirements:

Load both mock tables into a queryable structure
Translate natural-language questions into correct queries against the data
Return answers grounded in the actual data, never hallucinated
Handle at least one aggregate or multi-condition question (e.g., "which POs have unmatched receipts over $1,000?")
What we're evaluating:

Accuracy of query translation
Whether answers are verifiably grounded in the data
Handling of ambiguous or underspecified questions
That's the whole brief for this problem — deliberately short, because part of what's graded is how you fill the gaps with sound assumptions (per the general ground rule: "state the assumption you made rather than asking us").

2. What This Project Actually Is
In plain words: you're building a chatbot that sits on top of two spreadsheets of enterprise purchasing data. Someone types a question in normal English. Instead of the AI "answering from its own head," it converts the question into a real database query, runs that query against the actual rows, and gives back exactly what the data says — with zero room for the model to invent a number.

Example scenario: A finance analyst at a company using SAP wants to know "Which purchase orders above ₹50,000 haven't received their full quantity yet?" Today, that means opening SAP, running a T-code report, exporting to Excel, and manually cross-referencing two tables. Your chatbot does that lookup conversationally in seconds — and, critically, it must be able to prove the number it gives you is real, not a plausible-sounding guess.

The two mock tables represent SAP's real-world MM (Materials Management) module structure:

Purchase Order table (mirrors SAP's EKKO/EKPO tables) — what was ordered, from whom, at what price.
Goods Receipt / Invoice Receipt table (mirrors SAP's MSEG/RBKP tables) — what was actually received and billed.
Reconciling these two is one of the most common real finance-ops tasks in any company running SAP or similar ERP systems — checking that what was ordered, received, and invoiced all agree.

3. Why This Relates to You Specifically
Example scenario tying it to your background: At Paytm, when you work with metadata-driven systems and SQL-based data workflows, you're already doing the human version of "look at structured data and answer a business question from it." This project just adds a natural-language front-end to that same skill, powered by an LLM that translates the question into the query you'd otherwise write by hand.

Example scenario tying it to Con-VRAG: Your research argument is that retrieving something that merely looks similar isn't enough — you need to select evidence that's actually relevant and verify it. Here, the exact same principle applies to text: an LLM merely "sounding right" about a number isn't enough — the number must come from executing a real query against real rows. You're applying the same intellectual habit (grounding over surface plausibility) to a completely different data type (tables instead of images), which is a stronger proof of understanding than repeating the same domain.

Example scenario tying it to the FDE role: If Supervity deploys you to a client running SAP, your literal first weeks could involve exactly this — a client asking "can your AI just tell me which orders are stuck?" instead of running SAP reports manually. This project is close to a dry run of that real conversation.

4. Product Requirements Document (PRD)
4.1 Purpose
Build a working chat-based assistant that answers natural-language questions about purchase orders and goods/invoice receipts, where every answer is provably derived from executing a query against the actual mock data — never from the LLM's own generated text.

4.2 Goals
Demonstrate accurate natural-language-to-query translation.
Guarantee every returned answer is traceable to real rows in the data (grounding).
Handle at least one genuinely ambiguous question by asking for clarification instead of guessing.
Handle at least one multi-condition/aggregate question correctly.
Be demoable end-to-end in under 2 minutes of live walkthrough.
4.3 Primary User / Persona
Example scenario: "Priya, an AP (Accounts Payable) analyst," who doesn't know SQL, needs quick answers about PO/receipt status without opening SAP or asking IT for a report. She types questions in plain English and expects trustworthy answers, or an honest "I don't know / please clarify" rather than a wrong guess.

4.4 Functional Requirements
ID	Requirement	Example
FR1	Load both mock tables (PO header/line + GR/Invoice receipt) into a queryable store	On startup, two CSVs are loaded into SQLite tables purchase_orders and receipts.
FR2	Accept a natural-language question via chat interface	User types: "What's the total value of PO 4500123?"
FR3	Translate the question into a structured query using an LLM, constrained to the known schema	LLM outputs: SELECT SUM(order_qty * unit_price) FROM purchase_orders WHERE po_number = '4500123'
FR4	Validate the generated query before running it (correct tables/columns referenced, syntactically valid)	If LLM outputs a query referencing a nonexistent column vendor_phone, validator rejects it before execution.
FR5	Execute the validated query against real data and return the actual result	Query returns ₹2,50,000 — that exact number, not a paraphrase.
FR6	Compose a natural-language answer strictly from the query result, citing the values used	"PO 4500123 has a total value of ₹2,50,000, based on 100 units at ₹2,500 each."
FR7	Handle at least one multi-condition/aggregate question	"Which POs above ₹50,000 haven't been fully received?" → join + filter across both tables.
FR8	Detect ambiguous/underspecified questions and ask a clarifying question instead of guessing	"Show me the pending ones" → "Do you mean pending receipt or pending payment?"
FR9	Detect out-of-schema questions and explicitly say the data isn't available	"What's the vendor's phone number?" → "That information isn't present in the provided data."
FR10	Show the underlying generated query alongside the answer (for transparency/audit)	Answer is paired with a collapsible "query used" panel.
4.5 Non-Functional Requirements
Groundedness (critical): The system must never let the LLM state a number it didn't get from query execution.
Transparency: Every answer should be traceable — the generated query and result rows should be inspectable.
Robustness under ambiguity: Should degrade to "ask for clarification" rather than silently picking an interpretation.
Reasonable latency: Chat response within a few seconds for a live demo.
Simplicity of setup: Should run locally with clear README instructions (no complex infra), since it needs to work reliably during a live demo recording.
4.6 Data Model (Mock Schema)
Table 1 — purchase_orders (PO header/line, mirrors SAP EKKO/EKPO)

Column	Example
po_number	4500123
po_line_item	10
vendor_id	V-2041
vendor_name	Anand Steel Traders
material_description	HR Coil 2mm
order_qty	100
unit_price	2500
currency	INR
po_value	250000
order_date	2026-07-01
plant	Plant-Guntur
Table 2 — receipts (Goods Receipt + Invoice Receipt, mirrors SAP MSEG/RBKP)

Column	Example
gr_number	GR-9001
po_number	4500123
po_line_item	10
received_qty	80
receipt_date	2026-07-10
invoice_number	INV-77123
invoice_amount	200000
invoice_date	2026-07-12
invoice_status	Partially Received
Example scenario using this schema: PO 4500123 ordered 100 units worth ₹2,50,000, but only 80 units (₹2,00,000) were received/invoiced so far — a "partially received PO," which is exactly the kind of row your aggregate question ("POs above ₹50,000 not fully received") should surface.

4.7 System Architecture (high level)
User (chat UI)
      ↓ natural-language question
Query Translation Layer (LLM + schema description + few-shot examples)
      ↓ generated query (SQL or safe query DSL)
Validation Layer (checks tables/columns exist, query is well-formed, ambiguity check)
      ↓ if invalid or ambiguous → ask clarifying question, stop here
      ↓ if valid → execute
Execution Layer (runs query against SQLite tables loaded from mock CSVs)
      ↓ real result rows
Answer Composition Layer (LLM phrases the answer using ONLY the returned rows/values)
      ↓
User sees: natural-language answer + underlying query (for transparency)
Example scenario walking through the whole pipeline: User asks "Which POs above ₹50,000 haven't been fully received?" → Translation layer generates a query joining purchase_orders and receipts, filtering po_value > 50000 AND received_qty < order_qty → Validation layer confirms both tables/columns exist → Execution layer runs it and returns PO 4500123 among the results → Composition layer replies: "PO 4500123 (₹2,50,000) is only 80% received — 80 of 100 units so far." → UI also shows the exact SQL that produced this.

4.8 AI/LLM Design Details
Schema-grounded prompting: The LLM is always given the actual table/column names and a few example question→query pairs, so it never has to guess field names.
Constrained output: The LLM's job is narrow — translate to a query, or compose an answer from given rows. It is never asked "what's the answer" directly from its own knowledge.
Validation before execution: Reject/repair queries referencing unknown tables/columns before ever touching real data.
Refusal path: If translation confidence is low, or the question references fields not in the schema, respond with an explicit "not available" or clarification request rather than executing a best-guess query.
Example scenario: If the LLM tries to generate a query referencing a column payment_terms that doesn't exist in either mock table, the validation layer catches it before execution and the system responds: "I don't have payment terms data in the provided tables — I can answer questions about PO value, quantities, and receipt/invoice status."

4.9 Edge Cases & Ambiguity Handling
Case	Example	Expected Behavior
Ambiguous term	"Show me the pending ones"	Ask: "Pending receipt or pending payment?"
Out-of-schema field	"What's the vendor's phone number?"	"That data isn't available in the provided tables."
No matching rows	"Which POs above ₹10,00,000 are unpaid?" (none exist)	"No purchase orders match that condition." — not a fabricated example.
Multi-condition aggregate (required)	"Which POs above ₹50,000 have unmatched receipts?"	Correct join + filter, real rows returned.
Malformed/garbled question	"poo 123 wut total"	Attempt best-effort parse; if truly unparseable, ask for rephrasing.
4.10 Explicit Assumptions (required by the brief's ground rules)
Mock data is synthetic, small enough to fit fully in context/local DB — no real customer or SAP data used.
Single-user, single-session chat — no multi-user auth needed for this assessment.
"Queryable structure" is interpreted as a local SQL database (SQLite) rather than a live SAP connection.
Currency and locale are illustrative (INR used here) — not a functional requirement.
4.11 Out of Scope (for this 24-hour build — stated explicitly, not hidden)
No real SAP/ERP integration.
No user authentication/authorization.
No persistence beyond the mock dataset (no write-back to source systems).
No multi-turn memory beyond the current question (each question is handled independently, unless time allows a stretch goal).
No production deployment/hosting requirement — local run with clear README setup is sufficient.
4.12 Success / Acceptance Criteria
The build is considered complete and demo-ready when all four of these pass live:

Simple grounded lookup returns a correct, traceable number.
The required aggregate/multi-condition question returns correct results.
An ambiguous question triggers a clarifying question, not a guess.
An out-of-schema question is explicitly refused rather than hallucinated.
4.13 Risks & Mitigations
Risk	Mitigation
LLM generates a syntactically valid but logically wrong query	Validation layer + a small fixed set of test questions run before recording the demo
LLM occasionally ignores "only use given rows" instruction	Keep answer-composition prompt strict and minimal; test it explicitly with the refusal case
Ambiguity detection is unreliable	Use a simple, explicit rule (e.g., a short list of known-ambiguous terms) rather than relying purely on LLM judgment — more defensible and explainable in interview
Running out of time on UI polish	Keep the chat UI minimal (a single input + response + "query used" panel) — polish the reasoning, not the visuals
4.14 Proposed Tech Stack (for your decision, not yet committed)
Language: Python — fastest for you to move in, huge ecosystem for both data (pandas/SQLite) and LLM SDKs.
Data store: SQLite — real SQL, not just pandas filtering, which reads as more "database-literate" in an FDE context.
LLM: Your choice of provider (brief explicitly allows any) — the design should be provider-agnostic where possible.
Query generation approach: A controlled, manual prompt + validation step rather than a heavy autonomous "SQL agent" framework — because transparency and inspectability are explicitly graded, and a framework's internals are harder for you to fully explain in a follow-up conversation.
Frontend: A minimal chat UI (Streamlit is the fastest realistic option for a Python-based build in this timeframe) — this is a proposal, not a decision; happy to weigh alternatives if you'd rather build something more custom.
4.15 How This Maps to the Demo Video (5 minutes)
0:00–2:00 (tech stack + architecture): Walk through the pipeline diagram above — translation → validation → execution → grounded answer.
2:00–4:00 (live demo): Run the four test scenarios from section 4.12, in that order — simple lookup, required aggregate, ambiguity handling, refusal on missing data.
4:00–5:00 (one tradeoff): The constrained-query-generation-over-freeform-SQL tradeoff discussed earlier — flexibility traded for safety/groundedness.
This PRD is the full picture — no code written yet. Whenever you're ready, tell me to move into Phase 4/5 (locking the architecture decisions and tech stack for real) and then Phase 6 (implementation plan), and we'll proceed step by step from there.


Happy to do this — a story makes the grounding logic click faster than any architecture diagram. Here's your project as a mini comic script, then the mapping table right after.

🕵️ "Detective Botu and the Case of the Missing Units"
Scene 1 — The Office

Priya rushes in, stressed, holding her coffee.

Priya: "Detective Botu, I need the total value of PO 4500123, right now — I don't have time to log into SAP."

Detective Botu: "Say no more." (flips open a case folder labeled "PO-nny's Ledger") "Found it. PO 4500123 — 100 units at ₹2,500 each. Total: ₹2,50,000. Here's the exact page I checked." (slides over a note: SELECT SUM(order_qty*unit_price) WHERE po_number='4500123')

Scene 2 — The Twin Witnesses

Priya: "Now the hard one. Which POs above ₹50,000 haven't been fully received?"

Detective Botu: (calls in two witnesses — "PO-nny" holding the orders ledger, and "Rex" holding the receipts ledger) "Let's cross-examine both of you together." (compares their stories line by line) "PO-nny says 100 units were ordered on PO 4500123. Rex says only 80 arrived. Case flagged: partially received, value ₹2,50,000."

Scene 3 — The Vague Question Trap

Priya: "Show me the pending ones."

Detective Botu: (pauses, doesn't touch the folder) "Pending receipt, or pending payment? Those are two different case files. Detective's Rule #1 — never guess when a question could mean two things. Which do you mean?"

Scene 4 — The Trick Question

Priya: (testing him) "What's the vendor's phone number?"

Detective Botu: (checks the folder, shakes his head) "Not in my case file. I could make something up that sounds convincing — but a detective who fabricates evidence loses every case eventually. I'll just tell you straight: I don't have that."

Scene 5 — The Golden Rule

Above Botu's desk, taped to the wall, is one line:

"Never speak a number I haven't personally verified in the case file."

That's why Captain Schema never lets him wander outside the approved folders, and why he always shows his notes when he answers — so anyone can double-check his work.

Mapping: Story → Actual Problem Statement
Story Element	What Happens in the Story	What It Actually Is (Technical Requirement)	Why Supervity Grades This
Priya walks in with a question	She asks in plain English, not SQL	The chat interface accepting natural-language questions	Stated requirement: "build a chat interface where a user can ask natural-language questions"
Botu checks the case file instead of answering from memory	He never answers from what he "feels" is true — only from the folder	LLM translates the question into a query; the answer comes from executing that query, not from the model's own generated text	Core eval criterion: "answers grounded in the actual data, never hallucinated"
PO-nny's Ledger & Rex's Ledger	Two separate witnesses/folders Botu can consult	The two mock tables (Purchase Order header/line + Goods Receipt/Invoice Receipt) loaded into a queryable structure	Stated requirement: "Load both mock tables into a queryable structure"
Botu slides over his note (the query)	He shows exactly how he found the answer	The system displays the generated query alongside the answer (transparency/audit)	Directly supports the eval criterion: "whether answers are verifiably grounded in the data"
Cross-examining both witnesses together (Scene 2)	Comparing PO-nny's and Rex's stories side by side to spot a mismatch	A multi-condition/aggregate query joining both tables (POs over ₹50,000 with incomplete receipts)	Stated requirement: "handle at least one aggregate or multi-condition question"
Botu refusing to guess on "pending" (Scene 3)	He asks which meaning she intends instead of picking one	Ambiguity detection — the system asks a clarifying question instead of silently assuming	Explicit eval criterion: "handling of ambiguous or underspecified questions"
Botu refusing to invent the phone number (Scene 4)	He admits the case file doesn't have it, rather than making something up	The refusal path for out-of-schema/missing data — an explicit "not available" response	Directly protects the "never hallucinated" requirement — this is your best live, falsifiable demo moment
Captain Schema keeping Botu inside approved folders	Botu is never allowed to wander into files that aren't officially part of the case	Schema-constrained query generation + a validation layer that rejects queries referencing unknown tables/columns	Underpins the eval criterion: "accuracy of query translation" — wrong/invalid queries get caught before they can produce a wrong answer
The golden rule on the wall	"Never speak a number I haven't personally verified"	The central design principle: the LLM composes its answer only from real query results, never from its own knowledge	This one sentence is the entire grading rubric for Problem 8, restated
Every panel in the story corresponds to a real requirement you have to build — nothing was invented just for the story. If this framing was useful, I can turn the "Detective Botu" metaphor into the actual narration for your demo video's architecture explanation too — it's a genuinely good way to make the grounding concept land with a non-technical reviewer in under 2 minutes. Want me to draft that next, or move into locking the tech stack and implementation plan?



