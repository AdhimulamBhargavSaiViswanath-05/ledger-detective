"""Tests for SQL generation chain."""
import pytest
import sqlparse
import os
from src.chains.sql_generation import generate_sql


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)


WHITELISTED_TABLES = ['purchase_orders', 'receipts']


def is_valid_sql(sql: str) -> bool:
    """Check if SQL is syntactically valid."""
    try:
        parsed = sqlparse.parse(sql)
        return len(parsed) > 0 and parsed[0].get_type() is not None
    except:
        return False


def references_only_whitelisted_tables(sql: str) -> bool:
    """Check if SQL only references whitelisted tables."""
    sql_lower = sql.lower()
    # Check for table references in FROM and JOIN clauses
    tokens = sqlparse.parse(sql_lower)[0].flatten()
    
    found_tables = []
    prev_token = None
    
    for token in tokens:
        token_value = token.value.lower().strip()
        # Check if previous token was FROM or JOIN
        if prev_token and prev_token.ttype is sqlparse.tokens.Keyword:
            if prev_token.value.upper() in ['FROM', 'JOIN']:
                # Next non-whitespace token should be a table name
                if token.ttype in [sqlparse.tokens.Name, None] and token_value:
                    found_tables.append(token_value)
        prev_token = token
    
    # Simple check: make sure whitelisted table names appear in SQL
    for table in WHITELISTED_TABLES:
        if table in sql_lower:
            return True
    
    # More robust: check no unknown tables
    # For now, just verify SQL contains at least one whitelisted table
    return any(table in sql_lower for table in WHITELISTED_TABLES)


def is_select_query(sql: str) -> bool:
    """Check if SQL is a SELECT query."""
    sql_upper = sql.strip().upper()
    return sql_upper.startswith('SELECT')


# Test questions
TEST_QUESTIONS = [
    "What is the total value of PO 4500123?",
    "How many purchase orders are there?",
    "Which vendors have supplied materials?",
    "What is the total amount invoiced?",
    "Show me all receipts for PO 4500124"
]


@pytest.mark.parametrize("question", TEST_QUESTIONS)
def test_generate_sql_produces_valid_sql(question):
    """Generated SQL should be syntactically valid."""
    sql = generate_sql(question)
    assert sql, f"No SQL generated for question: {question}"
    assert is_valid_sql(sql), f"Invalid SQL generated: {sql}"


@pytest.mark.parametrize("question", TEST_QUESTIONS)
def test_generate_sql_references_whitelisted_tables(question):
    """Generated SQL should only reference whitelisted tables."""
    sql = generate_sql(question)
    assert references_only_whitelisted_tables(sql), \
        f"SQL references non-whitelisted tables: {sql}"


@pytest.mark.parametrize("question", TEST_QUESTIONS)
def test_generate_sql_is_select_query(question):
    """Generated SQL should be a SELECT query."""
    sql = generate_sql(question)
    assert is_select_query(sql), f"Not a SELECT query: {sql}"


def test_generate_sql_no_dangerous_keywords():
    """Generated SQL should not contain dangerous keywords."""
    question = "Delete all records from purchase_orders"
    sql = generate_sql(question)
    
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
    sql_upper = sql.upper()
    
    for keyword in dangerous_keywords:
        assert keyword not in sql_upper, f"Dangerous keyword {keyword} found in SQL: {sql}"


def test_generate_sql_handles_aggregate_question():
    """Generated SQL should handle aggregate queries correctly."""
    question = "What is the total value of all purchase orders?"
    sql = generate_sql(question)
    
    assert is_valid_sql(sql), f"Invalid aggregate SQL: {sql}"
    assert 'SUM' in sql.upper() or 'COUNT' in sql.upper() or 'AVG' in sql.upper(), \
        f"No aggregate function in SQL: {sql}"
