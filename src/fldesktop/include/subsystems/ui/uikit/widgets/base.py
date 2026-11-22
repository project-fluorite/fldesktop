from PySide6.QtCore import Qt

from fldesktop.include.subsystems.ui.uikit.ui import UI

import logging
import locale


BASEATTRS = {
    "Attr.UI.Widget.Width": -1,
    "Attr.UI.Widget.Height": -1,
    "Attr.UI.Widget.DragEnabled": False,
    "Attr.UI.Widget.DragData": "",
    "Attr.UI.Widget.DragMimeType": "",
    "Attr.UI.Widget.DropEnabled": False,
    "Attr.UI.Widget.DropMimeTypes": [],
    "Attr.UI.Widget.TransparentBackground": False
}


class Widget(UI):
    def __init__(self, comm, name, attrs={}, baseattrs={}):
        baseattrs.update(BASEATTRS)
        super().__init__(comm, name, attrs, baseattrs)
        self.type = "widget"

        self.callables = {}

    def _setup(self):
        
        if hasattr(self, "qwidget"):
            if hasattr(self.qwidget, "show") and hasattr(self.qwidget, "hide"):
                self.callables.update(
                    {
                        "show": self.qwidget.show,
                        "hide": self.qwidget.hide
                    }
                )
            if hasattr(self.qwidget, "enable") and \
                hasattr(self.qwidget, "disable"):
                self.callables.update(
                    {
                        "enable": self.qwidget.enable,
                        "disable": self.qwidget.disable
                    }
                )
                
            self.baseattrs.update(
                
            )

            self.qwidget.setProperty(
                "drop_callback", lambda data, mime: self.event(
                    type="data_dropped",
                    data=data, mimetype=mime
                )
            )

        self.attrs = {**self.baseattrs, **self.attrs}

        self.apply_attrs()

        #self.qwidget.installEventFilter(self._runner.drag_filter)
        #self.qwidget.installEventFilter(self._runner.drop_filter)

    def _setup_setters(self):
        for prop in self.baseattrs:

            def make_setter(name):
                def setter(**kwargs):
                    if name in kwargs:
                        self.attrs[name] = kwargs[name]
                        logging.debug(
                            f"Setting {name}={kwargs[name]} to {self.name}"
                        )
                        self.apply_attrs()

                return setter

            setter = make_setter(prop)
            setattr(self, f"set_{prop}", setter)
            self.callables[f"set_{prop}"] = setter

    def apply_attrs(self):
        super().apply_attrs()

        if hasattr(self, "qwidget"):
            if self.attrs["Attr.UI.Widget.Width"] >= 0:
                self.qwidget.setFixedWidth(
                    int(self.attrs["Attr.UI.Widget.Width"]))
            if self.attrs["Attr.UI.Widget.Height"] >= 0:
                self.qwidget.setFixedHeight(
                    int(self.attrs["Attr.UI.Widget.Height"]))

            return

            if self.attrs["drag_enabled"]:
                self.qwidget.setProperty(
                    "drag_enabled", bool(self.attrs["drag_enabled"])
                )
            if self.attrs["drag_data"]:
                self.qwidget.setProperty("drag_data", self.attrs["drag_data"])
            if self.attrs["drag_mime_type"]:
                self.qwidget.setProperty(
                    "drag_mime_type", self.attrs["drag_mime_type"]
                )

            if self.attrs["drop_enabled"]:
                self.qwidget.setAcceptDrops(bool(self.attrs["drop_enabled"]))
                self.qwidget.setProperty(
                    "drop_enabled", bool(self.attrs["drop_enabled"])
                )
            if self.attrs["drop_mime_types"]:
                self.qwidget.setProperty(
                    "drop_mime_types", self.attrs["drop_mime_types"]
                )

            self.qwidget.setStyleSheet(
                "background-color: transparent"
                if self.attrs["Attr.UI.Widget.TransparentBackground"]
                else ""
            )

    def delete(self):
        logging.debug(f"Deleting {self.type} {self.name}")

        if hasattr(self, "_cleanup"):
            self._cleanup()

        if hasattr(self, "qwidget"):
            self.qwidget.setParent(None)
            self.qwidget.deleteLater()
        if hasattr(self, "qlayout"):
            self.qlayout.deleteLater()
        if hasattr(self, "qaction"):
            self.qaction.deleteLater()

    def tr(self, base_text: str):
        "Translate text"
        loc = locale.getlocale()[0]

        return base_text

        if loc in self._runner.translations:
            trs = self._runner.translations[loc]
            if base_text in trs:
                return trs[base_text]

        return base_text


    def reparent(self, parent):

        logging.debug(f"Reparenting {self} to {parent}")

        self.parent = parent

        if hasattr(parent, "add_child"):
            if parent.add_child(self): # Schould return True on success
                return

        if hasattr(parent, "qlayout"):
            if hasattr(self, "qlayout"):
                parent.qlayout.addLayout(self.qlayout)
                logging.debug(f"Added {self}'s layout to {parent}'s one")
            elif hasattr(self, "qwidget"):
                parent.qlayout.addWidget(self.qwidget)
                logging.debug(f"Added {self}'s widget to {parent}'s layout")

        elif hasattr(parent, "qwidget"):
            if hasattr(self, "qlayout"):
                parent.qwidget.setLayout(self.qlayout)
                logging.debug(f"Added {parent}'s layout is now {self}")

        
