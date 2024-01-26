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
