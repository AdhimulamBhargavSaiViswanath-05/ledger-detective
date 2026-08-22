"""Evaluation harness - measures accuracy against test questions."""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import run_pipeline


def load_eval_questions(filepath: str) -> list:
    """Load evaluation questions from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def evaluate_answer(question: str, answer: str, expected_contains: list) -> bool:
    """
    Evaluate if answer is correct.
    
    Args:
        question: The question asked
        answer: The answer returned by pipeline
        expected_contains: List of strings that should appear in the answer
        
    Returns:
        True if answer contains at least one expected string
    """
    answer_lower = answer.lower()
    
    # Answer is correct if it contains ANY of the expected strings
    for expected in expected_contains:
        if expected.lower() in answer_lower:
            return True
    
    return False


def run_evaluation(questions_file: str = None, verbose: bool = True) -> tuple:
    """
    Run evaluation on all test questions.
    
    Args:
        questions_file: Path to eval questions JSON file
        verbose: Whether to print detailed results
        
    Returns:
        Tuple of (total_questions, passed_questions, accuracy_percentage)
    """
    if questions_file is None:
        questions_file = Path(__file__).parent / "eval_questions.json"
    
    questions = load_eval_questions(questions_file)
    
    total = len(questions)
    passed = 0
    
    if verbose:
        print(f"\nRunning evaluation on {total} questions...")
        print("=" * 80)
    
    for i, item in enumerate(questions, 1):
        question = item["question"]
        expected = item["expected_answer_contains"]
        
        # Run pipeline
        answer = run_pipeline(question)
        
        # Evaluate
        is_correct = evaluate_answer(question, answer, expected)
        
        if is_correct:
            passed += 1
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
        
        if verbose:
            print(f"\n{i}. {status}")
            print(f"Q: {question}")
            print(f"A: {answer}")
            if not is_correct:
                print(f"Expected to contain one of: {expected}")
    
    accuracy = (passed / total) * 100
    
    if verbose:
        print("\n" + "=" * 80)
        print(f"\nRESULTS: {passed}/{total} passed ({accuracy:.1f}% accuracy)")
        if accuracy >= 90:
            print("✓ Met 90% accuracy threshold!")
        else:
            print(f"✗ Did not meet 90% threshold (got {accuracy:.1f}%)")
    
    return total, passed, accuracy


if __name__ == "__main__":
    total, passed, accuracy = run_evaluation()
    
    # Exit with error code if accuracy < 90%
    if accuracy < 90:
        sys.exit(1)
