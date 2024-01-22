from cleo.events.console_events import TERMINATE
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.outputs.output import Verbosity
from poetry.console.application import Application
from poetry.console.commands.add import AddCommand
from poetry.console.commands.export import ExportCommand
from poetry.console.commands.lock import LockCommand
from poetry.console.commands.remove import RemoveCommand
from poetry.console.commands.update import UpdateCommand
from poetry.plugins.application_plugin import ApplicationPlugin
from tomlkit.container import Container
from tomlkit.items import Table


class PoetryAutoExport(ApplicationPlugin):
    def activate(self, application: Application):
        self.config = self.parse_pyproject(application.poetry.pyproject.data)
        if not application.event_dispatcher:
            return
        application.event_dispatcher.add_listener(TERMINATE, self.export)
        return super().activate(application)

    def parse_pyproject(self, pyproject: Container):
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

    def prepare_export_args(self):
        """Prepare arguments for the export command."""
        if not self.config:
            return None

        options = []
        if output := self.config.pop("output", None):
            options.append(f" -o {output!r}")
        if format := self.config.pop("format", None):
            options.append(f"--format {format}")

        if self.config.pop("without_hashes", None):
            options.append("--without-hashes")
        if self.config.pop("with_credentials", None):
            options.append("--with-credentials")
        if self.config.pop("without_urls", None):
            options.append("--without-urls")
        if self.config.pop("all_extras", None):
            options.append("--all-extras")

        if groups := self.config.pop("with", []):
            for group in groups:
                options.append(f"--with={group!r}")
        if groups := self.config.pop("without", []):
            for group in groups:
                options.append(f"--without={group!r}")
        if extras := self.config.pop("extras", []):
            for extra in extras:
                options.append(f"--extras={extra!r}")
        return " ".join(options).strip() or None

    def export(self, event: Event, event_name: str, dispatcher: EventDispatcher):
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

        if not self.config:
            event.io.write_line(
                "Skipping requirements export as no configuration was found.",
                Verbosity.VERY_VERBOSE,
            )
            return

        out_file = str(self.config["output"])
        args = self.prepare_export_args()

        event.io.write_line(f"<fg=blue>Exporting dependencies to</> {out_file}")
        command_message = f"> <fg=dark_gray>poetry export {args}</>"
        event.io.write_line(command_message, Verbosity.VERBOSE)

        event.command.call("export", args)
