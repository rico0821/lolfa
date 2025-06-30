import pytest
import sys
import os

if __name__ == "__main__":
    # Ensure project root is in sys.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    # Run all tests in the tests directory
    exit(pytest.main([os.path.dirname(__file__)])) 