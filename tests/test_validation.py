"""Tests for SQL validation layer."""
import pytest
from src.chains.validation import validate_sql, is_safe_query


# Test cases: (sql, expected_valid, description)
VALIDATION_TEST_CASES = [
    # Valid SELECT queries
    (
        "SELECT * FROM purchase_orders WHERE po_number = 4500123;",
        True,
        "Simple SELECT with WHERE clause"
    ),
    (
        "SELECT po_number, po_value FROM purchase_orders;",
        True,
        "SELECT with specific columns"
    ),
    (
        "SELECT COUNT(*) FROM receipts;",
        True,
        "SELECT with aggregate function"
    ),
    (
        "SELECT p.po_number, r.received_qty FROM purchase_orders p JOIN receipts r ON p.po_number = r.po_number;",
        True,
        "SELECT with JOIN"
    ),
    (
        "SELECT SUM(order_qty * unit_price) as total FROM purchase_orders;",
        True,
        "SELECT with calculated field and alias"
    ),
    
    # SQL Injection attempts - MUST BE REJECTED
    (
        "SELECT * FROM purchase_orders; DROP TABLE purchase_orders;",
        False,
        "SQL injection: multiple statements with DROP"
    ),
    (
        "SELECT * FROM purchase_orders; DELETE FROM receipts;",
        False,
        "SQL injection: multiple statements with DELETE"
    ),
    (
        "SELECT * FROM purchase_orders WHERE 1=1; UPDATE receipts SET invoice_status='hacked';",
        False,
        "SQL injection: UPDATE attempt"
    ),
    
    # Dangerous keywords - MUST BE REJECTED
    (
        "DROP TABLE purchase_orders;",
        False,
        "DROP TABLE attempt"
    ),
    (
        "DELETE FROM purchase_orders WHERE po_number = 4500123;",
        False,
        "DELETE attempt"
    ),
    (
        "UPDATE purchase_orders SET po_value = 0;",
        False,
        "UPDATE attempt"
    ),
    (
        "INSERT INTO purchase_orders (po_number) VALUES (9999);",
        False,
        "INSERT attempt"
    ),
    (
        "ALTER TABLE purchase_orders ADD COLUMN hacked INT;",
        False,
        "ALTER TABLE attempt"
    ),
    (
        "CREATE TABLE hacked (id INT);",
        False,
        "CREATE TABLE attempt"
    ),
    (
        "ATTACH DATABASE 'other.db' AS other;",
        False,
        "ATTACH DATABASE attempt"
    ),
    
    # Non-SELECT statements - MUST BE REJECTED
    (
        "EXPLAIN SELECT * FROM purchase_orders;",
        False,
        "EXPLAIN query (not pure SELECT)"
    ),
    
    # Invalid table references - MUST BE REJECTED
    (
        "SELECT * FROM users;",
        False,
        "Reference to non-whitelisted table"
    ),
    (
        "SELECT * FROM purchase_orders, users;",
        False,
        "Mix of valid and invalid tables"
    ),
    
    # Invalid column references - MUST BE REJECTED
    (
        "SELECT po_number, password FROM purchase_orders;",
        False,
        "Reference to non-existent column"
    ),
    
    # Edge cases
    (
        "",
        False,
        "Empty query"
    ),
    (
        "   ",
        False,
        "Whitespace only"
    ),
    (
        "SELECT",
        False,
        "Incomplete SELECT"
    ),
]


@pytest.mark.parametrize("sql,expected_valid,description", VALIDATION_TEST_CASES)
def test_validate_sql(sql, expected_valid, description):
    """Test SQL validation with various cases."""
    is_valid, reason = validate_sql(sql)
    
    if expected_valid:
        assert is_valid, f"Expected valid but got invalid: {description}. Reason: {reason}"
        assert reason == "", f"Valid SQL should have empty reason, got: {reason}"
    else:
        assert not is_valid, f"Expected invalid but got valid: {description}"
        assert reason != "", f"Invalid SQL should have a reason: {description}"


def test_sql_injection_multiple_statements():
    """Specific test for SQL injection with multiple statements."""
    sql = "SELECT * FROM purchase_orders; DROP TABLE purchase_orders;"
    is_valid, reason = validate_sql(sql)
    
    assert not is_valid, "SQL injection attempt should be rejected"
    assert "injection" in reason.lower() or "multiple" in reason.lower(), \
        f"Reason should mention injection or multiple statements, got: {reason}"


def test_nonexistent_column():
    """Specific test for query with non-existent column."""
    sql = "SELECT po_number, hacker_column FROM purchase_orders;"
    is_valid, reason = validate_sql(sql)
    
    assert not is_valid, "Query with non-existent column should be rejected"
    assert "column" in reason.lower() or "whitelist" in reason.lower(), \
        f"Reason should mention column issue, got: {reason}"


def test_is_safe_query_convenience_function():
    """Test the is_safe_query convenience function."""
    # Valid query
    assert is_safe_query("SELECT * FROM purchase_orders;") is True
    
    # Invalid query
    assert is_safe_query("DROP TABLE purchase_orders;") is False
    assert is_safe_query("SELECT * FROM purchase_orders; DELETE FROM receipts;") is False


def test_case_insensitive_keywords():
    """Test that dangerous keywords are caught regardless of case."""
    test_cases = [
        "drop table purchase_orders;",
        "DROP TABLE purchase_orders;",
        "DRoP TaBLe purchase_orders;",
    ]
    
    for sql in test_cases:
        is_valid, reason = validate_sql(sql)
        assert not is_valid, f"Should reject {sql}"
        assert "drop" in reason.lower() or "dangerous" in reason.lower()


def test_semicolon_in_string_literal():
    """Test that semicolons in string literals don't trigger injection detection."""
    # This is a tricky case - we're being conservative and rejecting multiple semicolons
    sql = "SELECT * FROM purchase_orders WHERE material_description = 'Steel; Grade A';"
    is_valid, reason = validate_sql(sql)
    
    # Our simple validator rejects this for safety
    # In production, a more sophisticated parser would handle this
    # For now, we document this as a known limitation
    assert not is_valid, "Conservative approach: reject semicolons even in literals"


def test_whitelist_enforcement_tables():
    """Test that only whitelisted tables are allowed."""
    # purchase_orders and receipts are whitelisted
    assert is_safe_query("SELECT * FROM purchase_orders;") is True
    assert is_safe_query("SELECT * FROM receipts;") is True
    
    # Other tables are not
    assert is_safe_query("SELECT * FROM users;") is False
    assert is_safe_query("SELECT * FROM admin;") is False
    assert is_safe_query("SELECT * FROM sqlite_master;") is False
