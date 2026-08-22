"""Enhanced Streamlit interface for Ledger Detective with detailed process view."""
import streamlit as st
import sys
import pandas as pd
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline import run_pipeline_detailed


# Page config
st.set_page_config(
    page_title="Ledger Detective",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
    }
    .main-header p {
        color: #f0f0f0;
        margin: 0.5rem 0 0 0;
    }
    .step-badge {
        background: #4CAF50;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .sql-box {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #007acc;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
    }
    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background: #e8f5e9;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔍 Ledger Detective</h1>
    <p>SAP-Style Procurement Data Reconciliation with AI-Powered Queries</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("📊 Database Info")
    st.markdown("""
    **5 Tables | 916 Records**
    - `po_headers`: 120 records
    - `po_items`: 242 records  
    - `goods_receipts`: 268 records
    - `invoices`: 101 records
    - `invoice_items`: 185 records
    """)
    
    st.divider()
    
    st.header("💡 Example Questions")
    
    # Categorized examples
    with st.expander("📈 Basic Queries", expanded=True):
        if st.button("How many purchase orders?", use_container_width=True):
            st.session_state.demo_question = "How many purchase orders are there?"
        if st.button("Total invoice amount?", use_container_width=True):
            st.session_state.demo_question = "What is the total amount invoiced?"
    
    with st.expander("🔍 Complex Queries"):
        if st.button("Top vendors by POs?", use_container_width=True):
            st.session_state.demo_question = "Which vendors have the most purchase orders?"
        if st.button("Unmatched receipts >100K?", use_container_width=True):
            st.session_state.demo_question = "Show me unmatched receipts over 100000"
        if st.button("Three-way match status?", use_container_width=True):
            st.session_state.demo_question = "Show me the three-way match status for all purchase orders"
    
    with st.expander("📋 Document Queries"):
        if st.button("POs without receipts?", use_container_width=True):
            st.session_state.demo_question = "Which purchase orders have no goods receipts?"
        if st.button("Receipts for PO 4500001?", use_container_width=True):
            st.session_state.demo_question = "Show me all goods receipts for PO 4500001"
    
    st.divider()
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


def parse_sql_result(raw_result: str):
    """Parse SQL result string into structured data."""
    if not raw_result or raw_result.strip() in ["", "[]", "None"]:
        return None, "No results"
    
    # Try to parse as list of tuples
    try:
        # Extract tuples using regex
        tuple_pattern = r'\(([^)]+)\)'
        matches = re.findall(tuple_pattern, raw_result)
        
        if not matches:
            return None, raw_result
        
        rows = []
        for match in matches:
            # Split by comma but preserve quoted strings
            values = []
            current = ""
            in_quotes = False
            for char in match:
                if char == "'" and not in_quotes:
                    in_quotes = True
                elif char == "'" and in_quotes:
                    in_quotes = False
                elif char == "," and not in_quotes:
                    values.append(current.strip().strip("'\""))
                    current = ""
                else:
                    current += char
            if current:
                values.append(current.strip().strip("'\""))
            rows.append(values)
        
        return rows, None
    except Exception as e:
        return None, str(e)


def display_result(result_data):
    """Display query results in a nice format."""
    question = result_data.get("question", "")
    sql_query = result_data.get("sql_query", "")
    raw_result = result_data.get("raw_result", "")
    answer = result_data.get("answer", "")
    steps = result_data.get("steps", [])
    error = result_data.get("error", None)
    
    # Show answer prominently
    if error:
        st.markdown(f'<div class="warning-box">⚠️ <strong>Error:</strong> {error}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="success-box">✅ <strong>Answer:</strong> {answer}</div>', unsafe_allow_html=True)
    
    # Show process steps
    with st.expander("🔄 **Processing Steps**", expanded=False):
        for i, step in enumerate(steps, 1):
            st.markdown(f"**{i}.** {step}")
    
    # Show SQL query
    if sql_query and sql_query.strip():
        with st.expander("💻 **SQL Query Generated**", expanded=True):
            st.code(sql_query, language="sql")
            st.caption("This is the actual SQL query executed against the database")
    
    # Show raw results in table format
    if raw_result and raw_result.strip() and not error:
        with st.expander("📊 **Query Results**", expanded=True):
            rows, parse_error = parse_sql_result(raw_result)
            
            if rows and len(rows) > 0:
                # Determine number of columns
                num_cols = len(rows[0])
                
                # Create column names
                if num_cols == 1:
                    col_names = ["Value"]
                elif num_cols == 2:
                    col_names = ["Column 1", "Column 2"]
                elif num_cols <= 5:
                    col_names = [f"Col {i+1}" for i in range(num_cols)]
                else:
                    col_names = [f"Field {i+1}" for i in range(num_cols)]
                
                # Try to infer better column names from the question
                question_lower = question.lower()
                if "vendor" in question_lower and num_cols == 2:
                    col_names = ["Vendor Name", "Count"]
                elif "po" in question_lower or "purchase order" in question_lower:
                    if num_cols >= 3:
                        col_names = ["PO Number", "Vendor", "Amount"] + [f"Col {i+1}" for i in range(3, num_cols)]
                
                # Create DataFrame
                df = pd.DataFrame(rows, columns=col_names)
                
                # Display table
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, (len(rows) + 1) * 35)
                )
                
                st.caption(f"📝 Showing {len(rows)} record(s)")
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
            else:
                # Show raw result if can't parse
                st.code(raw_result, language="text")
                if parse_error:
                    st.caption(f"Could not parse as table: {parse_error}")


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            display_result(message["content"])

# Handle demo question from sidebar
if "demo_question" in st.session_state:
    prompt = st.session_state.demo_question
    del st.session_state.demo_question
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing question... → 🔄 Generating SQL... → ⚡ Executing query..."):
            result_data = run_pipeline_detailed(prompt)
        display_result(result_data)
    
    # Add to history
    st.session_state.messages.append({"role": "assistant", "content": result_data})
    st.rerun()

# Chat input
if prompt := st.chat_input("💬 Ask a question about purchase orders, receipts, or invoices..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing question... → 🔄 Generating SQL... → ⚡ Executing query..."):
            result_data = run_pipeline_detailed(prompt)
        display_result(result_data)
    
    # Add to history
    st.session_state.messages.append({"role": "assistant", "content": result_data})

# Footer
st.divider()
st.caption("🔒 Secure | ✅ Data-Grounded | 🚀 Production-Ready")
