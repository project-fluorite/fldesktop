import os
import sys
sys.path.insert(0, os.getcwd())


from fldesktop.include.subsystem import Subsystem
from fldesktop.include.subsystems.ui import (
    localemgr, input, desktop, superfx,
    uikit, background, iconmgr, thememgr, wm,
    startupscreen, lockscreen, panel, dialogs,
    appletmgr, systemsounds, search, fade_effect,
    appserver
)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

import logging


SERVICES = {
    "localemgr": localemgr.LocaleManager,
    "inputmgr": input.InputManager,
    "desktop": desktop.Desktop,
    "superfx": superfx.SuperFX,
    "uikit": uikit.UIKit,
    "background": background.Background,
    "iconmgr": iconmgr.IconManager,
    "thememgr": thememgr.ThemingManager,
    "wm": wm.WindowManager,
    "startupscreen": startupscreen.StartupScreenManager,
    "lockscreen": lockscreen.LockScreen,
    "panel": panel.Panel,
    "dialogmgr": dialogs.DialogManager,
    "appletmgr": appletmgr.AppletManager,
    "systemsounds": systemsounds.SystemSounds,
    "search": search.Search,
    "fadeeffect": fade_effect.FadeEffect,
    "appserver": appserver.AppServer
}


class UI(Subsystem):
    def __init__(self):
        super().__init__("ui")

        logging.info("Hello there!")

        self.init.set_services(SERVICES)

        self.app = QApplication()

        self.timer = QTimer(interval=50)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

        self.comm.register(
            "uimain", {
                "shutdown": self.shutdown,
                "reboot": self.reboot
            }
        )

        self.app.exec()

    def shutdown(self):
        self.comm.request("ssmgr", "show_shutdown")
        self.comm.request("lifecycle", "shutdown")

    def reboot(self):
        self.comm.request("ssmgr", "show_shutdown", True)


if __name__ == "__main__":
    UI()
