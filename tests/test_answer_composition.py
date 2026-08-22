"""Tests for answer composition."""
import pytest
from src.chains.answer_composition import compose_answer


def test_compose_count_answer():
    """Test composing answer for COUNT query."""
    question = "How many purchase orders are there?"
    raw_result = "[(10,)]"
    
    answer = compose_answer(question, raw_result)
    
    # Answer should include the number 10
    assert "10" in answer
    # Should be natural language, not technical
    assert "SELECT" not in answer.upper()
    assert "SQL" not in answer.upper()


def test_compose_specific_po_value():
    """Test composing answer for specific PO value lookup."""
    question = "What is the total value of PO 4500123?"
    raw_result = "[(250000,)]"
    
    answer = compose_answer(question, raw_result)
    
    # Answer should include PO number and value
    assert "250000" in answer or "250,000" in answer
    assert "4500123" in answer or "PO" in answer
    # Should not fabricate data
    assert len([c for c in answer if c.isdigit()]) >= 6  # At least the 250000


def test_compose_aggregate_sum():
    """Test composing answer for aggregate sum."""
    question = "What is the total amount invoiced?"
    raw_result = "[(1366700,)]"
    
    answer = compose_answer(question, raw_result)
    
    # Answer should include the total
    assert "1366700" in answer or "1,366,700" in answer
    # Should mention invoice/invoiced
    assert "invoice" in answer.lower() or "total" in answer.lower()


def test_no_fabrication():
    """Ensure answer doesn't fabricate data."""
    question = "How many vendors have supplied materials?"
    raw_result = "[(5,)]"
    
    answer = compose_answer(question, raw_result)
    
    # Should include 5, not other numbers
    assert "5" in answer
    # Should not mention numbers not in result
    assert "10" not in answer
    assert "100" not in answer


def test_natural_language():
    """Test that answer is natural and conversational."""
    question = "What is the value of PO 4500124?"
    raw_result = "[(170000,)]"
    
    answer = compose_answer(question, raw_result)
    
    # Should be a complete sentence (has period or similar)
    assert len(answer) > 10
    assert any(answer.endswith(p) for p in ['.', '!', '?']) or len(answer.split()) > 3
