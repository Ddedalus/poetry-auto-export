from cleo.events.console_events import TERMINATE
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from poetry.console.application import Application
from poetry.console.commands.add import AddCommand
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
            print("Not a container!", type(tools))
            return {}
        config = tools.get("poetry-auto-export", None)
        if config and not isinstance(config, dict):
            raise ValueError(
                "Invalid pyproject.toml at [tool.poetry-auto-export]; must be an object!"
            )
        if config and not isinstance(config.get("output"), str):
            raise ValueError(
                "Invalid pyproject.toml at [tool.poetry-auto-export]; output=str is required."
            )
        return dict(config)

    def prepare_export_args(self):
        """Prepare arguments for the export command."""
        options = []
        if output := self.config.pop("output", None):
            options.append(f" -o {output}")
        if self.config.pop("without_hashes", None):
            options.append("--without-hashes")
        if self.config.pop("with_credentials", None):
            options.append("--with-credentials")
        if groups := self.config.pop("with", []):
            options.append(f"--with {' '.join(groups)}")
        if groups := self.config.pop("without", []):
            options.append(f"--without {' '.join(groups)}")
        if extras := self.config.pop("extras", []):
            options.append(f"--extras {' '.join(extras)}")

        return " ".join(options).strip() or None

    def export(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        if not isinstance(event, ConsoleTerminateEvent):
            return
        if event.exit_code:
            return
        if not isinstance(
            event.command, (LockCommand, UpdateCommand, AddCommand, RemoveCommand)
        ):
            return

        if not self.config:
            return

        out_file = str(self.config["output"])
        args = self.prepare_export_args()
        event.io.output.write_line(f"<fg=blue>Exporting dependencies to</> {out_file}")
        event.command.call("export", args)
