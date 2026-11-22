from PySide6.QtWidgets import QTabWidget
from fldesktop.include.subsystems.ui.uikit.widgets.base import Widget


class Tabs(Widget):
    def __init__(self, comm, name, attrs):

        self.qwidget = QTabWidget()

        super().__init__(
            comm, name, attrs,
            {
                "Attr.UI.Widget.Tabs.TabsPosition": "top",
                "Attr.UI.Widget.Tabs.TabsClosable": False,
                "Attr.UI.Widget.Tabs.SwitchDisabled": False
            }
        )

        self.type = "tabs"

        self._setup()

    def apply_attrs(self):
        super().apply_attrs()

        match self.attrs["Attr.UI.Widget.Tabs.TabsPosition"]:
            case "top":
                self.qwidget.setTabPosition(QTabWidget.TabPosition.North)
            case "bottom":
                self.qwidget.setTabPosition(QTabWidget.TabPosition.South)
            case "left":
                self.qwidget.setTabPosition(QTabWidget.TabPosition.West)
            case "right":
                self.qwidget.setTabPosition(QTabWidget.TabPosition.East)

        self.qwidget.setTabsClosable(
            bool(self.attrs["Attr.UI.Widget.Tabs.TabsClosable"])
        )

        self.qwidget.tabBar().setDisabled(
            bool(self.attrs["Attr.UI.Widget.Tabs.SwitchDisabled"])
        )

    def add_child(self, widget: Widget):

        if hasattr(widget, "qwidget"):
            title = next(
                (v for k, v in widget.attrs.items() \
                 if k.startswith("Attr.UI.") and k.endswith(".Text")),
                "Tab"
            )
            self.qwidget.addTab(widget.qwidget, title)
        
        return True
