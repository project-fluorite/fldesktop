from fldesktop.include.subsystems.ui.widgets.terminal \
    import Terminal as TerminalWidget
from fldesktop.include.subsystems.ui.uikit.widgets.base import Widget


class Terminal(Widget):
    def __init__(self, comm, name, attrs):
        self.qwidget = TerminalWidget()
        super().__init__(comm, name, attrs)
        self.type = "terminal"

        self._setup()
