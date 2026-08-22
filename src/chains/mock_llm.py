"""Mock LLM for development/testing when API keys are unavailable."""
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun


class MockSQLGenerationLLM(BaseChatModel):
    """
    Mock LLM that attempts to generate SQL queries intelligently.
    
    This is a development-time mock. For production, use real LLM (ChatOpenAI or ChatGoogleGenerativeAI).
    
    The mock tries to be smart by:
    - Parsing the schema from the prompt
    - Understanding the question intent
    - Generating appropriate SQL
    - Refusing gracefully when out of scope
    """
    
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
        """Generate SQL query by analyzing prompt and question."""
        import re
        
        prompt = messages[-1].content
        
        # Extract user question (last "Question:" in prompt)
        all_questions = list(re.finditer(r'question:\s*(.+?)(?:\n|response:|$)', prompt, re.IGNORECASE))
        if all_questions:
            user_question = all_questions[-1].group(1).strip()
        else:
            user_question = prompt
        
        # Extract available tables from schema section
        schema_match = re.search(r'available database schema:(.*?)(?:examples:|your task:|$)', prompt, re.IGNORECASE | re.DOTALL)
        available_tables = []
        if schema_match:
            schema_text = schema_match.group(1).lower()
            if 'po_headers' in schema_text:
                available_tables.append('po_headers')
            if 'po_items' in schema_text:
                available_tables.append('po_items')
            if 'goods_receipts' in schema_text:
                available_tables.append('goods_receipts')
            if 'invoices' in schema_text:
                available_tables.append('invoices')
            if 'invoice_items' in schema_text:
                available_tables.append('invoice_items')
        
        # Analyze question intent
        q_lower = user_question.lower()
        
        # Check for unclear/vague questions that need clarification
        unclear_patterns = [
            (r'^(list|show|tell|give|display)$', "Could you please specify what you'd like to see? For example: 'Show me all vendors' or 'List purchase orders'"),
            (r'^(what|which|how)$', "Could you please complete your question? For example: 'What is the total value?' or 'Which vendors have orders?'"),
            (r'^\w{1,3}$', "I need more context. Could you please ask a complete question about purchase orders, invoices, or receipts?"),
        ]
        
        for pattern, clarification in unclear_patterns:
            if re.match(pattern, q_lower.strip()):
                return f"NEEDS_CLARIFICATION: {clarification}"
        
        # Decision logic: Can this be answered from available data?
        has_data_context = any(term in q_lower for term in [
            'po', 'purchase', 'order', 'receipt', 'invoice', 'vendor', 
            'supplier', 'material', 'gr', 'goods', 'payment', 'value', 
            'amount', 'quantity', 'qty', 'received', 'delivered',
            'pending', 'outstanding', 'status', 'total', 'all', 'headers',
            'items', 'line', 'table', 'column', 'field', 'record'
        ])
        
        # If no data context, refuse
        if not has_data_context:
            sql_query = f"OUT_OF_SCOPE: I only have data about {', '.join(available_tables)}. I cannot answer questions about '{q_lower.split()[0] if q_lower else 'this topic'}'."
        else:
            # Generate SQL based on question patterns
            sql_query = self._generate_sql_from_intent(q_lower, available_tables)
        
        # Create response
        message = AIMessage(content=sql_query)
        generation = ChatGeneration(message=message)
        
        return ChatResult(generations=[generation])
    
    def _generate_sql_from_intent(self, question: str, tables: List[str]) -> str:
        """Generate SQL based on question intent (simplified for mock)."""
        # Check for ambiguous patterns first
        ambiguous_terms = ['pending', 'outstanding', 'status', 'total', 'all']
        for term in ambiguous_terms:
            if term in question:
                # Check if it's qualified
                qualified = any(qual in question for qual in [
                    'receipt', 'invoice', 'payment', 'po ', 'order', 
                    'vendor', 'value of', 'amount of', 'quantity'
                ])
                # Also check for specific PO numbers
                import re
                has_po_number = bool(re.search(r'\b45\d{5}\b', question))
                
                if not qualified and not has_po_number:
                    if term == 'pending':
                        return "NEEDS_CLARIFICATION: Do you mean pending receipts or pending invoices?"
                    elif term == 'outstanding':
                        return "NEEDS_CLARIFICATION: Do you mean outstanding quantity or outstanding payment?"
                    elif term == 'status':
                        return "NEEDS_CLARIFICATION: Which status? Receipt status or invoice status?"
                    elif term == 'total':
                        return "NEEDS_CLARIFICATION: Total of what? PO value, invoice amount, or received quantity?"
                    elif term == 'all':
                        return "NEEDS_CLARIFICATION: All of what? All POs, all receipts, or all vendors?"
        
        # Count queries
        if 'how many' in question or 'count' in question:
            if 'receipt' in question or 'gr' in question:
                return "SELECT COUNT(*) as count FROM goods_receipts;"
            elif 'invoice' in question:
                return "SELECT COUNT(*) as count FROM invoices;"
            elif 'line item' in question or 'item' in question:
                return "SELECT COUNT(*) as count FROM po_items;"
            else:
                return "SELECT COUNT(*) as count FROM po_headers;"
        
        # Sum/Total queries
        if 'total' in question or 'sum' in question:
            if 'invoice' in question:
                return "SELECT SUM(ii.invoice_amount) as total FROM invoice_items ii;"
            elif 'po' in question or 'purchase' in question:
                return "SELECT SUM(poi.po_value) as total FROM po_items poi;"
        
        # Specific PO lookups
        import re
        po_match = re.search(r'\b(45\d{5})\b', question)
        if po_match:
            po_number = po_match.group(1)
            if 'receipt' in question or 'gr' in question:
                return f"SELECT * FROM goods_receipts WHERE po_number = {po_number};"
            elif 'invoice' in question:
                return f"SELECT * FROM invoices WHERE po_number = {po_number};"
            else:
                return f"SELECT * FROM po_headers WHERE po_number = {po_number};"
        
        # Vendor queries
        if 'vendor' in question or 'supplier' in question:
            if 'which' in question or 'list' in question or 'most' in question:
                return "SELECT vendor_name, COUNT(*) as po_count FROM po_headers GROUP BY vendor_name ORDER BY po_count DESC;"
            else:
                return "SELECT DISTINCT vendor_name FROM po_headers;"
        
        # Missing invoices
        if 'no invoice' in question or 'without invoice' in question:
            return "SELECT poh.po_number, poh.vendor_name FROM po_headers poh WHERE NOT EXISTS (SELECT 1 FROM invoices inv WHERE inv.po_number = poh.po_number);"
        
        # Value/amount above threshold
        if 'above' in question or '>' in question:
            threshold_match = re.search(r'\b(\d{4,})\b', question)
            if threshold_match:
                threshold = threshold_match.group(1)
                if 'not received' in question or 'pending' in question:
                    return f"SELECT poh.* FROM po_headers poh WHERE NOT EXISTS (SELECT 1 FROM goods_receipts gr WHERE gr.po_number = poh.po_number) AND EXISTS (SELECT 1 FROM po_items poi WHERE poi.po_number = poh.po_number AND poi.po_value > {threshold});"
                else:
                    return f"SELECT poh.* FROM po_headers poh JOIN po_items poi ON poh.po_number = poi.po_number WHERE poi.po_value > {threshold};"
        
        # Default: return sample data
        if 'receipt' in question or 'gr' in question:
            return "SELECT * FROM goods_receipts LIMIT 10;"
        elif 'invoice' in question:
            return "SELECT * FROM invoices LIMIT 10;"
        else:
            return "SELECT * FROM po_headers LIMIT 10;"
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generation - delegates to sync for simplicity."""
        return self._generate(messages, stop, run_manager, **kwargs)

