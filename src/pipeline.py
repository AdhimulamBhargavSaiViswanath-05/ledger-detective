"""Full end-to-end pipeline orchestration."""
from src.chains.refusal import should_refuse, get_refusal_message
from src.chains.ambiguity_check import check_ambiguity
from src.chains.sql_generation import generate_sql
from src.chains.validation import validate_sql
from src.chains.execution import execute_sql
from src.chains.answer_composition import compose_answer


def run_pipeline(question: str) -> str:
    """
    Run the full question-answering pipeline.
    
    Pipeline flow:
    1. Check if question should be refused (out of scope)
    2. Check if question is ambiguous (needs clarification)
    3. Generate SQL query from question
    4. Validate SQL query (safety checks)
    5. Execute validated SQL query
    6. Compose natural language answer from results
    
    Args:
        question: Natural language question
        
    Returns:
        Final answer string (or refusal/clarification message)
    """
    # Step 1: Refusal check
    if should_refuse(question):
        return get_refusal_message()
    
    # Step 2: Ambiguity check
    is_ambiguous, clarification = check_ambiguity(question)
    if is_ambiguous:
        return f"Your question needs clarification: {clarification}"
    
    # Step 3: Generate SQL
    try:
        sql = generate_sql(question)
    except Exception as e:
        return f"Error generating SQL: {str(e)}"
    
    # Step 4: Validate SQL
    is_valid, validation_reason = validate_sql(sql)
    if not is_valid:
        return f"Generated query failed safety checks: {validation_reason}"
    
    # Step 5: Execute SQL
    success, result, _ = execute_sql(sql)
    if not success:
        return f"Error executing query: {result}"
    
    # Step 6: Compose answer
    try:
        answer = compose_answer(question, result)
        return answer
    except Exception as e:
        return f"Error composing answer: {str(e)}"
