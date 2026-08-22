"""Tests for mock data files."""
import pandas as pd
import pytest
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"
PO_HEADERS_FILE = DATA_DIR / "po_headers.csv"
PO_ITEMS_FILE = DATA_DIR / "po_items.csv"
GOODS_RECEIPTS_FILE = DATA_DIR / "goods_receipts.csv"
INVOICES_FILE = DATA_DIR / "invoices.csv"
INVOICE_ITEMS_FILE = DATA_DIR / "invoice_items.csv"


def test_purchase_orders_csv_exists():
    """PO headers CSV file should exist."""
    assert PO_HEADERS_FILE.exists(), f"PO headers CSV not found at {PO_HEADERS_FILE}"


def test_receipts_csv_exists():
    """Goods receipts CSV file should exist."""
    assert GOODS_RECEIPTS_FILE.exists(), f"Goods receipts CSV not found at {GOODS_RECEIPTS_FILE}"


def test_purchase_orders_loads():
    """PO items CSV should load with pandas."""
    df = pd.read_csv(PO_ITEMS_FILE)
    assert len(df) > 0, "PO items CSV is empty"


def test_receipts_loads():
    """Goods receipts CSV should load with pandas."""
    df = pd.read_csv(GOODS_RECEIPTS_FILE)
    assert len(df) > 0, "Goods receipts CSV is empty"


def test_purchase_orders_columns():
    """PO items CSV should have expected columns."""
    df = pd.read_csv(PO_ITEMS_FILE)
    expected_columns = [
        'po_number', 'po_line_item', 'material_code', 'material_description',
        'order_qty', 'unit_price', 'currency', 'po_value', 'uom',
        'delivery_date', 'item_status'
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col}"


def test_receipts_columns():
    """Goods receipts CSV should have expected columns."""
    df = pd.read_csv(GOODS_RECEIPTS_FILE)
    expected_columns = [
        'gr_number', 'po_number', 'po_line_item', 'received_qty',
        'receipt_date', 'movement_type', 'storage_location', 'received_by'
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col}"


def test_partially_received_case_exists():
    """At least one partially-received case should exist in the data."""
    po_df = pd.read_csv(PO_ITEMS_FILE)
    receipts_df = pd.read_csv(GOODS_RECEIPTS_FILE)
    
    # Join to find cases where received_qty < order_qty
    merged = pd.merge(
        po_df[['po_number', 'po_line_item', 'order_qty']],
        receipts_df[['po_number', 'po_line_item', 'received_qty']],
        on=['po_number', 'po_line_item'],
        how='inner'
    )
    
    # Group receipts by PO line and sum received quantities
    receipts_grouped = receipts_df.groupby(['po_number', 'po_line_item'])['received_qty'].sum().reset_index()
    merged2 = pd.merge(
        po_df[['po_number', 'po_line_item', 'order_qty']],
        receipts_grouped,
        on=['po_number', 'po_line_item'],
        how='inner'
    )
    
    partially_received = merged2[merged2['received_qty'] < merged2['order_qty']]
    assert len(partially_received) > 0, "No partially-received cases found in data"


def test_no_receipt_case_exists():
    """At least one no-receipt case should exist in the data."""
    po_df = pd.read_csv(PO_ITEMS_FILE)
    receipts_df = pd.read_csv(GOODS_RECEIPTS_FILE)
    
    # Find PO line items that don't appear in receipts
    po_keys = set(zip(po_df['po_number'], po_df['po_line_item']))
    receipt_keys = set(zip(receipts_df['po_number'], receipts_df['po_line_item']))
    
    no_receipt_items = po_keys - receipt_keys
    assert len(no_receipt_items) > 0, "No no-receipt cases found in data"
