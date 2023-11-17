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
