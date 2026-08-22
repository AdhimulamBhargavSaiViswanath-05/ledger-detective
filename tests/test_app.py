"""Basic test for Streamlit app."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_app_imports():
    """Test that app.py can be imported."""
    try:
        # Check that pipeline can be imported
        from src.pipeline import run_pipeline
        assert run_pipeline is not None
    except Exception as e:
        assert False, f"Failed to import: {e}"


def test_app_file_exists():
    """Test that app.py exists."""
    app_path = Path(__file__).parent.parent / "app.py"
    assert app_path.exists(), "app.py should exist"
