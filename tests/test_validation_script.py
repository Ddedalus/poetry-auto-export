import subprocess
from pathlib import Path

import pytest
from poetry.console.application import Application
from pytest_mock import MockerFixture

from poetry_auto_export.plugin import LockCommand, PoetryAutoExport

repo_root = Path(__file__).parent.parent
check_requirements_file_path = (
    repo_root / "poetry_auto_export/check_requirements_file.py"
).absolute()


@pytest.fixture
def valid_project(
    mocker: MockerFixture,
    basic_project: Path,
    event,
    dispatcher,
    plugin: PoetryAutoExport,
) -> Path:
    """
    A poetry project with up-to-date generated requirements.txt file.
    This fixture only runs the part of the plugin responsible for generating the commeent in requirements.txt.
    """
    application = Application()
    event._command = LockCommand()
    event.command.call = mocker.Mock()
    (basic_project / "requirements.txt").write_text("Placeholder value")
    # When
    plugin.activate(application)
    plugin.run_exports(event, "", dispatcher)
    return basic_project


def test_script_pass(valid_project: Path):
    """Execute check_requirements_file.py using subprocess and check exit code is zero."""
    exit_code = subprocess.call(
        ["python", check_requirements_file_path], cwd=valid_project
    )
    assert exit_code == 0


def test_script_help(basic_project: Path):
    """Execute check_requirements_file.py with --help and check exit code is zero.
    The script should also display the help message."""
    result = subprocess.run(
        ["python", check_requirements_file_path, "--help"],
        capture_output=True,
        cwd=basic_project,
    )
    assert result.returncode == 0
    assert "Usage" in result.stdout.decode()


@pytest.mark.parametrize(
    "file_name",
    ["poetry.lock", "requirements.txt"],
)
def test_script_missing_files(valid_project: Path, file_name: str):
    """
    Execute check_requirements_file.py with a missing poetry.lock or requirements file.
    Check there is non-zero exit code and suitable message.
    """
    (valid_project / file_name).unlink()

    result = subprocess.run(
        ["python", check_requirements_file_path], cwd=valid_project, capture_output=True
    )

    assert result.returncode == 1
    assert "File not found" in result.stderr.decode()


def test_script_outdated_requirements(valid_project: Path):
    """
    Execute check_requirements_file.py with lock file modified but requirements.txt not updated.
    Check there is non-zero exit code and suitable message.
    """
    lock_file = valid_project / "poetry.lock"
    lock_file.write_text(lock_file.read_text() + " ")

    result = subprocess.run(
        ["python", check_requirements_file_path], cwd=valid_project, capture_output=True
    )

    assert result.returncode == 1
    assert "requirements.txt is out of date" in result.stderr.decode()
    assert "poetry-auto-export" in result.stderr.decode()
