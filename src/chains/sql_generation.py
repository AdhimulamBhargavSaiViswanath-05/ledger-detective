"""SQL generation chain - translates natural language to SQL."""
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.db import get_database

# Import both real and mock LLM
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.chains.mock_llm import MockSQLGenerationLLM


# Load environment variables
load_dotenv()


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
    
    # Prompt template
    prompt_template = """You are a SQL expert. Generate a valid SQLite SELECT query to answer the question.

Database Schema:
{schema}

{examples}

Rules:
- Generate ONLY SELECT queries, never INSERT/UPDATE/DELETE/DROP
- Use only tables and columns that exist in the schema above
- Return only the SQL query, no explanation or markdown formatting
- Do not use quotes around the SQL query
- Ensure the query is valid SQLite syntax

Question: {question}
SQL:"""
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["question"],
        partial_variables={"schema": schema_info, "examples": few_shot_examples}
    )
    
    # LLM Selection - Auto-detect which LLM to use with fallback to mock
    # Priority: OpenAI > Gemini > Mock
    
    use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    llm = None
    
    if use_mock:
        # Explicitly use mock LLM (for testing)
        llm = MockSQLGenerationLLM()
    elif os.getenv("OPENAI_API_KEY") and OPENAI_AVAILABLE:
        # Try to use OpenAI if API key is available
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        except Exception as e:
            print(f"WARNING: Failed to initialize OpenAI: {e}. Falling back to mock.")
            llm = None
    elif os.getenv("GEMINI_API_KEY") and GEMINI_AVAILABLE:
        # Try to use Gemini if API key is available
        try:
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-1.5-flash-latest",
                temperature=0,
                google_api_key=os.getenv("GEMINI_API_KEY")
            )
        except Exception as e:
            print(f"WARNING: Failed to initialize Gemini: {e}. Falling back to mock.")
            llm = None
    
    # Fallback to mock if no LLM was successfully initialized
    if llm is None:
        print("WARNING: No valid API key found or LLM initialization failed. Using MockSQLGenerationLLM for development.")
        llm = MockSQLGenerationLLM()
    
    # Build LCEL chain
    chain = prompt | llm | StrOutputParser()
    
    return chain


def generate_sql(question: str) -> str:
    """
    Generate SQL query from natural language question.
    
    Args:
        question: Natural language question
        
    Returns:
        SQL query string
    """
    chain = get_sql_generation_chain()
    sql = chain.invoke({"question": question})
    
    # Clean up the SQL (remove markdown formatting if present)
    sql = sql.strip()
    if sql.startswith("```"):
        # Remove markdown code blocks
        lines = sql.split("\n")
        sql = "\n".join(line for line in lines if not line.startswith("```"))
        sql = sql.strip()
    
    return sql
