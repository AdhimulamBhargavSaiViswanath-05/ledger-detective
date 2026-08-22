"""Tests for database layer."""
import pandas as pd
import pytest
from pathlib import Path
from src.db import (
    get_database, init_database, DATA_DIR, DB_PATH,
    PO_HEADERS_CSV, PO_ITEMS_CSV, GOODS_RECEIPTS_CSV, 
    INVOICES_CSV, INVOICE_ITEMS_CSV
)


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


def test_database_contains_all_tables():
    """Database should contain all 5 expected tables."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_tables = ['po_headers', 'po_items', 'goods_receipts', 'invoices', 'invoice_items']
    
    for table in expected_tables:
        assert table in table_info, f"{table} table not found in database"


def test_po_headers_has_expected_columns():
    """po_headers table should have all expected columns."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_columns = [
        'po_number', 'vendor_id', 'vendor_name', 'po_date',
        'plant', 'currency', 'payment_terms', 'po_status', 'created_by'
    ]
    
    for col in expected_columns:
        assert col in table_info, f"Column {col} not found in po_headers table"


def test_po_items_has_expected_columns():
    """po_items table should have all expected columns."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_columns = [
        'po_number', 'po_line_item', 'material_code', 'material_description',
        'order_qty', 'unit_price', 'currency', 'po_value', 'uom',
        'delivery_date', 'item_status'
    ]
    
    for col in expected_columns:
        assert col in table_info, f"Column {col} not found in po_items table"


def test_goods_receipts_has_expected_columns():
    """goods_receipts table should have all expected columns."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_columns = [
        'gr_number', 'po_number', 'po_line_item', 'received_qty',
        'receipt_date', 'movement_type', 'storage_location', 'received_by'
    ]
    
    for col in expected_columns:
        assert col in table_info, f"Column {col} not found in goods_receipts table"


def test_invoices_has_expected_columns():
    """invoices table should have all expected columns."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_columns = [
        'invoice_number', 'po_number', 'vendor_id', 'vendor_name',
        'invoice_date', 'posting_date', 'due_date', 'currency',
        'payment_terms', 'invoice_status', 'posted_by'
    ]
    
    for col in expected_columns:
        assert col in table_info, f"Column {col} not found in invoices table"


def test_invoice_items_has_expected_columns():
    """invoice_items table should have all expected columns."""
    db = get_database()
    table_info = db.get_table_info()
    
    expected_columns = [
        'invoice_number', 'invoice_line_item', 'po_number', 'po_line_item',
        'material_code', 'material_description', 'invoice_qty', 'unit_price',
        'currency', 'invoice_amount', 'tax_amount', 'total_amount', 'gr_reference'
    ]
    
    for col in expected_columns:
        assert col in table_info, f"Column {col} not found in invoice_items table"


def test_po_headers_row_count():
    """po_headers table should have expected minimum number of rows."""
    db = get_database()
    result = db.run("SELECT COUNT(*) FROM po_headers")
    count = int(result.strip().strip('[]()').split(',')[0])
    assert count >= 100, f"Expected at least 100 PO headers, got {count}"


def test_po_items_row_count():
    """po_items table should have expected minimum number of rows."""
    db = get_database()
    result = db.run("SELECT COUNT(*) FROM po_items")
    count = int(result.strip().strip('[]()').split(',')[0])
    assert count >= 100, f"Expected at least 100 PO items, got {count}"


def test_goods_receipts_row_count():
    """goods_receipts table should have expected minimum number of rows."""
    db = get_database()
    result = db.run("SELECT COUNT(*) FROM goods_receipts")
    count = int(result.strip().strip('[]()').split(',')[0])
    assert count >= 100, f"Expected at least 100 goods receipts, got {count}"


def test_relationships_po_to_items():
    """All po_items should reference valid po_headers."""
    db = get_database()
    result = db.run("""
        SELECT COUNT(*) FROM po_items poi
        LEFT JOIN po_headers poh ON poi.po_number = poh.po_number
        WHERE poh.po_number IS NULL
    """)
    orphan_count = int(result.strip().strip('[]()').split(',')[0])
    assert orphan_count == 0, f"Found {orphan_count} orphaned PO items without valid header"


def test_relationships_gr_to_po_items():
    """All goods_receipts should reference valid po_items."""
    db = get_database()
    result = db.run("""
        SELECT COUNT(*) FROM goods_receipts gr
        LEFT JOIN po_items poi ON gr.po_number = poi.po_number 
            AND gr.po_line_item = poi.po_line_item
        WHERE poi.po_number IS NULL
    """)
    orphan_count = int(result.strip().strip('[]()').split(',')[0])
    assert orphan_count == 0, f"Found {orphan_count} orphaned goods receipts without valid PO item"


def test_relationships_invoices_to_po():
    """All invoices should reference valid po_headers."""
    db = get_database()
    result = db.run("""
        SELECT COUNT(*) FROM invoices inv
        LEFT JOIN po_headers poh ON inv.po_number = poh.po_number
        WHERE poh.po_number IS NULL
    """)
    orphan_count = int(result.strip().strip('[]()').split(',')[0])
    assert orphan_count == 0, f"Found {orphan_count} orphaned invoices without valid PO"


def test_three_way_match_data_exists():
    """Database should have records with three-way match (PO + GR + Invoice)."""
    db = get_database()
    result = db.run("""
        SELECT COUNT(*) FROM po_items poi
        JOIN goods_receipts gr ON poi.po_number = gr.po_number 
            AND poi.po_line_item = gr.po_line_item
        JOIN invoice_items ii ON poi.po_number = ii.po_number 
            AND poi.po_line_item = ii.po_line_item
    """)
    matched_count = int(result.strip().strip('[]()').split(',')[0])
    assert matched_count > 0, "No three-way matched records found"


def test_unmatched_receipts_exist():
    """Database should have receipts without invoices (for testing queries)."""
    db = get_database()
    result = db.run("""
        SELECT COUNT(*) FROM goods_receipts gr
        LEFT JOIN invoice_items ii ON gr.po_number = ii.po_number 
            AND gr.po_line_item = ii.po_line_item
        WHERE ii.invoice_number IS NULL
    """)
    unmatched_count = int(result.strip().strip('[]()').split(',')[0])
    assert unmatched_count > 0, "No unmatched receipts found (needed for testing)"
