"""Tests for SQL execution layer."""
import pytest
from src.chains.execution import execute_sql, safe_execute


def test_execute_count_purchase_orders():
    """Test executing a simple COUNT query."""
    sql = "SELECT COUNT(*) as count FROM purchase_orders;"
    success, result, validation_reason = execute_sql(sql)
    
    assert success is True, f"Query should succeed. Result: {result}"
    assert validation_reason is None, "No validation error expected"
    
    # Result should contain count of 10 (from CSV)
    assert "10" in result, f"Expected count 10, got: {result}"


def test_execute_po_value_lookup():
    """Test executing a specific PO value lookup."""
    sql = "SELECT po_value FROM purchase_orders WHERE po_number = 4500123;"
    success, result, validation_reason = execute_sql(sql)
    
    assert success is True, f"Query should succeed. Result: {result}"
    assert validation_reason is None, "No validation error expected"
    
    # PO 4500123 has value 250000 (from CSV row 2)
    assert "250000" in result, f"Expected PO value 250000, got: {result}"


def test_execute_total_invoice_amount():
    """Test executing aggregate sum query."""
    sql = "SELECT SUM(invoice_amount) as total FROM receipts;"
    success, result, validation_reason = execute_sql(sql)
    
    assert success is True, f"Query should succeed. Result: {result}"
    assert validation_reason is None, "No validation error expected"
    
    # Total invoice amount from CSV:
    # 200000 + 170000 + 352000 + 156000 + 225000 + 22500 + 180000 + 61200 = 1366700
    assert "1366700" in result, f"Expected total 1366700, got: {result}"


def test_execute_invalid_sql_rejected():
    """Test that invalid SQL is rejected by validation."""
    sql = "DROP TABLE purchase_orders;"
    success, result, validation_reason = execute_sql(sql)
    
    assert success is False, "DROP query should be rejected"
    assert validation_reason is not None, "Should have validation reason"
    assert "Validation failed" in result, f"Should mention validation failure, got: {result}"


def test_execute_sql_injection_rejected():
    """Test that SQL injection attempts are rejected."""
    sql = "SELECT * FROM purchase_orders; DELETE FROM receipts;"
    success, result, validation_reason = execute_sql(sql)
    
    assert success is False, "Injection attempt should be rejected"
    assert "injection" in validation_reason.lower() or "multiple" in validation_reason.lower(), \
        f"Should mention injection or multiple statements, got: {validation_reason}"


def test_safe_execute_convenience_function():
    """Test the safe_execute convenience function."""
    # Valid query
    result = safe_execute("SELECT COUNT(*) FROM purchase_orders;")
    assert "10" in result, f"Expected count 10, got: {result}"
    
    # Invalid query - should return error message
    result = safe_execute("DROP TABLE purchase_orders;")
    assert "Validation failed" in result, f"Should return error message, got: {result}"


def test_execute_join_query():
    """Test executing a JOIN query."""
    sql = """
    SELECT p.po_number, p.po_value, r.received_qty 
    FROM purchase_orders p 
    JOIN receipts r ON p.po_number = r.po_number 
    WHERE p.po_number = 4500123;
    """
    success, result, validation_reason = execute_sql(sql)
    
    assert success is True, f"JOIN query should succeed. Result: {result}"
    assert "4500123" in result, f"Should contain PO number, got: {result}"
    assert "250000" in result, f"Should contain PO value 250000, got: {result}"
    assert "80" in result, f"Should contain received qty 80, got: {result}"


def test_execute_nonexistent_table_rejected():
    """Test that queries referencing non-existent tables are rejected."""
    sql = "SELECT * FROM users;"
    success, result, validation_reason = execute_sql(sql)
    
    assert success is False, "Query with non-existent table should be rejected"
    assert "whitelist" in validation_reason.lower() or "table" in validation_reason.lower(), \
        f"Should mention table issue, got: {validation_reason}"
