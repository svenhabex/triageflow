"""Hello unit test module."""

from apps.backend.src.main import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello backend"
