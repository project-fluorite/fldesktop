import os
import sys
sys.path.insert(0, os.getcwd())


from fldesktop.include.subsystem import Subsystem
from fldesktop.include.subsystems.ui.thememgr import STD_COLORS
import json


FALLBACK_CONFIG = {
    "background-type": "singlecolor",
    "background-color": STD_COLORS["black"],
    "wallpaper": "",
    "glass-tint-color": "#151515",
    "glass-tint-alpha": 125,
    "glass-blur-strength": 0.35,
    "language": "en_US",
    "kb_locales": ["us"],
    "auth-type": "passwordless",
    "auth-pwhash": ""
}


class ConfigurationManager(Subsystem):
    def __init__(self):
        super().__init__("cfgmgr")

        self.comm.register(
            "cfgmgr", {
                "get": self.get_value,
                "reload": self.load_config
            }
        )

        self.path = self.comm.request(
            "osmgr", "get_path", "flcfg.json"
        )

        self.load_config()

        #self.debounce = QTimer(interval=500, singleShot=True)
        #self.debounce.timeout.connect(self.on_config_changed)

        #self.watcher = QFileSystemWatcher([self.path])
        #self.watcher.fileChanged.connect(self.debounce.start)

        self.comm.emit("reload_config")

        self.mainloop()
    
    def load_config(self):
        "Load configuration"

        if self.path:
            with open(self.path) as f:
                try:
                    self.config = json.load(f)
                except json.decoder.JSONDecodeError:
                    self.config = FALLBACK_CONFIG
        else:
            self.config = FALLBACK_CONFIG
    
    def get_value(self, key: str):
        "Return value"

        if key in self.config:
            return self.config[key]
        else:
            if key in FALLBACK_CONFIG:
                return FALLBACK_CONFIG[key]
            else:
                return None
    
    def on_config_changed(self):
        "Handle config file changes"

        self.load_config()
        self.comm.emit("reload_config")


if __name__ == "__main__":
    ConfigurationManager()
