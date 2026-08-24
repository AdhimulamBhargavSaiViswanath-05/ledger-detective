"""SQL generation chain - translates natural language to SQL."""
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.db import get_database
from src.chains.gemini_llm import GeminiLLM
from src.chains.mock_llm import MockSQLGenerationLLM


# Load environment variables
load_dotenv()

# Global state to track which LLM is being used and any fallback reasons
_llm_state = {
    "mode": None,  # "gemini", "mock"
    "fallback_reason": None,
    "last_error": None
}


def get_sql_generation_chain():
    """
    Create LCEL chain for natural language to SQL translation.
    
    Chain: PromptTemplate -> LLM -> StrOutputParser
    
    The prompt includes:
    - Real schema from database (via get_table_info())
    - Few-shot examples of question→SQL pairs
    - Instruction to generate SELECT queries only
    """
    # Get database instance to pull real schema
    db = get_database()
    schema_info = db.get_table_info()
    
    # Few-shot examples for Q→SQL translation
    few_shot_examples = """
Examples:

Question: What is the total value of PO 4500123?
SQL: SELECT SUM(order_qty * unit_price) as total_value FROM purchase_orders WHERE po_number = 4500123;

Question: Which POs above 50000 have not been fully received?
SQL: SELECT p.po_number, p.po_value, p.order_qty, COALESCE(r.received_qty, 0) as received_qty 
FROM purchase_orders p 
LEFT JOIN receipts r ON p.po_number = r.po_number AND p.po_line_item = r.po_line_item 
WHERE p.po_value > 50000 AND (r.received_qty IS NULL OR r.received_qty < p.order_qty);

Question: How many purchase orders are from vendor Anand Steel Traders?
SQL: SELECT COUNT(*) as count FROM purchase_orders WHERE vendor_name = 'Anand Steel Traders';

Question: What is the total amount invoiced so far?
SQL: SELECT SUM(invoice_amount) as total_invoiced FROM receipts;

Question: Show me all POs that have received goods
SQL: SELECT DISTINCT p.* FROM purchase_orders p INNER JOIN receipts r ON p.po_number = r.po_number AND p.po_line_item = r.po_line_item;
"""
    
    # Prompt template with full LLM autonomy
    prompt_template = """You are an intelligent SQL assistant. You have access to a database and must decide how to respond to user questions.

Available Database Schema:
{schema}

{examples}

Your Responsibilities:
1. Analyze the user's question
2. Check if it CAN be answered using the available tables/columns
3. Check if the question is CLEAR or AMBIGUOUS
4. Respond with ONE of the following:

Response Format A - Generate SQL (when question is clear and answerable):
Generate a valid SQLite SELECT query

Response Format B - Ask for Clarification (when question is ambiguous):
NEEDS_CLARIFICATION: <your clarifying question>

Response Format C - Refuse Gracefully (when question is out of scope):
OUT_OF_SCOPE: <brief explanation of what data you have>

Rules for SQL Generation:
- Generate ONLY SELECT queries, never INSERT/UPDATE/DELETE/DROP
- Use only tables and columns that exist in the schema
- Return only the SQL query, no explanation or markdown
- Ensure valid SQLite syntax

Examples of Ambiguous Questions (return NEEDS_CLARIFICATION):
- "Show me pending ones" → NEEDS_CLARIFICATION: Do you mean pending receipts or pending invoices?
- "What's the total?" → NEEDS_CLARIFICATION: Total of what? PO values, invoice amounts, or received quantities?

Examples of Out-of-Scope Questions (return OUT_OF_SCOPE):
- "What's the weather?" → OUT_OF_SCOPE: I only have purchase orders and receipts data, not weather information.
- "Tell me a joke" → OUT_OF_SCOPE: I can help with PO values, vendors, invoices, and receipt information.

Question: {question}
Response:"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["question"],
        partial_variables={"schema": schema_info, "examples": few_shot_examples}
    )
    
    # This function is now only used for Mock LLM fallback
    # The primary Gemini path uses GeminiLLM directly in generate_sql()
    llm = MockSQLGenerationLLM()
    
    # Build LCEL chain
    chain = prompt | llm | StrOutputParser()
    
    return chain


def generate_sql(question: str) -> str:
    """
    Generate SQL query from natural language question.
    
    Tries Gemini API first, falls back to mock on error.
    
    Args:
        question: Natural language question
        
    Returns:
        SQL query string
    """
    global _llm_state
    
    # Get database schema
    db = get_database()
    schema_info = db.get_table_info()
    
    # Build prompt
    few_shot_examples = """
Examples:

Question: What is the total value of PO 4500123?
SQL: SELECT SUM(order_qty * unit_price) as total_value FROM purchase_orders WHERE po_number = 4500123;

Question: Which POs above 50000 have not been fully received?
SQL: SELECT p.po_number, p.po_value, p.order_qty, COALESCE(r.received_qty, 0) as received_qty 
FROM purchase_orders p 
LEFT JOIN receipts r ON p.po_number = r.po_number AND p.po_line_item = r.po_line_item 
WHERE p.po_value > 50000 AND (r.received_qty IS NULL OR r.received_qty < p.order_qty);

Question: How many purchase orders are from vendor Anand Steel Traders?
SQL: SELECT COUNT(*) as count FROM purchase_orders WHERE vendor_name = 'Anand Steel Traders';
"""
    
    prompt_text = f"""You are an intelligent SQL assistant. You have access to a database and must decide how to respond to user questions.

Available Database Schema:
{schema_info}

{few_shot_examples}

Your Responsibilities:
1. Analyze the user's question
2. Check if it CAN be answered using the available tables/columns
3. Check if the question is CLEAR or AMBIGUOUS
4. Respond with ONE of the following:

Response Format A - Generate SQL (when question is clear and answerable):
Generate a valid SQLite SELECT query

Response Format B - Ask for Clarification (when question is ambiguous):
NEEDS_CLARIFICATION: <your clarifying question>

Response Format C - Refuse Gracefully (when question is out of scope):
OUT_OF_SCOPE: <brief explanation of what data you have>

Rules for SQL Generation:
- Generate ONLY SELECT queries, never INSERT/UPDATE/DELETE/DROP
- Use only tables and columns that exist in the schema
- Return only the SQL query, no explanation or markdown
- Ensure valid SQLite syntax

Examples of Ambiguous Questions (return NEEDS_CLARIFICATION):
- "Show me pending ones" → NEEDS_CLARIFICATION: Do you mean pending receipts or pending invoices?
- "What's the total?" → NEEDS_CLARIFICATION: Total of what? PO values, invoice amounts, or received quantities?

Examples of Out-of-Scope Questions (return OUT_OF_SCOPE):
- "What's the weather?" → OUT_OF_SCOPE: I only have purchase orders and receipts data, not weather information.

Question: {question}
Response:"""
    
    # Check if forced to use mock
    use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    
    if not use_mock:
        # Try Gemini first
        gemini = GeminiLLM()
        if gemini.is_configured:
            success, sql, error = gemini.generate(prompt_text)
            if success:
                _llm_state["mode"] = "gemini"
                _llm_state["fallback_reason"] = None
                _llm_state["last_error"] = None
                return _clean_sql(sql)
            else:
                # Gemini failed, fallback to mock
                _llm_state["mode"] = "mock"
                _llm_state["fallback_reason"] = error or "Gemini API failed"
                _llm_state["last_error"] = error
        else:
            _llm_state["mode"] = "mock"
            _llm_state["fallback_reason"] = "Gemini API not configured"
            _llm_state["last_error"] = gemini.last_error
    else:
        _llm_state["mode"] = "mock"
        _llm_state["fallback_reason"] = "Mock mode forced by configuration"
        _llm_state["last_error"] = None
    
    # Use mock LLM
    chain = get_sql_generation_chain()
    sql = chain.invoke({"question": question})
    return _clean_sql(sql)


def _clean_sql(sql: str) -> str:
    """Clean up SQL response (remove markdown formatting)"""
    sql = sql.strip()
    if sql.startswith("```"):
        # Remove markdown code blocks
        lines = sql.split("\n")
        sql = "\n".join(line for line in lines if not line.startswith("```"))
        sql = sql.strip()
    return sql


def get_llm_state() -> dict:
    """Get current LLM state (mode and fallback reason)"""
    global _llm_state
    return _llm_state.copy()


def reset_llm_state():
    """Reset LLM state"""
    global _llm_state
    _llm_state = {
        "mode": None,
        "fallback_reason": None,
        "last_error": None
    }
