from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

from pathlib import Path
import logging


class SystemSounds:
    def __init__(self, comm):

        self.comm = comm
        self.comm.register(
            "syssounds", {
                "play": self.play
            }
        )

        self.load_sounds()

    def play(self, name: str):

        if name in self.sounds:
            self.sounds[name].play()

    def load_sounds(self):

        self.sounds = {}

        path = Path(__file__).resolve().parent / "assets" / "sounds"

        for i in path.iterdir():
            if i.suffix == ".wav":
                sound = QSoundEffect()
                sound.setSource(QUrl.fromLocalFile(str(i)))
                sound.setLoopCount(1)
                self.sounds[i.stem] = sound