from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton

from fldesktop.include.subsystems.ui.uikit.applet import Applet


class Power(Applet):
    def __init__(self, comm):
        super().__init__(
            comm, "", {
                "Attr.UI.Applet.ButtonIcon": comm.request(
                    "iconmgr", "get_src", "system-shutdown"
                )
            }
        )

        self.container = QWidget()
        self.container.setFixedSize(150, 50)
        self.layout = QHBoxLayout(self.container)
        self.qlayout.addWidget(self.container)

        self.qlayout.setContentsMargins(5, 5, 5, 5)
        self.layout.setContentsMargins(0, 0, 0, 0)

        for i in (
            ("Lock", "system-lock", 
             lambda: self.comm.request("lockscreen", "show")),
            ("Sleep", "system-suspend",
             lambda: self.comm.request("osmgr", "suspend")),
            ("Shutdown", "system-shutdown",
             lambda: self.comm.request("uimain", "shutdown")),
            ("Reboot", "system-reboot",
             lambda: self.comm.request("uimain", "reboot"))
        ):
            btn = QToolButton()
            btn.setIcon(self.comm.request("iconmgr", "get", i[1]))
            btn.setToolTip(i[0])
            btn.setFixedSize(32, 32)
            self.layout.addWidget(btn)
            btn.clicked.connect(i[2])

        self.widget.setFixedSize(
            self.container.width() + 5, self.container.height() + 5
        )
        self.menu.sync_size()
