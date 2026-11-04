from PySide6.QtWidgets import QWidget
from fldesktop.include.uikit.widgets.base import Widget


class Widget(Widget):
    def __init__(self, comm, name, attrs):
        self.qwidget = QWidget()
        super().__init__(comm, name, attrs)
        self.type = "widget"

        self._setup()
