import importlib.util
import sys
from types import ModuleType


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
