"""Streamlit chat interface for ledger-detective."""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline import run_pipeline


# Page config
st.set_page_config(
    page_title="Ledger Detective",
    page_icon="🔍",
    layout="centered"
)

# Title
st.title("🔍 Ledger Detective")
st.markdown("*Ask questions about your purchase orders and receipts*")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about purchase orders or receipts..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_pipeline(prompt)
        st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with examples
with st.sidebar:
    st.header("Example Questions")
    st.markdown("""
    - How many purchase orders are there?
    - What is the value of PO 4500123?
    - What is the total amount invoiced?
    - Which vendors have supplied materials?
    - Show me all receipts for PO 4500124
    """)
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
