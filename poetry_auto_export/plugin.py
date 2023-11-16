from cleo.commands.command import Command
from cleo.events.console_command_event import ConsoleCommandEvent
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


class PoetryAutoExport(ApplicationPlugin):
    def activate(self, application: Application):
        if not application.event_dispatcher:
            return
        application.event_dispatcher.add_listener(TERMINATE, self.export)
        return super().activate(application)

    def export(self, event: Event, event_name: str, dispatcher: EventDispatcher):
        if not isinstance(event, ConsoleTerminateEvent):
            return
        if event.exit_code:
            return
        if not isinstance(
            event.command, (LockCommand, UpdateCommand, AddCommand, RemoveCommand)
        ):
            return

        event.io.output.write_line("Poetry Auto Export Activated")
        event.command.call("export", "-o requirements.txt --without-hashes")
