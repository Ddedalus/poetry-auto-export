import pytest
from cleo.commands.command import Command
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.inputs.input import Input
from cleo.io.io import IO
from cleo.io.outputs.output import Output
from tomlkit.container import Container

from poetry_auto_export.plugin import (
    AddCommand,
    ExportCommand,
    LockCommand,
    PoetryAutoExport,
    RemoveCommand,
    UpdateCommand,
)


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
    assert plugin._parse_pyproject(container) == expected


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
        plugin._parse_pyproject(container)


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
    assert plugin._prepare_export_args(config, Output()) == args


@pytest.fixture
def dispatcher() -> EventDispatcher:
    return EventDispatcher()


@pytest.fixture
def event() -> Event:
    return ConsoleTerminateEvent(
        command=LockCommand(),
        exit_code=0,
        io=IO(input=Input(), output=Output(), error_output=Output()),
    )


@pytest.fixture
def plugin() -> PoetryAutoExport:
    p = PoetryAutoExport()
    p.configs = [{"output": "requirements.txt"}]
    return p


def test_export_skips_random_event(plugin: PoetryAutoExport, dispatcher, event):
    event._command = Command()
    assert plugin.run_exports(event, "", dispatcher) is None


def test_export_skips_on_export(plugin: PoetryAutoExport, dispatcher, event):
    event._command = ExportCommand()
    assert plugin.run_exports(event, "", dispatcher) is None


@pytest.mark.parametrize(
    "command", [LockCommand, UpdateCommand, AddCommand, RemoveCommand]
)
def test_export_triggers(mocker, command, plugin: PoetryAutoExport, dispatcher, event):
    event._command = command()
    event.io.write_line = mocker.Mock()
    event.command.call = mocker.Mock()

    plugin.run_exports(event, "", dispatcher)

    assert event.io.write_line.call_count >= 1
    assert event.command.call.call_count == 1
