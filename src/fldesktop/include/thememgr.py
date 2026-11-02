from PySide6.QtGui import QPalette, QColor, QIcon, QFont
from PySide6.QtWidgets import QApplication


STYLESHEET = """
              QWidget#surface
              {
                background-color: rgba(0, 0, 0, 200);
              }

              QWidget#panel
              {
                background-color: black;
              }

              QWidget#menu
              {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 13;
              }

              QWidget#dock
              {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 13;
                padding: 1;
              }

              QPushButton#traybtn
              {
                border: 1;
                background-color: rgba(0, 0, 0, 0);
                padding: 5px;
                margin: 0px;
              }

              QPushButton#traybtn::hover
              {
                background-color: rgba(255, 255, 255, 50);
              }

              QPushButton#traybtn::pressed
              {
                background-color: rgba(255, 255, 255, 25);
              }

              QToolButton#flatbtn
              {
                border: 1;
                background-color: rgba(0, 0, 0, 0);
                padding: 0px;
                margin: 0px;
              }

              QToolButton#flatbtn::hover
              {
                background-color: rgba(255, 255, 255, 50);
              }

              QToolButton#flatbtn::pressed
              {
                background-color: rgba(0, 0, 0, 100);
              }

              QPushButton#taskbarbtn
              {
                border: 1;
                background-color: rgba(0, 0, 0, 0);
                padding-left: 7;
                padding-right: 7
              }

              QPushButton#taskbarbtn::hover
              {
                background-color: rgba(255, 255, 255, 50);
                border-radius: 25;
              }

              QPushButton#taskbarbtn::pressed
              {
                border-bottom: 2px solid white;
              }

              QTextEdit
              {
                background-color: transparent
              }

              QTextBrowser
              {
                background-color: transparent
              }

              QLineEdit
              {
                background-color: transparent
              }
"""

FLUORITE_CS = {
    "Window": "#2C333B",
    "WindowText": "#F0F4F9",
    "Base": "#0E1217",
    "AlternateBase": "#1A2027",
    "ToolTipBase": "#2C333B",
    "ToolTipText": "#F0F4F9",
    "PlaceholderText": "#7C8794",
    "Text": "#F0F4F9",
    "Button": "#2C333B",
    "ButtonText": "#F0F4F9",
    "BrightText": "#FFFFFF",
    "Highlight": "#769EDB",
    "HighlightedText": "#0E1217",
    "Light": "#525E6C",
    "Midlight": "#3F4854",
    "Dark": "#0E1217",
    "Mid": "#1A2027",
    "Shadow": "#080A0D",
    "Link": "#BCCDE6",
    "LinkVisited": "#CBBCE6"
}


STD_COLORS = {
    "white": "#F0F4F9",
    "lightwhite": "#FFFFFF",
    "darkwhite": "#D3DDEA",

    "black": "#2C333B",
    "lightblack": "#525E6C",
    "darkblack": "#0E1217",

    "red": "#DB7676",
    "lightred": "#E6BCBC",
    "darkred": "#B63A3A",

    "orange": "#DBA876",
    "lightorange": "#E6D1BC",
    "darkorange": "#B6783A",

    "yellow": "#DBC176",
    "lightyellow": "#E6DCBC",
    "darkyellow": "#B6973A",

    "green": "#76DBA8",
    "lightgreen": "#BCE6D1",
    "darkgreen": "#3AB678",

    "teal": "#76DBD4",
    "lightteal": "#BCE6E3",
    "darkteal": "#3AB6AE",

    "blue": "#769EDB",
    "lightblue": "#BCCDE6",
    "darkblue": "#3A6BB6",

    "indigo": "#767EDB",
    "lightindigo": "#BCC0E6",
    "darkindigo": "#3A44B6",

    "purple": "#9B76DB",
    "lightpurple": "#CBBCE6",
    "darkpurple": "#673AB6",

    "pink": "#DB76A8",
    "lightpink": "#E6BCD1",
    "darkpink": "#B63A78",

    "cyan": "#76B6DB",
    "lightcyan": "#BCD7E6",
    "darkcyan": "#3A88B6"
}


class ThemingManager:
    def __init__(self, comm):

        self.comm = comm

        self.comm.register(
            "thememgr",
            {
                "stdcolors": self.get_stdcolors
            }
        )

        self.setup_theming()

    def setup_theming(self):

        palette = QPalette()

        for i in FLUORITE_CS:
            palette.setColor(getattr(QPalette.ColorRole, i), 
                             QColor(FLUORITE_CS[i]))

        QIcon.setThemeName("breeze-dark")

        QApplication.instance().setPalette(palette)
        QApplication.instance().setStyleSheet(STYLESHEET)
        QApplication.instance().setStyle("oxygen")
        QApplication.instance().setFont(QFont("Noto Sans", 10))

    def get_stdcolors(self):

        colors = STD_COLORS
        colors["fg"] = STD_COLORS["white"]
        colors["bg"] = STD_COLORS["black"]
        colors["accent"] = STD_COLORS["blue"]
        colors["transparent"] = "#00000000"

        return colors
