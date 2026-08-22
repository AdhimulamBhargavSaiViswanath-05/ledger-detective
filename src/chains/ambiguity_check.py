"""Ambiguity detection - flags underspecified questions."""
from typing import Tuple


# Ambiguous terms that need clarification
AMBIGUOUS_TERMS = {
    'pending': 'Do you mean pending receipt or pending payment?',
    'outstanding': 'Do you mean outstanding quantity or outstanding payment?',
    'status': 'Which status? Receipt status or invoice status?',
    'total': 'Total of what? PO value, invoice amount, or received quantity?',
    'all': 'All of what? All POs, all receipts, or all vendors?',
}


def check_ambiguity(question: str) -> Tuple[bool, str]:
    """
    Check if question contains ambiguous terms.
    
    Args:
        question: Natural language question
        
    Returns:
        Tuple of (is_ambiguous, clarifying_question)
        - is_ambiguous: True if question needs clarification
        - clarifying_question: Question to ask for clarification (empty if not ambiguous)
    """
    question_lower = question.lower()
    
    # Check for standalone ambiguous terms (not qualified)
    for term, clarification in AMBIGUOUS_TERMS.items():
        if term in question_lower:
            # Check if it's already qualified
            qualified_patterns = [
                f'{term} receipt',
                f'{term} payment',
                f'{term} invoice',
                f'receipt {term}',
                f'payment {term}',
                f'invoice {term}',
                f'{term} po',
                f'po {term}',
                f'{term} value of po',  # "total value of PO X"
                f'{term} value of',     # "total value of X"
                f'{term} amount of',    # "total amount of X"
            ]
            
            # Also check if question mentions specific PO number
            has_po_number = any(f'po {n}' in question_lower or f'po{n}' in question_lower 
                              for n in range(4500000, 4600000))
            
            is_qualified = any(pattern in question_lower for pattern in qualified_patterns) or has_po_number
            
            if not is_qualified:
                return True, clarification
    
    return False, ""
