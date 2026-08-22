"""SQL execution layer - safely runs validated queries against the database."""
from typing import Tuple, Optional
from src.db import get_database
from src.chains.validation import validate_sql


def execute_sql(sql: str) -> Tuple[bool, str, Optional[str]]:
    """
    Execute SQL query after validation.
    
    Args:
        sql: SQL query string to execute
        
    Returns:
        Tuple of (success, result_or_error, validation_reason)
        - success: True if query executed successfully, False if validation failed or execution error
        - result_or_error: Query result string if success, error message if failure
        - validation_reason: Reason for validation failure (None if validated successfully)
    """
    # Step 1: Validate SQL
    is_valid, reason = validate_sql(sql)
    
    if not is_valid:
        return False, f"Validation failed: {reason}", reason
    
    # Step 2: Execute validated query
    try:
        db = get_database()
        result = db.run(sql)
        return True, result, None
    except Exception as e:
        return False, f"Execution error: {str(e)}", None


def safe_execute(sql: str) -> str:
    """
    Safely execute SQL and return result or error message.
    
    Convenience function that always returns a string (result or error).
    
    Args:
        sql: SQL query string
        
    Returns:
        Query result or error message
    """
    success, result, _ = execute_sql(sql)
    return result
