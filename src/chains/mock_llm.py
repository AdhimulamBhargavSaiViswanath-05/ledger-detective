"""Mock LLM for development/testing when API keys are unavailable."""
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun


class MockSQLGenerationLLM(BaseChatModel):
    """
    Mock LLM that returns valid SQL queries for testing.
    
    This is a development-time mock to unblock testing when API keys are unavailable.
    Replace with real LLM (ChatOpenAI or ChatGoogleGenerativeAI) for production.
    """
    
    # Predefined SQL responses for common questions
    # Order matters - more specific matches should come first
    _sql_map = {
        # Count queries (specific)
        "how many purchase orders are there":
            "SELECT COUNT(*) as count FROM purchase_orders;",
        
        # Aggregate sums
        "what is the total amount invoiced":
            "SELECT SUM(invoice_amount) as total_invoiced FROM receipts;",
        
        "what is the total invoice amount":
            "SELECT SUM(invoice_amount) as total_invoiced FROM receipts;",
            
        "what is the total value of all purchase orders":
            "SELECT SUM(po_value) as total_value FROM purchase_orders;",
        
        # Specific PO lookups
        "what is the total value of po 4500123": 
            "SELECT po_value FROM purchase_orders WHERE po_number = 4500123;",
        
        "show me all receipts for po 4500124":
            "SELECT * FROM receipts WHERE po_number = 4500124;",
        
        # Vendor queries
        "which vendors have supplied materials":
            "SELECT DISTINCT vendor_name FROM purchase_orders;",
        
        # Delete attempts (should be caught by validation)
        "delete all records from purchase_orders":
            "SELECT * FROM purchase_orders;",
        
        # Complex aggregate
        "which pos above 50000 have not been fully received":
            "SELECT p.po_number, p.po_value, p.order_qty, COALESCE(r.received_qty, 0) as received_qty FROM purchase_orders p LEFT JOIN receipts r ON p.po_number = r.po_number AND p.po_line_item = r.po_line_item WHERE p.po_value > 50000 AND (r.received_qty IS NULL OR r.received_qty < p.order_qty);",
    }
    
    @property
    def _llm_type(self) -> str:
        return "mock-sql-generation"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate SQL query based on the last message."""
        # Extract question from the last message
        last_message = messages[-1].content.lower()
        
        # Extract the actual user question from the prompt
        # Look for "User Question:" pattern in the prompt
        import re
        question_match = re.search(r'user question:\s*(.+?)(?:\n|$)', last_message, re.IGNORECASE)
        if question_match:
            user_question = question_match.group(1).strip().lower()
        else:
            user_question = last_message
        
        # Try to find a matching SQL query
        sql_query = None
        for question_key, sql in self._sql_map.items():
            if question_key in user_question:
                sql_query = sql
                break
        
        # If no exact match, generate a simple SELECT based on detected tables
        if sql_query is None:
            if "purchase_orders" in last_message or "purchase order" in last_message:
                sql_query = "SELECT * FROM purchase_orders LIMIT 10;"
            elif "receipts" in last_message or "receipt" in last_message:
                sql_query = "SELECT * FROM receipts LIMIT 10;"
            else:
                sql_query = "SELECT 1;"  # Fallback
        
        # Create response message
        message = AIMessage(content=sql_query)
        generation = ChatGeneration(message=message)
        
        return ChatResult(generations=[generation])
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generation - delegates to sync for simplicity."""
        return self._generate(messages, stop, run_manager, **kwargs)
