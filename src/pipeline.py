"""Full end-to-end pipeline orchestration."""
from typing import Dict, Any
from src.chains.sql_generation import generate_sql
from src.chains.validation import validate_sql
from src.chains.execution import execute_sql
from src.chains.answer_composition import compose_answer


def run_pipeline(question: str) -> str:
    """
    Run the full question-answering pipeline.
    
    LLM-Driven Pipeline:
    1. Generate SQL from question (LLM decides if answerable, ambiguous, or out-of-scope)
    2. Validate SQL query (security checks only)
    3. Execute validated SQL query
    4. Compose natural language answer from results
    
    The LLM has full autonomy to:
    - Decide if question can be answered from available data
    - Ask for clarification if question is ambiguous
    - Refuse gracefully if out of scope
    - Generate appropriate SQL for any data-related question
    
    Args:
        question: Natural language question (any form - clear, ambiguous, random)
        
    Returns:
        Final answer string (or out-of-scope/clarification message)
    """
    # Step 1: Generate SQL (LLM makes ALL decisions based on schema + question)
    try:
        sql = generate_sql(question)
    except Exception as e:
        return f"Error generating SQL: {str(e)}"
    
    # Check LLM decision
    if sql.startswith("OUT_OF_SCOPE:"):
        # LLM determined question cannot be answered from available data
        reason = sql.replace("OUT_OF_SCOPE:", "").strip()
        return reason
    
    if sql.startswith("NEEDS_CLARIFICATION:"):
        # LLM determined question is ambiguous
        clarification = sql.replace("NEEDS_CLARIFICATION:", "").strip()
        return clarification
    
    # Step 2: Validate SQL (security only - no business logic)
    is_valid, validation_reason = validate_sql(sql)
    if not is_valid:
        return f"Generated query failed safety checks: {validation_reason}"
    
    # Step 3: Execute SQL
    success, result, _ = execute_sql(sql)
    if not success:
        return f"Error executing query: {result}"
    
    # Step 4: Compose answer
    try:
        answer = compose_answer(question, result)
        return answer
    except Exception as e:
        return f"Error composing answer: {str(e)}"


def run_pipeline_detailed(question: str) -> Dict[str, Any]:
    """
    Run the full pipeline and return detailed information for UI display.
    
    Returns a dictionary with:
    - question: Original question
    - sql_query: Generated SQL query
    - raw_result: Raw database result
    - answer: Natural language answer
    - steps: List of processing steps taken
    - error: Error message if any
    
    Args:
        question: Natural language question
        
    Returns:
        Dictionary with detailed execution information
    """
    result_data = {
        "question": question,
        "sql_query": "",
        "raw_result": "",
        "answer": "",
        "steps": [],
        "error": None
    }
    
    # Step 1: Generate SQL
    result_data["steps"].append("📝 Analyzing question and determining intent")
    try:
        sql = generate_sql(question)
        result_data["steps"].append("✅ Generated SQL query from natural language")
    except Exception as e:
        result_data["error"] = f"Error generating SQL: {str(e)}"
        result_data["answer"] = result_data["error"]
        return result_data
    
    # Check LLM decision
    if sql.startswith("OUT_OF_SCOPE:"):
        reason = sql.replace("OUT_OF_SCOPE:", "").strip()
        result_data["steps"].append("🚫 Question determined to be out of scope")
        result_data["answer"] = reason
        return result_data
    
    if sql.startswith("NEEDS_CLARIFICATION:"):
        clarification = sql.replace("NEEDS_CLARIFICATION:", "").strip()
        result_data["steps"].append("❓ Question is ambiguous, requesting clarification")
        result_data["answer"] = clarification
        return result_data
    
    result_data["sql_query"] = sql
    
    # Step 2: Validate SQL
    result_data["steps"].append("🔒 Validating SQL query for security")
    is_valid, validation_reason = validate_sql(sql)
    if not is_valid:
        result_data["error"] = f"Query failed safety checks: {validation_reason}"
        result_data["answer"] = result_data["error"]
        result_data["steps"].append(f"❌ Validation failed: {validation_reason}")
        return result_data
    result_data["steps"].append("✅ SQL query passed all security validations")
    
    # Step 3: Execute SQL
    result_data["steps"].append("⚡ Executing query against database")
    success, result, _ = execute_sql(sql)
    if not success:
        result_data["error"] = f"Error executing query: {result}"
        result_data["answer"] = result_data["error"]
        result_data["steps"].append(f"❌ Execution failed: {result}")
        return result_data
    
    result_data["raw_result"] = result
    result_data["steps"].append(f"✅ Query executed successfully")
    
    # Step 4: Compose answer
    result_data["steps"].append("💬 Composing natural language answer")
    try:
        answer = compose_answer(question, result)
        result_data["answer"] = answer
        result_data["steps"].append("✅ Answer generated successfully")
    except Exception as e:
        result_data["error"] = f"Error composing answer: {str(e)}"
        result_data["answer"] = result_data["error"]
        result_data["steps"].append(f"❌ Answer composition failed: {str(e)}")
    
    return result_data
