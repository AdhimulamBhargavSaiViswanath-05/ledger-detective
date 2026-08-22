"""Tests for ambiguity detection."""
import pytest
from src.chains.ambiguity_check import check_ambiguity


def test_ambiguous_pending():
    """'pending' without qualifier should be ambiguous."""
    is_ambiguous, clarification = check_ambiguity("show me the pending ones")
    assert is_ambiguous is True
    assert len(clarification) > 0


def test_unambiguous_specific_question():
    """Specific question should not be ambiguous."""
    is_ambiguous, clarification = check_ambiguity("total value of PO 4500123")
    assert is_ambiguous is False
    assert clarification == ""


def test_qualified_pending_not_ambiguous():
    """'pending receipt' is qualified, should not be ambiguous."""
    is_ambiguous, _ = check_ambiguity("show me pending receipt items")
    assert is_ambiguous is False


def test_ambiguous_outstanding():
    """'outstanding' without qualifier should be ambiguous."""
    is_ambiguous, clarification = check_ambiguity("what are the outstanding items")
    assert is_ambiguous is True
    assert "outstanding" in clarification.lower()


def test_specific_po_query():
    """Specific PO query should not be ambiguous."""
    is_ambiguous, _ = check_ambiguity("What is the value of PO 4500124?")
    assert is_ambiguous is False


def test_specific_aggregate():
    """Specific aggregate query should not be ambiguous."""
    is_ambiguous, _ = check_ambiguity("How many purchase orders are there?")
    assert is_ambiguous is False
