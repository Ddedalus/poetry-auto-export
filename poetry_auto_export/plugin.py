import hashlib
from pathlib import Path

from cleo.events.console_events import TERMINATE
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.outputs.output import Output, Verbosity
from poetry.console.application import Application
from poetry.console.commands.add import AddCommand
from poetry.console.commands.export import ExportCommand
from poetry.console.commands.lock import LockCommand
from poetry.console.commands.remove import RemoveCommand
from poetry.console.commands.update import UpdateCommand
from poetry.plugins.application_plugin import ApplicationPlugin
from tomlkit.container import Container

Export = dict


class PoetryAutoExport(ApplicationPlugin):
    def activate(self, application: Application):
        if not application.event_dispatcher:
            return
        try:
            application.poetry
        except RuntimeError:
            return
        self.configs = self._parse_pyproject(application.poetry.pyproject.data)
        self.application = application

        application.event_dispatcher.add_listener(TERMINATE, self.run_exports)
        return super().activate(application)

    def _parse_pyproject(self, pyproject: Container) -> list[Export]:
        """Parse the pyproject.toml file for export configuration(s)."""
        configs: list[Export] = []
        tools = pyproject["tool"]
        if not isinstance(tools, dict):
            return configs
        full_config = tools.get("poetry-auto-export", None)
        if not full_config:
            return configs
        if not isinstance(full_config, dict):
            raise ValueError(
                "pyproject.toml: [tool.poetry-auto-export] must be an object!"
            )
        exports_list = full_config.pop("exports", None)
        if exports_list and not isinstance(exports_list, list):
            raise ValueError(
                "pyproject.toml: [tool.poetry-auto-export.exports]; must be a list!"
            )
        elif exports_list:
            for export in exports_list:
                if config := self._parse_pyproject_section(export):
                    configs.append(config)

        if top_config := self._parse_pyproject_section(full_config):
            configs.insert(0, top_config)

        return configs

    def _parse_pyproject_section(self, config: dict) -> Export | None:
        """Parse an individual export section. This can be top-level or and element of the `exports` list."""
        if config and not isinstance(config.get("output"), str):
            raise ValueError(
                "Invalid pyproject.toml at [tool.poetry-auto-export]; output=str is required."
            )
        config.pop("exports", None)
        if not config:
            return None
        return Export(config)

    def _prepare_export_args(self, export: Export, output: Output):
        """Prepare arguments for the export command."""
        options = []
        if output := export.pop("output", None):
            options.append(f" -o {output!r}")
        if format := export.pop("format", None):
            options.append(f"--format {format}")

        if export.pop("without_hashes", None):
            options.append("--without-hashes")
        if export.pop("with_credentials", None):
            options.append("--with-credentials")
        if export.pop("without_urls", None):
            options.append("--without-urls")
        if export.pop("all_extras", None):
            options.append("--all-extras")
        if export.pop("only_root", None):
            options.append("--only-root")

        if groups := export.pop("with", []):
            for group in groups:
                options.append(f"--with={group!r}")
        if groups := export.pop("without", []):
            for group in groups:
                options.append(f"--without={group!r}")
        if groups := export.pop("only", []):
            for group in groups:
                options.append(f"--only={group!r}")
        if extras := export.pop("extras", []):
            for extra in extras:
                options.append(f"--extras={extra!r}")
        if export:
            output.write_line(f"<fg=red>Unknown export options:</> {export}")
        return " ".join(options).strip()

    def run_exports(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        if not isinstance(event, ConsoleTerminateEvent):
            return
        if event.exit_code:
            return
        if isinstance(event.command, ExportCommand):
            return
        if not isinstance(
            event.command, (LockCommand, UpdateCommand, AddCommand, RemoveCommand)
        ):
            event.io.write_line(
                "Skipping requirements export as command is not modifying lock file.",
                Verbosity.VERY_VERBOSE,  # type: ignore
            )
            return

        if not self.configs:
            event.io.write_line(
                "Skipping requirements export as no configuration was found.",
                Verbosity.VERY_VERBOSE,  # type: ignore
            )
            return
        lock_hash = self._compute_poetry_lock_hash()
        if not lock_hash:
            event.io.write_line(
                "Could not find poetry.lock file, so hash will be missing.",
                Verbosity.NORMAL,  # type: ignore
            )
        for export in self.configs:
            self._run_export(event, export, lock_hash)

    def _run_export(
        self, event: ConsoleTerminateEvent, export: dict, lock_hash: str | None
    ):
        out_file = Path(export["output"])
        args = self._prepare_export_args(export, event.io.output)

        event.io.write_line(f"<fg=blue>Exporting dependencies to</> {out_file}")
        command_message = f"> <fg=dark_gray>poetry export {args}</>"
        event.io.write_line(
            command_message,
            Verbosity.VERBOSE,  # type: ignore
        )

        event.command.call("export", args)
        if lock_hash:
            self._prepend_lock_hash(out_file, lock_hash)

    def _prepend_lock_hash(self, out_file: Path, lock_hash: str | None):
        with open(out_file, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            if lock_hash:
                f.write(f"# poetry.lock hash: {lock_hash}\n")
            else:
                f.write("# <missing poetry.lock file>\n")
            f.write(
                "# This file is generated by poetry-auto-export\n"
                "# The SHA1 hash of the poetry.lock file is printed above\n"
            )
            f.write(content)

    def _compute_poetry_lock_hash(self) -> str | None:
        """Compute a SHA1 hash of the poetry.lock file."""
        try:
            lock_file = self.application.poetry.locker.lock
        except (RuntimeError, AttributeError):
            return None
        if not lock_file.exists():
            return None
        with lock_file.open("rb") as f:
            return hashlib.sha1(f.read()).hexdigest()
