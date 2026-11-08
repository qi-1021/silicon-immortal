"""保持纵横比的图像检查器：滚轮缩放、拖动、双击复位。"""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy

from . import theme as T


class ImageView(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setMinimumSize(280, 260)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("芯片图像：滚轮缩放，拖动平移，双击或按 0 复位")
        self.zoom = 1.0
        self.pan = QPointF()
        self._drag = None

    def reset_view(self):
        self.zoom = 1.0
        self.pan = QPointF()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(T.BG2))
        px = self.pixmap()
        if px and not px.isNull():
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            factor = min(self.width() / px.width(), self.height() / px.height()) * self.zoom
            w, h = px.width() * factor, px.height() * factor
            rect = QRectF((self.width() - w) / 2 + self.pan.x(), (self.height() - h) / 2 + self.pan.y(), w, h)
            p.drawPixmap(rect, px, QRectF(px.rect()))
        if self.hasFocus():
            p.setPen(QColor(T.CYAN_DIM))
            p.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def wheelEvent(self, event):
        old = self.zoom
        self.zoom = max(1.0, min(8.0, old * (1.15 if event.angleDelta().y() > 0 else 1 / 1.15)))
        # 保持鼠标指向的图像坐标不变。
        anchor = event.position() - QPointF(self.width() / 2, self.height() / 2)
        self.pan = anchor - (anchor - self.pan) * (self.zoom / old)
        if self.zoom == 1.0:
            self.pan = QPointF()
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            self.pan += event.position() - self._drag
            self._drag = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        self._drag = None
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.reset_view()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_0, Qt.Key.Key_Home):
            self.reset_view()
        elif event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_Minus):
            self.zoom = max(1.0, min(8.0, self.zoom * (1 / 1.15 if event.key() == Qt.Key.Key_Minus else 1.15)))
            self.update()
        else:
            super().keyPressEvent(event)
