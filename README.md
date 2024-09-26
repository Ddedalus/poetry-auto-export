# poetry-auto-export

Automatically export dependencies to requirements.txt on every poetry lock

This plugin enables you to keep a `requirements.txt` file always up to date with your `poetry.lock` file. This is helpful if you want to use `pip` to install your dependencies somewhere, e.g.

- in CI/CD environments
- in docker containers

# Usage

Add plugin configuration to your `pyproject.toml`. The options follow arguments for `poetry export`.

```toml
[tool.poetry-auto-export]
output = "requirements.txt"
without_hashes = true
without = ["dev"]
```

Then, run poetry commands as usual:

```bash
poetry lock
```

The `requirements.txt` file will be updated automatically.

The supported commands are:

- lock
- update
- add
- remove

## Detect lock file changes

Suppose you're working on a project with CI/CD and several contributors. You want the CI/CD to depend on the `requirements.txt` file created by `poetry-auto-export`, but you need to make sure everyone updates the `requirements.txt` file correctly.

To make this easy, `poetry-auto-export` puts a SHA1 hash in a comment on top of `requirements.xtx` file. In CI/CD you can quickly compute the hash and compare that with the comment without installing poetry or any other dependencies.

Here is an example python script that does this:

```python
import hashlib
from pathlib import Path

lock_hash = hashlib.sha1(Path("poetry.lock").read_bytes()).hexdigest()
first_line = Path("requirements.txt").read_text().split("\n")[0]

if first_line != f"# poetry.lock hash: {lock_hash}":
    raise ValueError("requirements.txt is out of date, use the `poetry-auto-export` plugin to update it!")
```

A more fancy version of the above script is shipped with this package as `check_requirements_file.py`.
You can also download it from the Github repository directly, e.g.

```bash
curl -O https://raw.githubusercontent.com/Ddedalus/poetry-auto-export/refs/heads/main/poetry_auto_export/check_requirements_file.py
```

Or pipe straight into python, for a quick one-liner:

```bash
curl -sSL https://raw.githubusercontent.com/Ddedalus/poetry-auto-export/refs/heads/main/poetry_auto_export/check_requirements_file.py | python3 -
```

## Creating multiple export files

If you need to create multiple requirements files, e.g. `dev-requirements.txt` and `prod-requirements.txt`, use the following syntax:

```toml
[[tool.poetry-auto-export.exports]]
output = "dev-requirements.txt"
without = ["prod"]

[[tool.poetry-auto-export.exports]]
output = "prod-requirements.txt"
without = ["dev"]
```

# Installation

This is a poetry plugin, so it's meant to be installed inside the global poetry environment, not your project environment like regular pacakges.
See [poetry's docs](https://python-poetry.org/docs/master/plugins/#using-plugins).

There are three ways of doing so.

## The pipx way

If you are using pipx already, that's easy:

```bash
pipx inject poetry poetry-auto-export
```

## The pip way

Otherwise, you can use the [pip that comes with poetry](https://python-poetry.org/docs/1.6/#installation). The difficulty is finding that pip! It's not the same one you get with `poetry run pip`.
Here is a best effort guess:

On Linux:

```bash
~/.local/share/pypoetry/venv/bin/pip install poetry-auto-export
```

On Windows:

```powershell
%APPDATA%\pypoetry\venv\bin\pip install poetry-auto-export
```

## The poetry way

For some reason, this is [discouraged by poetry](https://python-poetry.org/docs/master/plugins/#the-self-add-command).

```bash
poetry self add poetry-auto-export
```

# Roadmap and contributing

The primary goal of the project is to make it more convenient to work with poetry projects in CI/CD and docker. Contributions towards this goal are welcome!

Roadmap:

- more unit tests for the plugin
- integration tests for the plugin
- proper configuration parsing (note: typed dict and dataclasses can't support the `with` option, since it's a python keyword)
- schema or exhaustive documentation of the supported configuration options
