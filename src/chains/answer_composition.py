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
    """Simple rule-based answer generation for mock."""
    import re
    
    # Extract numbers - look for actual result values in format [(number,)]
    result_match = re.search(r'\[\((\d+),?\)\]', input_text)
    if result_match:
        main_number = result_match.group(1)
    else:
        # Fallback: extract all numbers
        numbers = re.findall(r'\d+', input_text)
        main_number = numbers[-1] if numbers else "0"
    
    # Simple template responses
    if "count" in input_text.lower():
        return f"There are {main_number} records in the database."
    elif "po 4500123" in input_text.lower() or "4500123" in input_text:
        return f"PO 4500123 has a value of {main_number} INR."
    elif "po 4500124" in input_text.lower() or "4500124" in input_text:
        return f"PO 4500124 has a value of {main_number} INR."
    elif "total" in input_text.lower() and "invoice" in input_text.lower():
        return f"The total invoice amount is {main_number} INR."
    elif "vendor" in input_text.lower():
        return f"There are {main_number} vendors."
    else:
        return f"The result is {main_number}."



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

