import pytest
from tomlkit.container import Container

from poetry_auto_export.plugin import PoetryAutoExport


def test_placeholder():
    assert PoetryAutoExport()


@pytest.mark.parametrize(
    "data, expected",
    [
        ({"tool": {}}, None),
        ({"tool": {"poetry-auto-export": {}}}, None),
        (
            {"tool": {"poetry-auto-export": {"output": "requirements.txt"}}},
            {"output": "requirements.txt"},
        ),
        (
            {
                "tool": {
                    "poetry-auto-export": {
                        "output": "requirements.txt",
                        "without_hashes": True,
                    }
                }
            },
            {"output": "requirements.txt", "without_hashes": True},
        ),
    ],
)
def test_empty_config_parsing(data, expected):
    plugin = PoetryAutoExport()
    container = Container()
    container.update(data)
    assert plugin.parse_pyproject(container) == expected


@pytest.mark.parametrize(
    "data",
    [
        {"tool": {"poetry-auto-export": "invalid"}},
        {"tool": {"poetry-auto-export": {"output": 1}}},
    ],
)
def test_invalid_config_parsing(data):
    plugin = PoetryAutoExport()
    container = Container()
    container.update(data)
    with pytest.raises(ValueError):
        plugin.parse_pyproject(container)


@pytest.mark.parametrize(
    "config, args",
    [
        (
            {"output": "requirements.txt", "without_hashes": True},
            "-o 'requirements.txt' --without-hashes",
        ),
        (
            {"output": "requirements.txt", "without": ["dev"]},
            "-o 'requirements.txt' --without='dev'",
        ),
        (
            {"output": "requirements.txt", "without": ["dev", "test"]},
            "-o 'requirements.txt' --without='dev' --without='test'",
        ),
        (
            {
                "output": "requirements.txt",
                "with": ["dev", "test"],
                "without": ["main"],
            },
            "-o 'requirements.txt' --with='dev' --with='test' --without='main'",
        ),
    ],
)
def test_prepare_export_args(config, args):
    plugin = PoetryAutoExport()
    plugin.config = config
    assert plugin.prepare_export_args() == args
