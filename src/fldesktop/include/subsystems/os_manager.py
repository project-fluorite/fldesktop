import os
import sys
sys.path.insert(0, os.getcwd())


from fldesktop.include.subsystem import Subsystem


class OSManager(Subsystem):
    def __init__(self):
        super().__init__("osmgr")

        self.comm.register(
            "osmgr", {
                "get_path": self.get_path
            }
        )

        self.mainloop()
    
    def get_path(self, postfix) -> str | None:
        "Get data path (useful for testing)"

        prefixes = [
            "/usr/lib/python3/dist-packages/fldesktop/",
            "/",
            "/home/",
            "~/",
            "./",
            "../",
            "/tmp/"
        ] # ^^^^^ Prefixes are sorted like this for security reasons

        for p in prefixes:
            path = p + postfix
            if os.path.exists(path):
                return path
            
        return None


if __name__ == "__main__":
    OSManager()
