"""Database initialization and access layer."""
import sqlite3
from pathlib import Path
import pandas as pd
from langchain_community.utilities import SQLDatabase


# Path constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "ledger.db"
PO_CSV = DATA_DIR / "purchase_orders.csv"
RECEIPTS_CSV = DATA_DIR / "receipts.csv"


def init_database():
    """Load CSVs into SQLite database."""
    # Load CSVs
    po_df = pd.read_csv(PO_CSV)
    receipts_df = pd.read_csv(RECEIPTS_CSV)
    
    # Create/overwrite database
    conn = sqlite3.connect(DB_PATH)
    
    # Write dataframes to SQL tables
    po_df.to_sql('purchase_orders', conn, if_exists='replace', index=False)
    receipts_df.to_sql('receipts', conn, if_exists='replace', index=False)
    
    conn.close()


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
