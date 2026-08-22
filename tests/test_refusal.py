"""Tests for refusal handling."""
import pytest
from src.chains.refusal import should_refuse, get_refusal_message


def test_refuse_weather_question():
    """Weather questions should be refused."""
    assert should_refuse("What's the weather?") is True


def test_refuse_unrelated_question():
    """Unrelated questions should be refused."""
    assert should_refuse("Tell me a joke") is True
    assert should_refuse("What is the capital of France?") is True


def test_accept_po_question():
    """PO-related questions should not be refused."""
    assert should_refuse("What is the value of PO 4500123?") is False
    assert should_refuse("How many purchase orders are there?") is False


def test_accept_receipt_question():
    """Receipt-related questions should not be refused."""
    assert should_refuse("Show me all receipts") is False
    assert should_refuse("What is the total invoice amount?") is False


def test_accept_vendor_question():
    """Vendor-related questions should not be refused."""
    assert should_refuse("Which vendors have supplied materials?") is False


def test_refusal_message_exists():
    """Refusal message should be non-empty."""
    message = get_refusal_message()
    assert len(message) > 0
    assert "purchase" in message.lower() or "receipt" in message.lower()
