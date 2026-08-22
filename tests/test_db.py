"""Tests for database layer."""
import pandas as pd
import pytest
from pathlib import Path
from src.db import get_database, init_database, DATA_DIR, DB_PATH, PO_CSV, RECEIPTS_CSV


def test_init_database_creates_file():
    """init_database should create the SQLite database file."""
    # Clean up if exists
    if DB_PATH.exists():
        DB_PATH.unlink()
    
    init_database()
    assert DB_PATH.exists(), "Database file was not created"


def test_get_database_returns_sqldb():
    """get_database should return a LangChain SQLDatabase instance."""
    db = get_database()
    assert db is not None
    assert hasattr(db, 'get_table_info'), "Database doesn't have get_table_info method"
    assert hasattr(db, 'run'), "Database doesn't have run method"


def test_database_contains_purchase_orders_table():
    """Database should contain purchase_orders table."""
    db = get_database()
    table_info = db.get_table_info()
    assert 'purchase_orders' in table_info, "purchase_orders table not found"


def test_database_contains_receipts_table():
    """Database should contain receipts table."""
    db = get_database()
    table_info = db.get_table_info()
    assert 'receipts' in table_info, "receipts table not found"


def test_purchase_orders_has_expected_columns():
    """purchase_orders table should have all expected columns."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_columns = [
        'po_number', 'po_line_item', 'vendor_id', 'vendor_name',
        'material_description', 'order_qty', 'unit_price', 'currency',
        'po_value', 'order_date', 'plant'
    ]
    
    for col in expected_columns:
        assert col in table_info, f"Column {col} not found in purchase_orders table info"


def test_receipts_has_expected_columns():
    """receipts table should have all expected columns."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_columns = [
        'gr_number', 'po_number', 'po_line_item', 'received_qty',
        'receipt_date', 'invoice_number', 'invoice_amount',
        'invoice_date', 'invoice_status'
    ]
    
    for col in expected_columns:
        assert col in table_info, f"Column {col} not found in receipts table info"


def test_purchase_orders_row_count_matches_csv():
    """purchase_orders table row count should match source CSV."""
    db = get_database()
    result = db.run("SELECT COUNT(*) as count FROM purchase_orders")
    
    # Parse result (LangChain returns string)
    count_str = result.strip()
    if '\n' in count_str:
        count_str = count_str.split('\n')[0]
    db_count = int(count_str.strip('[]()').split(',')[0])
    
    # Compare with CSV
    csv_count = len(pd.read_csv(PO_CSV))
    assert db_count == csv_count, f"Row count mismatch: DB has {db_count}, CSV has {csv_count}"


def test_receipts_row_count_matches_csv():
    """receipts table row count should match source CSV."""
    db = get_database()
    result = db.run("SELECT COUNT(*) as count FROM receipts")
    
    # Parse result (LangChain returns string)
    count_str = result.strip()
    if '\n' in count_str:
        count_str = count_str.split('\n')[0]
    db_count = int(count_str.strip('[]()').split(',')[0])
    
    # Compare with CSV
    csv_count = len(pd.read_csv(RECEIPTS_CSV))
    assert db_count == csv_count, f"Row count mismatch: DB has {db_count}, CSV has {csv_count}"
