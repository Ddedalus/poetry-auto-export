import os
from pathlib import Path

import pytest
import tomlkit
from cleo.commands.command import Command
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.inputs.input import Input
from cleo.io.io import IO
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


@pytest.fixture
def dispatcher() -> EventDispatcher:
    return EventDispatcher()


@pytest.fixture
def event(mocker: MockerFixture) -> Event:
    e = ConsoleTerminateEvent(
        command=LockCommand(),
        exit_code=0,
        io=IO(input=Input(), output=Output(), error_output=Output()),
    )
    e.io.write_line = mocker.Mock()
    return e


@pytest.fixture
def plugin() -> PoetryAutoExport:
    p = PoetryAutoExport()
    p.configs = [{"output": "requirements.txt"}]
    return p


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
    path = Path(__file__).parent / "fixtures" / "multiple_pyproject.toml"
    pyproject = tomlkit.parse(path.read_text())
    config = plugin._parse_pyproject(pyproject)

    assert len(config) == 2


def test_incorrect_table_type(plugin: PoetryAutoExport):
    path = Path(__file__).parent / "fixtures" / "out_of_order_table.toml"
    pyproject = tomlkit.parse(path.read_text())
    config = plugin._parse_pyproject(pyproject)

    assert len(config) == 1


def test_activate_current_directory(plugin: PoetryAutoExport):
    application = Application()
    assert application.event_dispatcher
    listeners_count = len(application.event_dispatcher._listeners)

    plugin.activate(application)

    assert len(application.event_dispatcher._listeners) == listeners_count + 1


@pytest.fixture
def cwd_without_pyproject(tmp_path: Path):
    """This scenario represents a new project, where there is no pyproject.toml file yet.
    User may want to run `poetry init` or just `poetry --help`
    """
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)


def test_activate_no_pyproject_present(cwd_without_pyproject, plugin: PoetryAutoExport):
    application = Application()
    assert application.event_dispatcher
    listeners_count = len(application.event_dispatcher._listeners)

    plugin.activate(application)

    assert len(application.event_dispatcher._listeners) == listeners_count
