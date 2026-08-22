"""Refusal handling for out-of-scope questions."""


REFUSAL_MESSAGE = """I can only answer questions about purchase orders and receipts in the database. 

I can help you with:
- Purchase order details (values, quantities, vendors)
- Receipt information (received quantities, invoice amounts)
- Aggregate statistics (totals, counts)
- Relationships between POs and receipts

Please ask a question related to these topics."""


def should_refuse(question: str) -> bool:
    """
    Determine if question is out of scope and should be refused.
    
    Args:
        question: Natural language question
        
    Returns:
        True if question should be refused, False otherwise
    """
    question_lower = question.lower()
    
    # Keywords that indicate in-scope questions
    in_scope_keywords = [
        'po', 'purchase', 'order', 'receipt', 'invoice', 'vendor',
        'material', 'quantity', 'value', 'amount', 'price', 'total',
        '4500'  # PO numbers start with 4500
    ]
    
    # If any in-scope keyword present, don't refuse
    if any(keyword in question_lower for keyword in in_scope_keywords):
        return False
    
    # Otherwise, likely out of scope
    return True


def get_refusal_message() -> str:
    """Get the standard refusal message."""
    return REFUSAL_MESSAGE
