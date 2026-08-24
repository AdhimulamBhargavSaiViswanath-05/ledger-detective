"""
Conversation Context Manager - Multi-turn conversation support with entity tracking
"""
from typing import Dict, List, Optional, Any
import re
from datetime import datetime


class ConversationContext:
    """Manages conversation history and entity tracking for multi-turn conversations"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.entities: Dict[str, Any] = {}
        self.last_query_result = None
        self.last_sql = None
        self.session_start = datetime.now()
    
    def add_turn(self, question: str, sql: str, result: str, answer: str):
        """Add a conversation turn and extract entities"""
        turn = {
            'timestamp': datetime.now(),
            'question': question,
            'sql': sql,
            'result': result,
            'answer': answer
        }
        self.history.append(turn)
        self.last_query_result = result
        self.last_sql = sql
        
        # Extract entities from question and result
        self._extract_entities(question, sql, result)
    
    def _extract_entities(self, question: str, sql: str, result: str):
        """Extract and track entities mentioned in conversation"""
        
        # Extract vendor codes (V-XXXX pattern)
        vendors = re.findall(r'V-\d+', question + sql + result)
        if vendors:
            self.entities['vendor_code'] = vendors[0]
            self.entities['vendor_codes'] = list(set(vendors))
        
        # Extract PO numbers (4500XXX pattern)
        po_numbers = re.findall(r'45\d{5}', question + sql + result)
        if po_numbers:
            self.entities['po_number'] = po_numbers[0]
            self.entities['po_numbers'] = list(set(po_numbers))
        
        # Extract invoice numbers (INV-XXXX pattern)
        invoices = re.findall(r'INV-\d+', question + sql + result)
        if invoices:
            self.entities['invoice_number'] = invoices[0]
            self.entities['invoice_numbers'] = list(set(invoices))
        
        # Extract material codes (MAT-XXXX pattern)
        materials = re.findall(r'MAT-\d+', question + sql + result)
        if materials:
            self.entities['material_code'] = materials[0]
            self.entities['material_codes'] = list(set(materials))
        
        # Track table mentions
        if 'po_headers' in sql or 'purchase order' in question.lower():
            self.entities['last_table'] = 'po_headers'
        elif 'goods_receipts' in sql or 'receipt' in question.lower():
            self.entities['last_table'] = 'goods_receipts'
        elif 'invoices' in sql or 'invoice' in question.lower():
            self.entities['last_table'] = 'invoices'
    
    def resolve_references(self, question: str) -> str:
        """Resolve pronouns and references using conversation context"""
        question_lower = question.lower()
        resolved_question = question
        
        # Handle pronouns and references
        if any(ref in question_lower for ref in ['them', 'those', 'these', 'that', 'it', 'their', 'its']):
            
            # "What is their total value?" → Add vendor context
            if self.entities.get('vendor_code'):
                if 'their' in question_lower or 'those' in question_lower:
                    resolved_question = question + f" (for vendor {self.entities['vendor_code']})"
            
            # "What about them?" → Refer to last entity
            if self.entities.get('po_numbers'):
                if 'them' in question_lower or 'those' in question_lower:
                    resolved_question = question + f" (for POs: {', '.join(self.entities['po_numbers'][:3])})"
        
        # Handle follow-up questions without explicit subject
        if len(question.split()) <= 5 and '?' in question:
            # Short question, likely a follow-up
            if self.entities.get('last_table'):
                # Add table context if not explicitly mentioned
                if not any(table in question_lower for table in ['po', 'purchase', 'invoice', 'receipt', 'vendor']):
                    resolved_question = question + f" (from {self.entities['last_table']})"
        
        return resolved_question
    
    def get_context_for_query(self) -> Dict[str, Any]:
        """Get relevant context for SQL generation"""
        return {
            'entities': self.entities,
            'last_sql': self.last_sql,
            'last_result': self.last_query_result,
            'history_count': len(self.history),
            'recent_tables': self._get_recent_tables()
        }
    
    def _get_recent_tables(self) -> List[str]:
        """Get tables mentioned in recent conversation"""
        tables = []
        for turn in self.history[-3:]:  # Last 3 turns
            if turn.get('sql'):
                for table in ['po_headers', 'po_items', 'goods_receipts', 'invoices', 'invoice_items']:
                    if table in turn['sql']:
                        tables.append(table)
        return list(set(tables))
    
    def get_summary(self) -> str:
        """Get conversation summary"""
        duration = (datetime.now() - self.session_start).seconds
        return f"Session: {len(self.history)} questions, {duration}s duration, Entities tracked: {len(self.entities)}"
    
    def clear(self):
        """Clear conversation context (new chat)"""
        self.history = []
        self.entities = {}
        self.last_query_result = None
        self.last_sql = None
        self.session_start = datetime.now()
