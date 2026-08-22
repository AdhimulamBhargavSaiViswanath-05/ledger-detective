"""Answer composition - converts raw SQL results into natural language."""
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

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


# Prompt template for answer composition
ANSWER_COMPOSITION_PROMPT = PromptTemplate(
    input_variables=["question", "raw_result"],
    template="""You are converting database query results into clear, natural language answers.

User's Question: {question}

Query Result: {raw_result}

Instructions:
1. Write a short, friendly sentence that directly answers the user's question
2. Include the key numbers/values from the query result
3. DO NOT fabricate any data not present in the result
4. DO NOT mention SQL, databases, or technical details
5. Keep it conversational and natural

Natural Answer:"""
)


def get_answer_composition_chain():
    """
    Create and return the answer composition chain.
    
    Returns:
        LCEL chain that takes (question, raw_result) and returns natural_answer
    """
    # LLM Selection - same logic as SQL generation
    use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    llm = None
    
    if use_mock:
        # Use simple lambda for mock
        from langchain_core.runnables import RunnableLambda
        mock_func = lambda inputs: mock_answer_composition(inputs.content if hasattr(inputs, 'content') else str(inputs))
        return ANSWER_COMPOSITION_PROMPT | RunnableLambda(mock_func)
    elif os.getenv("OPENAI_API_KEY") and OPENAI_AVAILABLE:
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        except Exception:
            llm = None
    elif os.getenv("GEMINI_API_KEY") and GEMINI_AVAILABLE:
        try:
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-1.5-flash-latest",
                temperature=0,
                google_api_key=os.getenv("GEMINI_API_KEY")
            )
        except Exception:
            llm = None
    
    # Fallback to mock if no LLM available
    if llm is None:
        from langchain_core.runnables import RunnableLambda
        mock_func = lambda inputs: mock_answer_composition(inputs.content if hasattr(inputs, 'content') else str(inputs))
        return ANSWER_COMPOSITION_PROMPT | RunnableLambda(mock_func)
    
    # Create LCEL chain with real LLM
    chain = ANSWER_COMPOSITION_PROMPT | llm | StrOutputParser()
    
    return chain


def mock_answer_composition(input_text: str) -> str:
    """
    Enhanced rule-based answer generation for mock.
    Handles diverse result formats from 5-table schema.
    """
    import re
    
    # Extract question and raw result from the prompt
    question_match = re.search(r"User's Question:\s*(.+?)(?:\n|Query Result:)", input_text, re.DOTALL)
    result_match = re.search(r"Query Result:\s*(.+?)(?:\n|Instructions:|$)", input_text, re.DOTALL)
    
    question = question_match.group(1).strip() if question_match else ""
    raw_result = result_match.group(1).strip() if result_match else input_text
    
    question_lower = question.lower()
    
    # Handle empty results
    if not raw_result or raw_result == "[]" or raw_result == "None":
        return "No matching records found in the database."
    
    # Parse result based on format
    # Format 1: [(value,)] for single value queries
    single_value_match = re.search(r'\[\(([^)]+)\)\]', raw_result)
    
    # Format 2: Multiple rows [(val1,), (val2,), ...]
    multi_rows = re.findall(r'\(([^)]+)\)', raw_result)
    
    # Count queries - "how many" or "count"
    if "how many" in question_lower or "count" in question_lower:
        if single_value_match:
            count = single_value_match.group(1).strip("'\",")
            if "line item" in question_lower or "item" in question_lower:
                return f"There are {count} line items across all purchase orders."
            elif "purchase order" in question_lower or "po" in question_lower:
                return f"There are {count} purchase orders in the database."
            elif "invoice" in question_lower:
                return f"There are {count} invoices in the database."
            elif "receipt" in question_lower or "gr" in question_lower:
                return f"There are {count} goods receipts in the database."
            else:
                return f"There are {count} records in the database."
        return "Unable to determine count from the query result."
    
    # Sum/Total queries
    if ("total" in question_lower or "sum" in question_lower) and single_value_match:
        total = single_value_match.group(1).strip("'\",")
        if "invoice" in question_lower:
            return f"The total invoice amount is {total} INR."
        elif "po" in question_lower or "purchase order" in question_lower:
            return f"The total purchase order value is {total} INR."
        else:
            return f"The total is {total}."
    
    # Vendor queries with aggregation
    if "vendor" in question_lower and "most" in question_lower:
        if multi_rows and len(multi_rows) > 0:
            # Parse vendor with count: ('Vendor Name', count)
            vendors = []
            for row in multi_rows[:5]:  # Top 5
                parts = row.split(',')
                if len(parts) >= 2:
                    vendor = parts[0].strip("'\"")
                    count = parts[1].strip("'\"")
                    vendors.append(f"{vendor} ({count} POs)")
            if vendors:
                return f"Top vendors by purchase orders: {', '.join(vendors)}"
        return f"Found {len(multi_rows)} vendors with purchase orders."
    
    # List queries - vendors, plants, etc.
    if ("show" in question_lower or "list" in question_lower or "which" in question_lower) and "vendor" in question_lower:
        if multi_rows:
            items = [row.strip("'\"") for row in multi_rows[:10]]
            return f"Vendors: {', '.join(items)}"
    
    # Specific PO queries
    po_number_match = re.search(r'(45\d{5})', question_lower)
    if po_number_match:
        po_num = po_number_match.group(1)
        if multi_rows:
            return f"Found {len(multi_rows)} records for PO {po_num}."
        elif single_value_match:
            value = single_value_match.group(1).strip("'\",")
            return f"PO {po_num} has a value of {value} INR."
    
    # Missing document queries
    if "no" in question_lower or "without" in question_lower or "unmatched" in question_lower:
        if multi_rows:
            return f"Found {len(multi_rows)} records matching your criteria."
        return "No unmatched records found."
    
    # Three-way match or variance queries
    if "variance" in question_lower or "match" in question_lower or "difference" in question_lower:
        if multi_rows:
            return f"Found {len(multi_rows)} records with the requested status."
        return "No variances detected in the dataset."
    
    # Performance or summary queries
    if "performance" in question_lower or "summary" in question_lower:
        if multi_rows:
            return f"Generated performance summary with {len(multi_rows)} vendor records."
        return "No performance data available."
    
    # Generic multi-row result
    if multi_rows and len(multi_rows) > 0:
        return f"Found {len(multi_rows)} matching records. {raw_result[:200]}"
    
    # Generic single value result
    if single_value_match:
        value = single_value_match.group(1).strip("'\",")
        return f"The result is: {value}"
    
    # Fallback: show raw result truncated
    return f"Query returned: {raw_result[:300]}"



def compose_answer(question: str, raw_result: str) -> str:
    """
    Compose a natural language answer from query result.
    
    Args:
        question: User's original question
        raw_result: Raw database query result
        
    Returns:
        Natural language answer
    """
    chain = get_answer_composition_chain()
    answer = chain.invoke({"question": question, "raw_result": raw_result})
    return answer.strip()

