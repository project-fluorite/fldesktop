from PySide6.QtWidgets import QLineEdit
from fldesktop.include.uikit.widgets.base import Widget


class Entry(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QLineEdit()

        super().__init__(comm, name, attrs)

        self.type = "entry"
        
        self.callables = {
            "get_text": self.get_text,
            "set_text": self.set_text,
            "enable": lambda _: self.qwidget.setEnabled(True),
            "disable": lambda _: self.qwidget.setEnabled(False)
        }

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

    def get_text(self) -> str:
        return self.qwidget.text()

    def set_text(self, text: str) -> None:
        self.qwidget.setText(str(text))