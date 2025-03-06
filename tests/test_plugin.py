import hashlib
from pathlib import Path

import pytest
import tomlkit
from cleo.commands.command import Command
from cleo.io.outputs.output import Output
from poetry.console.application import Application
from pytest_mock import MockerFixture
from tomlkit.container import Container

from poetry_auto_export.plugin import (
    AddCommand,
    ExportCommand,
    LockCommand,
    PoetryAutoExport,
    RemoveCommand,
    UpdateCommand,
)
from tests.conftest import FIXTURES_DIR


@pytest.mark.parametrize(
    "data, expected",
    [
        ({"tool": {}}, []),
        ({"tool": {"poetry-auto-export": {}}}, []),
        (
            {"tool": {"poetry-auto-export": {"output": "requirements.txt"}}},
            [{"output": "requirements.txt"}],
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
            [{"output": "requirements.txt", "without_hashes": True}],
        ),
    ],
)
def test_config_parsing(data, expected, plugin: PoetryAutoExport):
    container = Container()
    container.update(data)
    assert plugin._parse_pyproject(container) == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {
                "tool": {
                    "poetry-auto-export": {"exports": [{"output": "requirements.txt"}]}
                }
            },
            [{"output": "requirements.txt"}],
        ),
        (
            {
                "tool": {
                    "poetry-auto-export": {
                        "exports": [
                            {"output": "requirements.txt", "without_hashes": True},
                            {"output": "dev-requirements.txt"},
                        ]
                    }
                }
            },
            [
                {"output": "requirements.txt", "without_hashes": True},
                {"output": "dev-requirements.txt"},
            ],
        ),
    ],
)
def test_nested_config_parsing(data, expected, plugin: PoetryAutoExport):
    container = Container()
    container.update(data)
    assert plugin._parse_pyproject(container) == expected


@pytest.mark.parametrize(
    "data",
    [
        {"tool": {"poetry-auto-export": {"exports": "invalid"}}},
        {"tool": {"poetry-auto-export": {"exports": [{"output": 1}]}}},
    ],
)
def test_invalid_config_parsing_exports(data, plugin: PoetryAutoExport):
    container = Container()
    container.update(data)
    with pytest.raises(ValueError):
        plugin._parse_pyproject(container)


@pytest.mark.parametrize(
    "data",
    [
        {"tool": {"poetry-auto-export": "invalid"}},
        {"tool": {"poetry-auto-export": {"output": 1}}},
    ],
)
def test_invalid_config_parsing(data, plugin: PoetryAutoExport):
    container = Container()
    container.update(data)
    with pytest.raises(ValueError):
        plugin._parse_pyproject_section(container)


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
        (
            {
                "output": "requirements.txt",
                "only": ["dev", "test"],
            },
            "-o 'requirements.txt' --only='dev' --only='test'",
        ),
    ],
)
def test_prepare_export_args(config, args, plugin: PoetryAutoExport):
    assert plugin._prepare_export_args(config, Output()) == args


def test_export_skips_random_event(plugin: PoetryAutoExport, dispatcher, event):
    event._command = Command()
    assert plugin.run_exports(event, "", dispatcher) is None


def test_export_skips_on_export(plugin: PoetryAutoExport, dispatcher, event):
    event._command = ExportCommand()
    assert plugin.run_exports(event, "", dispatcher) is None


@pytest.mark.parametrize(
    "command", [LockCommand, UpdateCommand, AddCommand, RemoveCommand]
)
def test_export_triggers(
    mocker: MockerFixture, command, plugin: PoetryAutoExport, dispatcher, event
):
    event._command = command()
    event.command.call = mocker.Mock()

    plugin.run_exports(event, "", dispatcher)

    assert event.io.write_line.call_count >= 1
    assert event.command.call.call_count == 1


def test_multiple_exports(
    mocker: MockerFixture, plugin: PoetryAutoExport, dispatcher, event
):
    event._command = LockCommand()
    event.command.call = mocker.Mock()
    plugin.configs = [
        {"output": "requirements.txt"},
        {"output": "requirements-dev.txt", "without": ["dev"]},
    ]

    plugin.run_exports(event, "", dispatcher)

    assert event.io.write_line.call_count >= 1
    assert event.command.call.call_count == 2
    assert event.command.call.call_count == 2


def test_config_loading_from_pyproject(plugin: PoetryAutoExport):
    path = FIXTURES_DIR / "multiple_pyproject.toml"
    pyproject = tomlkit.parse(path.read_text())
    config = plugin._parse_pyproject(pyproject)

    assert len(config) == 2


def test_incorrect_table_type(plugin: PoetryAutoExport):
    path = FIXTURES_DIR / "out_of_order_table.toml"
    pyproject = tomlkit.parse(path.read_text())
    config = plugin._parse_pyproject(pyproject)

    assert len(config) == 1


def test_activate_current_directory(plugin: PoetryAutoExport):
    application = Application()
    assert application.event_dispatcher
    listeners_count = len(application.event_dispatcher._listeners)

    plugin.activate(application)

    assert len(application.event_dispatcher._listeners) == listeners_count + 1


def test_activate_no_pyproject_present(cwd_without_pyproject, plugin: PoetryAutoExport):
    application = Application()
    assert application.event_dispatcher
    listeners_count = len(application.event_dispatcher._listeners)

    plugin.activate(application)

    assert len(application.event_dispatcher._listeners) == listeners_count


def test_hash_generation(
    mocker: MockerFixture,
    basic_project: Path,
    event,
    dispatcher,
    plugin: PoetryAutoExport,
):
    # Given
    application = Application()
    event._command = LockCommand()
    event.command.call = mocker.Mock()
    lock_file_path = basic_project / "poetry.lock"
    requirements_path = basic_project / "requirements.txt"
    requirements_path.write_text("Example requirements file")
    lock_hash = hashlib.sha1(lock_file_path.read_bytes()).hexdigest()

    # When
    plugin.activate(application)
    plugin.run_exports(event, "", dispatcher)

    # Then
    requirements_text = requirements_path.read_text()
    assert "Example requirements file" in requirements_text
    assert "generated by poetry-auto-export" in requirements_text

    first_line = requirements_text.split("\n")[0]
    assert first_line == f"# poetry.lock hash: {lock_hash}"
