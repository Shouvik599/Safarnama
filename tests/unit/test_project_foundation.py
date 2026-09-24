"""Phase 0 smoke tests: the package structure is importable."""

from src import __version__


def test_package_version() -> None:
    assert __version__ == "0.1.0"


def test_subpackages_importable() -> None:
    import src.api
    import src.graph
    import src.models
    import src.nodes
    import src.prompts
    import src.tools

    assert src.api.__doc__
    assert src.graph.__doc__
    assert src.models.__doc__
    assert src.nodes.__doc__
    assert src.prompts.__doc__
    assert src.tools.__doc__
