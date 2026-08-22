"""Tests for full end-to-end pipeline."""
import pytest
from src.pipeline import run_pipeline


def test_pipeline_count_question():
    """Test full pipeline with COUNT question."""
    question = "How many purchase orders are there?"
    answer = run_pipeline(question)
    
    # Should contain the count (10 POs in our data)
    assert "10" in answer
    # Should not be an error message
    assert "Error" not in answer
    assert "failed" not in answer.lower()


def test_pipeline_specific_po_value():
    """Test full pipeline with specific PO lookup."""
    question = "What is the total value of PO 4500123?"
    answer = run_pipeline(question)
    
    # Should contain PO number and a value (mock may vary)
    assert "4500123" in answer
    assert any(c.isdigit() for c in answer)
    assert "Error" not in answer


def test_pipeline_aggregate_sum():
    """Test full pipeline with aggregate sum."""
    question = "What is the total invoice amount?"
    answer = run_pipeline(question)
    
    # Should contain the total (1366700)
    assert "1366700" in answer or "1,366,700" in answer
    assert "Error" not in answer


def test_pipeline_refusal():
    """Test pipeline refuses out-of-scope questions."""
    question = "What's the weather today?"
    answer = run_pipeline(question)
    
    # Should contain refusal message
    assert "purchase" in answer.lower() or "receipt" in answer.lower()
    assert "can only" in answer.lower() or "cannot" in answer.lower()


def test_pipeline_ambiguity():
    """Test pipeline catches ambiguous questions."""
    question = "Show me the pending ones"
    answer = run_pipeline(question)
    
    # Should ask for clarification
    assert "clarification" in answer.lower() or "pending" in answer.lower()


def test_pipeline_dangerous_sql_rejected():
    """Test pipeline rejects dangerous SQL attempts."""
    # This question might trigger SQL generation but should be blocked by validation
    question = "Delete all purchase orders"
    answer = run_pipeline(question)
    
    # Should not execute successfully - either refused or validation failed
    assert "10" not in answer  # Should not return count of deleted records
