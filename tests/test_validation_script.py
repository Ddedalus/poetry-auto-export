import subprocess
from pathlib import Path

import pytest

from poetry_auto_export.plugin import PoetryAutoExport

repo_root = Path(__file__).parent.parent
validation_script_path = (
    repo_root / "poetry_auto_export/validation_script.py"
).absolute()


@pytest.fixture
def valid_project(
    basic_project: Path,
    event,
    dispatcher,
    plugin: PoetryAutoExport,
) -> Path:
    """A poetry project with up-to-date generated requirements.txt file."""
    # TODO: call the plugin directly instead to save time
    subprocess.run(["poetry", "lock"], cwd=basic_project)
    return basic_project


def test_validation_script_pass(valid_project: Path):
    """Execute validation_script.py using subprocess and check exit code is zero."""
    exit_code = subprocess.call(["python", validation_script_path], cwd=valid_project)
    assert exit_code == 0


def test_validation_script_help(basic_project: Path):
    """Execute validation_script.py with --help and check exit code is zero.
    The script should also display the help message."""
    result = subprocess.run(
        ["python", validation_script_path, "--help"],
        capture_output=True,
        cwd=basic_project,
    )
    assert result.returncode == 0
    assert "Usage" in result.stdout.decode()


@pytest.mark.parametrize(
    "file_name",
    ["poetry.lock", "requirements.txt"],
)
def test_validation_script_missing_files(valid_project: Path, file_name: str):
    """
    Execute validation_script.py with a missing poetry.lock or requirements file.
    Check there is non-zero exit code and suitable message.
    """
    (valid_project / file_name).unlink()

    result = subprocess.run(
        ["python", validation_script_path], cwd=valid_project, capture_output=True
    )

    assert result.returncode == 1
    assert "File not found" in result.stderr.decode()
