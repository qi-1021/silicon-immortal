"""本地SVG品牌标志，不依赖网络或位图生成。"""
from pathlib import Path
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QIcon,QPainter,QPixmap
from PySide6.QtSvg import QSvgRenderer

from ..paths import resource_root
LOGO=resource_root()/'assets/logo.svg'


def logo_pixmap(size=128):
    pixmap=QPixmap(size,size);pixmap.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pixmap);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(str(LOGO)).render(painter,QRectF(0,0,size,size));painter.end();return pixmap


def app_icon():return QIcon(logo_pixmap(256))
