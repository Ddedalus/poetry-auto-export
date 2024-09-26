import os
import shutil
from pathlib import Path

import pytest
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.inputs.string_input import StringInput
from cleo.io.io import IO
from cleo.io.outputs.output import Output
from pytest_mock import MockerFixture

from poetry_auto_export.plugin import LockCommand, PoetryAutoExport


@pytest.fixture
def dispatcher() -> EventDispatcher:
    return EventDispatcher()


@pytest.fixture
def event(io: IO, mocker: MockerFixture) -> Event:
    e = ConsoleTerminateEvent(command=LockCommand(), exit_code=0, io=io)
    e.io.write_line = mocker.Mock()
    return e


@pytest.fixture
def plugin() -> PoetryAutoExport:
    p = PoetryAutoExport()
    p.configs = [{"output": "requirements.txt"}]
    return p


@pytest.fixture
def io():
    return IO(input=StringInput(""), output=Output(), error_output=Output())


@pytest.fixture
def cwd_without_pyproject(tmp_path: Path):
    """This scenario represents a new project, where there is no pyproject.toml file yet.
    User may want to run `poetry init` or just `poetry --help`
    """
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)
    os.chdir(cwd)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def basic_project(cwd_without_pyproject):
    for file in (FIXTURES_DIR / "basic_project").glob("*"):
        shutil.copy(file, cwd_without_pyproject)
    yield cwd_without_pyproject
