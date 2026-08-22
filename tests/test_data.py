"""Tests for mock data files."""
import pandas as pd
import pytest
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"
PO_FILE = DATA_DIR / "purchase_orders.csv"
RECEIPTS_FILE = DATA_DIR / "receipts.csv"


def test_purchase_orders_csv_exists():
    """Purchase orders CSV file should exist."""
    assert PO_FILE.exists(), f"Purchase orders CSV not found at {PO_FILE}"


def test_receipts_csv_exists():
    """Receipts CSV file should exist."""
    assert RECEIPTS_FILE.exists(), f"Receipts CSV not found at {RECEIPTS_FILE}"


def test_purchase_orders_loads():
    """Purchase orders CSV should load with pandas."""
    df = pd.read_csv(PO_FILE)
    assert len(df) > 0, "Purchase orders CSV is empty"


def test_receipts_loads():
    """Receipts CSV should load with pandas."""
    df = pd.read_csv(RECEIPTS_FILE)
    assert len(df) > 0, "Receipts CSV is empty"


def test_purchase_orders_columns():
    """Purchase orders CSV should have expected columns."""
    df = pd.read_csv(PO_FILE)
    expected_columns = [
        'po_number', 'po_line_item', 'vendor_id', 'vendor_name',
        'material_description', 'order_qty', 'unit_price', 'currency',
        'po_value', 'order_date', 'plant'
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col}"


def test_receipts_columns():
    """Receipts CSV should have expected columns."""
    df = pd.read_csv(RECEIPTS_FILE)
    expected_columns = [
        'gr_number', 'po_number', 'po_line_item', 'received_qty',
        'receipt_date', 'invoice_number', 'invoice_amount',
        'invoice_date', 'invoice_status'
    ]
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col}"


def test_partially_received_case_exists():
    """At least one partially-received case should exist in the data."""
    po_df = pd.read_csv(PO_FILE)
    receipts_df = pd.read_csv(RECEIPTS_FILE)
    
    # Join to find cases where received_qty < order_qty
    merged = pd.merge(
        po_df[['po_number', 'po_line_item', 'order_qty']],
        receipts_df[['po_number', 'po_line_item', 'received_qty']],
        on=['po_number', 'po_line_item'],
        how='inner'
    )
    
    partially_received = merged[merged['received_qty'] < merged['order_qty']]
    assert len(partially_received) > 0, "No partially-received cases found in data"


def test_no_receipt_case_exists():
    """At least one no-receipt case should exist in the data."""
    po_df = pd.read_csv(PO_FILE)
    receipts_df = pd.read_csv(RECEIPTS_FILE)
    
    # Find POs that don't appear in receipts
    po_numbers = set(po_df['po_number'].unique())
    receipt_po_numbers = set(receipts_df['po_number'].unique())
    
    no_receipt_pos = po_numbers - receipt_po_numbers
    assert len(no_receipt_pos) > 0, "No no-receipt cases found in data"
