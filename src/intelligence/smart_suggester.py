"""
Smart Suggestion System - Predict and suggest relevant follow-up questions
"""
from typing import List, Dict, Any


class SmartSuggester:
    """Generates intelligent follow-up question suggestions"""
    
    def suggest_followups(self, question: str, answer: str, sql: str, result: str) -> List[str]:
        """Generate relevant follow-up questions based on current conversation"""
        suggestions = []
        
        question_lower = question.lower()
        
        # Count queries → suggest value/details
        if any(word in question_lower for word in ['how many', 'count', 'number of']):
            if 'purchase order' in question_lower or 'po' in question_lower:
                suggestions.extend([
                    "What is the total value of all purchase orders?",
                    "Which vendors have the most purchase orders?",
                    "Show me the status breakdown of these POs"
                ])
            elif 'invoice' in question_lower:
                suggestions.extend([
                    "What is the total amount invoiced?",
                    "Which invoices are still pending?",
                    "Show me invoices with payment issues"
                ])
            elif 'receipt' in question_lower or 'gr' in question_lower:
                suggestions.extend([
                    "Which receipts are unmatched to invoices?",
                    "Show me the most recent goods receipts",
                    "What is the average receipt value?"
                ])
        
        # Total/sum queries → suggest breakdown
        elif any(word in question_lower for word in ['total', 'sum', 'amount']):
            suggestions.extend([
                "Show me the breakdown by vendor",
                "What is the month-over-month trend?",
                "Which items contribute the most to this total?"
            ])
        
        # Vendor queries → suggest vendor analysis
        elif 'vendor' in question_lower or 'supplier' in question_lower:
            if 'most' in question_lower or 'highest' in question_lower:
                suggestions.extend([
                    "What is their on-time delivery rate?",
                    "Show me their price variance history",
                    "Are there any pending issues with this vendor?"
                ])
            else:
                suggestions.extend([
                    "Which vendor has the best performance?",
                    "Compare vendor pricing for the same materials",
                    "Show me vendor payment terms"
                ])
        
        # Anomaly/issue queries → suggest investigation
        elif any(word in question_lower for word in ['issue', 'problem', 'mismatch', 'variance', 'unmatched']):
            suggestions.extend([
                "What is the root cause of these issues?",
                "Show me the historical trend of these problems",
                "Which vendors have the most issues?"
            ])
        
        # Status queries → suggest action items
        elif 'status' in question_lower or 'pending' in question_lower:
            suggestions.extend([
                "Which items need immediate attention?",
                "Show me aging analysis",
                "What actions are required?"
            ])
        
        # Price queries → suggest comparison
        elif 'price' in question_lower or 'cost' in question_lower:
            suggestions.extend([
                "Compare prices across vendors",
                "Show me price trends over time",
                "Which materials have the highest price variance?"
            ])
        
        # If no specific suggestions, provide general exploration
        if not suggestions:
            suggestions = [
                "Run a comprehensive data health check",
                "Show me today's procurement summary",
                "What are the top 3 issues I should know about?"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def suggest_proactive_actions(self) -> List[str]:
        """Suggest proactive questions user might want to ask"""
        return [
            "Run anomaly detection scan",
            "Generate daily procurement summary",
            "Show me three-way match status",
            "Which POs need follow-up?",
            "Compare vendor performance"
        ]
    
    def get_quick_insights(self, db) -> Dict[str, Any]:
        """Get quick insights for dashboard"""
        try:
            # Total POs
            po_count = db.run("SELECT COUNT(*) FROM po_headers")
            
            # Total invoiced
            total_invoiced = db.run("SELECT SUM(total_amount) FROM invoices")
            
            # Pending GRs
            pending_gr = db.run("""
                SELECT COUNT(*) FROM po_headers ph
                LEFT JOIN goods_receipts gr ON ph.po_number = gr.po_number
                WHERE gr.gr_number IS NULL AND ph.status != 'Closed'
            """)
            
            return {
                'total_pos': po_count,
                'total_invoiced': total_invoiced,
                'pending_grs': pending_gr
            }
        except Exception as e:
            return {
                'error': str(e)
            }
