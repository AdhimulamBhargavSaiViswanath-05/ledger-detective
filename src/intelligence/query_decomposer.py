"""
Query Decomposition - Break complex questions into multiple steps
"""
from typing import List, Dict, Any, Tuple
import re


class QueryStep:
    """Represents a single step in a multi-step query"""
    
    def __init__(self, step_id: int, description: str, query_type: str, 
                 intent: str, depends_on: List[int] = None):
        self.step_id = step_id
        self.description = description
        self.query_type = query_type  # 'aggregate', 'filter', 'join', 'compare'
        self.intent = intent
        self.depends_on = depends_on or []
        self.result = None


class QueryDecomposer:
    """Decomposes complex questions into executable steps"""
    
    def should_decompose(self, question: str) -> bool:
        """Determine if question needs decomposition"""
        question_lower = question.lower()
        
        # Indicators of complex queries
        comparison_words = ['compare', 'versus', 'vs', 'difference between']
        multi_metric_words = ['and', 'along with', 'as well as']
        conditional_words = ['if', 'when', 'where', 'with', 'without']
        
        # Check for comparison
        if any(word in question_lower for word in comparison_words):
            return True
        
        # Check for multiple metrics
        word_count = len(question.split())
        and_count = question_lower.count(' and ')
        if word_count > 15 and and_count >= 2:
            return True
        
        # Check for complex conditions
        where_clause = any(word in question_lower for word in ['where', 'with', 'that have'])
        aggregate = any(word in question_lower for word in ['average', 'total', 'sum', 'count'])
        if where_clause and aggregate and word_count > 12:
            return True
        
        return False
    
    def decompose(self, question: str) -> List[QueryStep]:
        """Decompose complex question into steps"""
        question_lower = question.lower()
        steps = []
        
        # Pattern 1: Comparison queries
        if any(word in question_lower for word in ['compare', 'versus', 'vs', 'difference']):
            steps = self._decompose_comparison(question)
        
        # Pattern 2: Multiple aggregations
        elif question_lower.count(' and ') >= 2 and any(word in question_lower for word in ['total', 'average', 'count']):
            steps = self._decompose_multi_aggregate(question)
        
        # Pattern 3: Filtered aggregation
        elif any(word in question_lower for word in ['where', 'with', 'that have']):
            steps = self._decompose_filtered_aggregate(question)
        
        # Pattern 4: Vendor/entity analysis
        elif 'vendor' in question_lower and any(word in question_lower for word in ['performance', 'analysis', 'breakdown']):
            steps = self._decompose_vendor_analysis(question)
        
        return steps if steps else [QueryStep(1, question, 'simple', question)]
    
    def _decompose_comparison(self, question: str) -> List[QueryStep]:
        """Decompose comparison queries"""
        steps = []
        
        # Example: "Compare average PO value per vendor with their invoice amounts"
        if 'average' in question.lower() and 'invoice' in question.lower():
            steps.append(QueryStep(
                step_id=1,
                description="Get average PO value per vendor",
                query_type='aggregate',
                intent="SELECT vendor_code, AVG(total_value) FROM po_items GROUP BY vendor_code"
            ))
            steps.append(QueryStep(
                step_id=2,
                description="Get total invoice amount per vendor",
                query_type='aggregate',
                intent="SELECT vendor_code, SUM(total_amount) FROM invoices GROUP BY vendor_code",
                depends_on=[1]
            ))
            steps.append(QueryStep(
                step_id=3,
                description="Calculate variance between PO and invoice",
                query_type='compare',
                intent="Compare results from step 1 and step 2",
                depends_on=[1, 2]
            ))
        
        return steps
    
    def _decompose_multi_aggregate(self, question: str) -> List[QueryStep]:
        """Decompose multiple aggregation queries"""
        steps = []
        
        # Example: "Show total POs, invoices, and goods receipts by vendor"
        if 'vendor' in question.lower():
            if 'po' in question.lower() or 'purchase' in question.lower():
                steps.append(QueryStep(
                    step_id=1,
                    description="Count purchase orders by vendor",
                    query_type='aggregate',
                    intent="SELECT vendor_code, COUNT(*) FROM po_headers GROUP BY vendor_code"
                ))
            
            if 'invoice' in question.lower():
                steps.append(QueryStep(
                    step_id=2,
                    description="Count invoices by vendor",
                    query_type='aggregate',
                    intent="SELECT vendor_code, COUNT(*) FROM invoices GROUP BY vendor_code",
                    depends_on=[1]
                ))
            
            if 'receipt' in question.lower() or 'gr' in question.lower():
                steps.append(QueryStep(
                    step_id=3,
                    description="Count goods receipts by vendor (via PO)",
                    query_type='aggregate',
                    intent="SELECT vendor_code, COUNT(*) FROM goods_receipts JOIN po_headers",
                    depends_on=[1, 2]
                ))
        
        return steps
    
    def _decompose_filtered_aggregate(self, question: str) -> List[QueryStep]:
        """Decompose filtered aggregation queries"""
        steps = []
        
        # Example: "Total value of POs where vendor is from Karnataka"
        steps.append(QueryStep(
            step_id=1,
            description="Filter entities based on condition",
            query_type='filter',
            intent="Identify matching records"
        ))
        steps.append(QueryStep(
            step_id=2,
            description="Calculate aggregate on filtered results",
            query_type='aggregate',
            intent="Compute total/average/count",
            depends_on=[1]
        ))
        
        return steps
    
    def _decompose_vendor_analysis(self, question: str) -> List[QueryStep]:
        """Decompose vendor performance/analysis queries"""
        steps = []
        
        steps.append(QueryStep(
            step_id=1,
            description="Get vendor PO statistics",
            query_type='aggregate',
            intent="COUNT POs, SUM values per vendor"
        ))
        steps.append(QueryStep(
            step_id=2,
            description="Get vendor invoice statistics",
            query_type='aggregate',
            intent="COUNT invoices, SUM amounts per vendor",
            depends_on=[1]
        ))
        steps.append(QueryStep(
            step_id=3,
            description="Calculate vendor performance metrics",
            query_type='compare',
            intent="Compute reliability, price variance, on-time rate",
            depends_on=[1, 2]
        ))
        
        return steps
    
    def format_execution_plan(self, steps: List[QueryStep]) -> str:
        """Format decomposition steps for display"""
        if len(steps) == 1:
            return None  # Simple query, no decomposition needed
        
        plan = "🧩 Breaking down your complex question into steps:\n\n"
        
        for step in steps:
            emoji = "📊" if step.query_type == 'aggregate' else "🔍" if step.query_type == 'filter' else "⚖️"
            plan += f"{emoji} Step {step.step_id}: {step.description}\n"
        
        plan += f"\nExecuting {len(steps)} steps..."
        return plan
