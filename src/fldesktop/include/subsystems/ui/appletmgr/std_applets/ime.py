from fldesktop.include.subsystems.ui.uikit.applet import Applet


class InputMethod(Applet):
    def __init__(self, comm):
        super().__init__(comm, "", {})
