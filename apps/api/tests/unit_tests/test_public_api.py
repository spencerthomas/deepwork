"""Public import and package-data tests."""

from importlib.resources import files

import deepwork_api


def test_public_api_is_deliberate_and_typed() -> None:
    assert deepwork_api.__all__ == ["create_app"]
    assert callable(deepwork_api.create_app)
    assert files("deepwork_api").joinpath("py.typed").is_file()
