from cleo.io.io import IO
from poetry.plugins import Plugin
from poetry.poetry import Poetry


class PoetryAutoExport(Plugin):
    def activate(self, poetry: Poetry, io: IO) -> None:
        io.output.write_line("Poetry Auto Export Activated")
        return super().activate(poetry, io)
