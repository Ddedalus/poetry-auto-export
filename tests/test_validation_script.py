import subprocess
from pathlib import Path

from poetry_auto_export.plugin import PoetryAutoExport

repo_root = Path(__file__).parent.parent
validation_script_path = (
    repo_root / "poetry_auto_export/validation_script.py"
).absolute()


def test_validation_script_pass(
    basic_project: Path,
    event,
    dispatcher,
    plugin: PoetryAutoExport,
):
    """Execute validation_script.py using subprocess and check exit code is zero."""
    # Given
    # TODO: call the plugin directly instead to save time
    subprocess.run(["poetry", "lock"], cwd=basic_project)

    # When
    exit_code = subprocess.call(["python", validation_script_path], cwd=basic_project)

    # Then
    assert exit_code == 0
