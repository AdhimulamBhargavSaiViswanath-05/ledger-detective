"""
Enhanced Streamlit UI for Ledger Detective
Features:
- Light/Dark theme toggle
- Chat history management
- API key configuration
- Better error handling with clarifications
- Responsive design with brand colors
"""

import streamlit as st
import sys
import pandas as pd
import re
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline import run_pipeline_detailed

# Page config
st.set_page_config(
    page_title="Ledger Detective",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "api_key_configured" not in st.session_state:
    st.session_state.api_key_configured = False

# Brand colors (extracted from typical financial/analytical app)
COLORS = {
    "light": {
        "primary": "#0066CC",      # Professional blue
        "secondary": "#00A3E0",    # Light blue
        "success": "#28A745",      # Green
        "warning": "#FFA500",      # Orange
        "error": "#DC3545",        # Red
        "background": "#FFFFFF",
        "surface": "#F8F9FA",
        "text": "#212529",
        "text_secondary": "#6C757D",
        "border": "#DEE2E6",
        "code_bg": "#F5F5F5",
    },
    "dark": {
        "primary": "#4A9EFF",      # Bright blue
        "secondary": "#64B5F6",    # Light blue
        "success": "#4CAF50",      # Green
        "warning": "#FF9800",      # Orange
        "error": "#F44336",        # Red
        "background": "#1A1A1A",
        "surface": "#2D2D2D",
        "text": "#E0E0E0",
        "text_secondary": "#B0B0B0",
        "border": "#404040",
        "code_bg": "#1E1E1E",
    }
}

theme = COLORS[st.session_state.theme]

# Custom CSS with theme support
st.markdown(f"""
<style>
    /* Global theme */
    .stApp {{
        background-color: {theme['background']};
        color: {theme['text']};
    }}
    
    /* Header */
    .main-header {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .main-header h1 {{
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }}
    
    .main-header p {{
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }}
    
    /* Boxes */
    .info-box {{
        background: {theme['surface']};
        border-left: 4px solid {theme['primary']};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: {theme['text']};
    }}
    
    .success-box {{
        background: {theme['surface']};
        border-left: 4px solid {theme['success']};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: {theme['text']};
    }}
    
    .warning-box {{
        background: {theme['surface']};
        border-left: 4px solid {theme['warning']};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: {theme['text']};
    }}
    
    .error-box {{
        background: {theme['surface']};
        border-left: 4px solid {theme['error']};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: {theme['text']};
    }}
    
    /* SQL Code */
    .sql-box {{
        background: {theme['code_bg']};
        color: {theme['text']};
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid {theme['primary']};
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
        font-size: 0.9rem;
    }}
    
    /* Buttons */
    .stButton>button {{
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background-color: {theme['surface']};
    }}
    
    /* Chat messages */
    .stChatMessage {{
        background-color: {theme['surface']};
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {theme['surface']};
        border-radius: 8px;
        color: {theme['text']};
    }}
    
    /* Tables */
    .dataframe {{
        border: 1px solid {theme['border']};
        border-radius: 8px;
    }}
    
    /* Theme toggle */
    .theme-toggle {{
        background: {theme['primary']};
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        cursor: pointer;
        display: inline-block;
        margin-bottom: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Header with logo
st.markdown(f"""
<div class="main-header">
    <h1>🔍 Ledger Detective</h1>
    <p>SAP-Style Procurement Data Reconciliation • AI-Powered Natural Language Queries</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # Theme toggle
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("☀️ Light" if st.session_state.theme == "dark" else "🌙 Dark", use_container_width=True):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    
    with col2:
        if st.button("➕ New Chat", use_container_width=True):
            # Save current chat to history
            if st.session_state.messages:
                chat_data = {
                    "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "timestamp": datetime.now().isoformat(),
                    "messages": st.session_state.messages.copy(),
                    "preview": st.session_state.messages[0]["content"][:50] if st.session_state.messages else "Empty chat"
                }
                st.session_state.chat_history.append(chat_data)
            
            # Clear current chat
            st.session_state.messages = []
            st.session_state.current_chat_id = None
            st.rerun()
    
    st.divider()
    
    # API Configuration
    with st.expander("⚙️ API Configuration", expanded=False):
        st.markdown("**Optional:** Configure API key for production")
        
        api_provider = st.selectbox(
            "Provider",
            ["Mock (Local)", "OpenAI", "Google Gemini"],
            help="Mock mode works locally without API keys"
        )
        
        if api_provider != "Mock (Local)":
            api_key = st.text_input(
                "API Key",
                type="password",
                help="Enter your API key"
            )
            
            if st.button("💾 Save API Key"):
                if api_key:
                    # Save to .env file
                    env_path = Path(__file__).parent / ".env"
                    with open(env_path, "a") as f:
                        if api_provider == "OpenAI":
                            f.write(f"\nOPENAI_API_KEY={api_key}")
                        else:
                            f.write(f"\nGEMINI_API_KEY={api_key}")
                    st.success("✅ API key saved!")
                    st.session_state.api_key_configured = True
                else:
                    st.error("Please enter an API key")
        else:
            st.info("🔧 Running in Mock mode (no API key needed)")
    
    st.divider()
    
    # Database info
    st.header("📊 Database Stats")
    st.markdown("""
    **5 Tables | 916 Records**
    
    - 📋 `po_headers`: 120
    - 📄 `po_items`: 242  
    - 📦 `goods_receipts`: 268
    - 🧾 `invoices`: 101
    - 📊 `invoice_items`: 185
    """)
    
    st.divider()
    
    # Chat history
    if st.session_state.chat_history:
        st.header("💬 Chat History")
        for chat in reversed(st.session_state.chat_history[-5:]):  # Show last 5
            if st.button(
                f"📝 {chat['preview']}...",
                key=f"chat_{chat['id']}",
                use_container_width=True
            ):
                st.session_state.messages = chat['messages'].copy()
                st.session_state.current_chat_id = chat['id']
                st.rerun()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    st.divider()
    
    # Example questions
    st.header("💡 Example Questions")
    
    with st.expander("📈 Basic Queries", expanded=True):
        examples_basic = [
            "How many purchase orders are there?",
            "What is the total amount invoiced?",
            "How many line items exist?",
        ]
        for q in examples_basic:
            if st.button(q, key=f"ex_basic_{q[:20]}", use_container_width=True):
                st.session_state.demo_question = q
    
    with st.expander("🔍 Complex Queries"):
        examples_complex = [
            "Which vendors have the most purchase orders?",
            "Show me unmatched receipts over 100000",
            "Which purchase orders have no goods receipts?",
        ]
        for q in examples_complex:
            if st.button(q, key=f"ex_complex_{q[:20]}", use_container_width=True):
                st.session_state.demo_question = q
    
    with st.expander("📋 Reconciliation"):
        examples_recon = [
            "Show me the three-way match status",
            "Which invoices have price differences?",
            "Show me all goods receipts for PO 4500001",
        ]
        for q in examples_recon:
            if st.button(q, key=f"ex_recon_{q[:20]}", use_container_width=True):
                st.session_state.demo_question = q


def parse_sql_result(raw_result: str):
    """Parse SQL result string into structured data."""
    if not raw_result or raw_result.strip() in ["", "[]", "None"]:
        return None, "No results"
    
    try:
        tuple_pattern = r'\(([^)]+)\)'
        matches = re.findall(tuple_pattern, raw_result)
        
        if not matches:
            return None, raw_result
        
        rows = []
        for match in matches:
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
    """Display query results in themed format."""
    question = result_data.get("question", "")
    sql_query = result_data.get("sql_query", "")
    raw_result = result_data.get("raw_result", "")
    answer = result_data.get("answer", "")
    steps = result_data.get("steps", [])
    error = result_data.get("error", None)
    
    # Show answer
    if error:
        st.markdown(f'<div class="error-box">❌ <strong>Error:</strong> {error}</div>', unsafe_allow_html=True)
    elif "clarification" in answer.lower() or "?" in answer:
        st.markdown(f'<div class="warning-box">❓ <strong>Need more info:</strong> {answer}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="success-box">✅ <strong>Answer:</strong> {answer}</div>', unsafe_allow_html=True)
    
    # Processing steps
    with st.expander("🔄 Processing Steps", expanded=False):
        for step in steps:
            st.markdown(f"• {step}")
    
    # SQL query
    if sql_query and sql_query.strip():
        with st.expander("💻 SQL Query", expanded=True):
            st.code(sql_query, language="sql")
            st.caption("📝 This is the actual SQL query executed")
    
    # Results table
    if raw_result and raw_result.strip() and not error:
        with st.expander("📊 Query Results", expanded=True):
            rows, parse_error = parse_sql_result(raw_result)
            
            if rows and len(rows) > 0:
                num_cols = len(rows[0])
                
                # Smart column naming
                col_names = [f"Col {i+1}" for i in range(num_cols)]
                question_lower = question.lower()
                
                if "vendor" in question_lower and num_cols == 2:
                    col_names = ["Vendor Name", "Count"]
                elif num_cols >= 3 and "po" in question_lower:
                    col_names = ["PO Number", "Vendor", "Amount"] + [f"Col {i+1}" for i in range(3, num_cols)]
                
                df = pd.DataFrame(rows, columns=col_names)
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, (len(rows) + 1) * 35)
                )
                
                st.caption(f"📝 Showing {len(rows)} record(s)")
                
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    data=csv,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.code(raw_result, language="text")


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            display_result(message["content"])

# Handle demo question
if "demo_question" in st.session_state:
    prompt = st.session_state.demo_question
    del st.session_state.demo_question
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing... → 🔄 Generating SQL... → ⚡ Executing..."):
            result_data = run_pipeline_detailed(prompt)
        display_result(result_data)
    
    st.session_state.messages.append({"role": "assistant", "content": result_data})
    st.rerun()

# Chat input
if prompt := st.chat_input("💬 Ask about purchase orders, goods receipts, or invoices..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analyzing... → 🔄 Generating SQL... → ⚡ Executing..."):
            result_data = run_pipeline_detailed(prompt)
        display_result(result_data)
    
    st.session_state.messages.append({"role": "assistant", "content": result_data})

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🔒 Secure & Private")
with col2:
    st.caption("✅ Data-Grounded Answers")
with col3:
    st.caption(f"🎨 Theme: {st.session_state.theme.title()}")
