import importlib.util
import os
import sys
from types import ModuleType

# Add the parent directory of 'src' to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _install_optional_dependency_stubs():
    if (
        importlib.util.find_spec("pyseoanalyzer") is None
        and "pyseoanalyzer" not in sys.modules
    ):
        pyseoanalyzer = ModuleType("pyseoanalyzer")
        pyseoanalyzer.analyze = lambda url: {}
        sys.modules["pyseoanalyzer"] = pyseoanalyzer

    if (
        importlib.util.find_spec("matplotlib") is None
        and "matplotlib" not in sys.modules
    ):
        matplotlib = ModuleType("matplotlib")
        pyplot = ModuleType("matplotlib.pyplot")
        matplotlib.pyplot = pyplot
        sys.modules["matplotlib"] = matplotlib
        sys.modules["matplotlib.pyplot"] = pyplot


_install_optional_dependency_stubs()
