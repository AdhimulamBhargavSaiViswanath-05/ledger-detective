"""Database initialization and access layer."""
import sqlite3
from pathlib import Path
import pandas as pd
from langchain_community.utilities import SQLDatabase


# Path constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "ledger.db"

# CSV file paths
PO_HEADERS_CSV = DATA_DIR / "po_headers.csv"
PO_ITEMS_CSV = DATA_DIR / "po_items.csv"
GOODS_RECEIPTS_CSV = DATA_DIR / "goods_receipts.csv"
INVOICES_CSV = DATA_DIR / "invoices.csv"
INVOICE_ITEMS_CSV = DATA_DIR / "invoice_items.csv"

# Legacy CSV paths (for backward compatibility)
PO_CSV = DATA_DIR / "purchase_orders.csv"
RECEIPTS_CSV = DATA_DIR / "receipts.csv"


def init_database():
    """
    Load CSVs into SQLite database.
    
    Creates 5 tables representing SAP-style procurement data:
    1. po_headers - Purchase order headers
    2. po_items - Purchase order line items
    3. goods_receipts - Goods receipt records
    4. invoices - Vendor invoice headers
    5. invoice_items - Invoice line items
    
    Relationships:
    - po_headers (1) -> (N) po_items via po_number
    - po_items (1) -> (N) goods_receipts via (po_number, po_line_item)
    - po_headers (1) -> (N) invoices via po_number
    - invoices (1) -> (N) invoice_items via invoice_number
    - invoice_items references po_items via (po_number, po_line_item)
    """
    # Load all CSV files
    po_headers_df = pd.read_csv(PO_HEADERS_CSV)
    po_items_df = pd.read_csv(PO_ITEMS_CSV)
    goods_receipts_df = pd.read_csv(GOODS_RECEIPTS_CSV)
    invoices_df = pd.read_csv(INVOICES_CSV)
    invoice_items_df = pd.read_csv(INVOICE_ITEMS_CSV)
    
    # Create/overwrite database
    conn = sqlite3.connect(DB_PATH)
    
    # Write dataframes to SQL tables
    po_headers_df.to_sql('po_headers', conn, if_exists='replace', index=False)
    po_items_df.to_sql('po_items', conn, if_exists='replace', index=False)
    goods_receipts_df.to_sql('goods_receipts', conn, if_exists='replace', index=False)
    invoices_df.to_sql('invoices', conn, if_exists='replace', index=False)
    invoice_items_df.to_sql('invoice_items', conn, if_exists='replace', index=False)
    
    conn.close()
    
    print("✓ Database initialized with 5 tables")
    print(f"  - po_headers: {len(po_headers_df)} records")
    print(f"  - po_items: {len(po_items_df)} records")
    print(f"  - goods_receipts: {len(goods_receipts_df)} records")
    print(f"  - invoices: {len(invoices_df)} records")
    print(f"  - invoice_items: {len(invoice_items_df)} records")


def get_database() -> SQLDatabase:
    """
    Get configured SQLDatabase instance.
    
    Initializes database from CSVs if it doesn't exist.
    Returns LangChain SQLDatabase wrapper for query execution.
    """
    # Initialize database if it doesn't exist
    if not DB_PATH.exists():
        init_database()
    
    # Return LangChain SQLDatabase wrapper
    return SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
