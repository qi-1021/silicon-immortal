"""应用入口。"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .ui import theme as T
from .ui.main_window import MainWindow
from .version import GAME_VERSION


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
    app = QApplication(sys.argv)
    app.setApplicationName("Silicon Immortal")
    app.setApplicationDisplayName("硅仙人")
    app.setApplicationVersion(GAME_VERSION)
    app.setStyle("Fusion")
    app.setFont(QFont(T.FONT_UI, 13))
    app.setStyleSheet(T.QSS)
    win = MainWindow()
    if '--smoke-test' in sys.argv:
        from .smoke import run
        index=sys.argv.index('--smoke-test')
        run(app,win,sys.argv[index+1]);return
    if len(sys.argv)>1:
        from pathlib import Path
        if Path(sys.argv[1]).is_file():win.import_soc(sys.argv[1])
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
