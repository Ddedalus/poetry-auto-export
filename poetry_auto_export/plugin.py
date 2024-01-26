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
from tomlkit.items import Table

Export = dict


class PoetryAutoExport(ApplicationPlugin):
    def activate(self, application: Application):
        self.configs: list[Export] = []
        basic_export = self._parse_pyproject(application.poetry.pyproject.data)
        if basic_export:
            self.configs.append(basic_export)
        if not application.event_dispatcher:
            return
        application.event_dispatcher.add_listener(TERMINATE, self.run_exports)
        return super().activate(application)

    def _parse_pyproject(self, pyproject: Container):
        tools = pyproject["tool"]
        if not isinstance(tools, Table):
            return None
        config = tools.get("poetry-auto-export", None)
        if config and not isinstance(config, dict):
            raise ValueError(
                "Invalid pyproject.toml at [tool.poetry-auto-export]; must be an object!"
            )
        if config and not isinstance(config.get("output"), str):
            raise ValueError(
                "Invalid pyproject.toml at [tool.poetry-auto-export]; output=str is required."
            )
        if not config:
            return None
        return dict(config)

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

        if groups := export.pop("with", []):
            for group in groups:
                options.append(f"--with={group!r}")
        if groups := export.pop("without", []):
            for group in groups:
                options.append(f"--without={group!r}")
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
                Verbosity.VERY_VERBOSE,
            )
            return

        if not self.configs:
            event.io.write_line(
                "Skipping requirements export as no configuration was found.",
                Verbosity.VERY_VERBOSE,
            )
            return

        for export in self.configs:
            self._run_export(event, export)

    def _run_export(self, event, export):
        out_file = str(export["output"])
        args = self._prepare_export_args(export, event.io.output)

        event.io.write_line(f"<fg=blue>Exporting dependencies to</> {out_file}")
        command_message = f"> <fg=dark_gray>poetry export {args}</>"
        event.io.write_line(command_message, Verbosity.VERBOSE)

        event.command.call("export", args)
