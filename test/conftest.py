import os
import sys
import pytest

# Add the parent directory of 'src' to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
