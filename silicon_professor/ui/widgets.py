"""可复用控件：卡片、分段选择、滑杆、条形图、仪表、缩略 die 图。"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                               QLayout, QSlider, QVBoxLayout, QWidget)

from . import theme as T


class Card(QFrame):
    def __init__(self, title: str | None = None, subtitle: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.body = QVBoxLayout(self)
        self.body.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.body.setContentsMargins(16, 14, 16, 14)
        self.body.setSpacing(10)
        if title:
            row = QHBoxLayout()
            row.setSpacing(8)
            lab = QLabel(title)
            lab.setObjectName("H3")
            row.addWidget(lab)
            row.addStretch(1)
            if subtitle:
                sub = QLabel(subtitle)
                sub.setObjectName("Muted")
                sub.setWordWrap(True)
                row.addWidget(sub, 1)
            self.body.addLayout(row)

    def add(self, w):
        self.body.addWidget(w)
        return w

    def add_layout(self, l):
        self.body.addLayout(l)
        return l


class Pill(QLabel):
    def __init__(self, text: str, color: str = T.TEXT2, parent=None):
        super().__init__(text, parent)
        self.setObjectName("Pill")
        self.setStyleSheet(f"color:{color}; border-color:{T.rgba(color, 0.27)}; background:{T.rgba(color, 0.08)};")


def label(text: str, obj: str = "Dim", size: int | None = None) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName(obj)
    if size:
        lab.setStyleSheet(f"font-size:{size}px;")
    return lab


class ElidedLabel(QLabel):
    """长名称保持布局宽度稳定，完整文本可通过工具提示查看。"""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._full_text = text
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(40)
        self.setText(text)

    def setText(self, text):
        self._full_text = text
        self.setToolTip(text)
        self._elide()

    def _elide(self):
        text = self.fontMetrics().elidedText(self._full_text, Qt.TextElideMode.ElideRight, max(10, self.width() - 12))
        super().setText(text)

    def resizeEvent(self, event):
        self._elide()
        super().resizeEvent(event)


class Stat(QWidget):
    def __init__(self, title: str, value: str = "—", sub: str = "", accent: str = T.CYAN, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setMinimumHeight(72)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(1)
        self.t = QLabel(title)
        self.t.setStyleSheet(f"color:{T.TEXT2}; font-size:11px;")
        self.v = QLabel(value)
        self.v.setMinimumHeight(26)
        self.v.setStyleSheet(f"color:{accent}; font-size:20px; font-weight:700; font-family:{T.FONT_MONO};")
        self.s = QLabel(sub)
        self.s.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        lay.addWidget(self.t)
        lay.addWidget(self.v)
        lay.addWidget(self.s)
        self.setObjectName("Stat")
        self.setStyleSheet(f"QWidget#Stat {{ background:{T.BG2}; border:1px solid {T.BORDER}; border-radius:8px; }}")

    def set(self, value: str, sub: str | None = None, accent: str | None = None):
        self.v.setText(value)
        if sub is not None:
            self.s.setText(sub)
        if accent:
            self.accent = accent
        self.v.setMinimumHeight(26)
        self.v.setStyleSheet(f"color:{self.accent}; font-size:20px; font-weight:700; font-family:{T.FONT_MONO};")


class SectionTitle(QWidget):
    def __init__(self, idx: str, title: str, desc: str = "", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 2)
        lay.setSpacing(10)
        n = QLabel(idx)
        n.setFixedSize(26, 26)
        n.setAlignment(Qt.AlignmentFlag.AlignCenter)
        n.setStyleSheet(f"background:{T.PANEL2}; color:{T.DIM}; border:1px solid {T.BORDER}; border-radius:5px; font-size:11px; font-weight:600;")
        lay.addWidget(n, 0, Qt.AlignmentFlag.AlignTop)
        box = QVBoxLayout()
        box.setSpacing(1)
        t = QLabel(title)
        t.setObjectName("H3")
        box.addWidget(t)
        if desc:
            d = QLabel(desc)
            d.setObjectName("Muted")
            d.setWordWrap(True)
            box.addWidget(d)
        lay.addLayout(box, 1)


class Segmented(QWidget):
    changed = Signal(str)

    def __init__(self, options: list[tuple[str, str]], value: str | None = None, parent=None):
        super().__init__(parent)
        self.options = options
        self.value = value or (options[0][0] if options else "")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.buttons: dict[str, QPushButton] = {}
        for key, text in options:
            b = QPushButton(text)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet("padding:5px 10px; font-size:12px;")
            b.clicked.connect(lambda _, k=key: self.select(k))
            lay.addWidget(b)
            self.buttons[key] = b
        lay.addStretch(1)
        self.refresh()

    def select(self, key: str):
        if key == self.value:
            return
        self.value = key
        self.refresh()
        self.changed.emit(key)

    def refresh(self):
        for k, b in self.buttons.items():
            b.setChecked(k == self.value)


class SliderRow(QWidget):
    changed = Signal(float)

    def __init__(self, title: str, lo: float, hi: float, value: float,
                 fmt: str = "{:.2f}", hint: str = "", parent=None):
        super().__init__(parent)
        self.fmt = fmt
        self.lo, self.hi = lo, hi
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(3)
        top = QHBoxLayout()
        self.title = QLabel(title)
        self.title.setMinimumHeight(16)
        self.title.setStyleSheet(f"color:{T.TEXT2}; font-size:12px;")
        self.val = QLabel(fmt.format(value))
        self.val.setMinimumHeight(16)
        self.val.setStyleSheet(f"color:{T.CYAN}; font-size:12px; font-family:{T.FONT_MONO};")
        top.addWidget(self.title)
        top.addStretch(1)
        top.addWidget(self.val)
        lay.addLayout(top)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setValue(int((value - lo) / max(1e-6, hi - lo) * 1000))
        self.slider.setMinimumHeight(22)
        self.slider.setAccessibleName(title)
        self.slider.valueChanged.connect(self._on)
        lay.addWidget(self.slider)
        if hint:
            h = QLabel(hint)
            h.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
            h.setWordWrap(True)
            lay.addWidget(h)
        self._value = value

    def _on(self, v: int):
        self._value = self.lo + (self.hi - self.lo) * v / 1000.0
        self.val.setText(self.fmt.format(self._value))
        self.changed.emit(self._value)

    def value(self) -> float:
        return self._value

    def set_value(self, v: float):
        self._value = v
        self.slider.blockSignals(True)
        self.slider.setValue(int((v - self.lo) / max(1e-6, self.hi - self.lo) * 1000))
        self.slider.blockSignals(False)
        self.val.setText(self.fmt.format(v))


class BarRow(QWidget):
    def __init__(self, title: str, value: float, target: float, vmax: float,
                 unit: str = "", color: str = T.CYAN, parent=None, fmt: str = "{:.0f}"):
        super().__init__(parent)
        self.title, self.value, self.target, self.vmax, self.unit, self.color = title, value, target, vmax, unit, color
        self.fmt = fmt
        self.setMinimumHeight(42)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_values(self, value: float, target: float | None = None, vmax: float | None = None):
        self.value = value
        if target is not None:
            self.target = target
        if vmax is not None:
            self.vmax = vmax
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        p.setFont(T.font(11))
        p.setPen(T.color(T.TEXT2))
        p.drawText(QRectF(0, 0, w * 0.55, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)
        txt = f"{self.fmt.format(self.value)}{self.unit}"
        p.setFont(T.font(11, 600, mono=True))
        p.setPen(T.color(self.color))
        p.drawText(QRectF(w * 0.55, 0, w * 0.45, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, txt)
        y = 24
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(T.color(T.BORDER))
        p.drawRoundedRect(QRectF(0, y, w, 6), 3, 3)
        frac = max(0.0, min(1.0, self.value / max(1e-6, self.vmax)))
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0, T.color(self.color, 180))
        grad.setColorAt(1, T.color(self.color))
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(0, y, max(4, w * frac), 6), 3, 3)
        if self.target > 0:
            tx = max(0, min(w - 1, w * self.target / max(1e-6, self.vmax)))
            p.setPen(QPen(T.color(T.TEXT2, 160), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(tx, y - 3), QPointF(tx, y + 9))


class Gauge(QWidget):
    def __init__(self, value: float = 0.0, label: str = "", color: str = T.CYAN, parent=None):
        super().__init__(parent)
        self.value = value
        self.label = label
        self.color = color
        self.setMinimumSize(150, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_value(self, v: float, label: str | None = None):
        self.value = max(0, min(1, v))
        if label is not None:
            self.label = label
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = min(self.width(), self.height() * 1.45)
        rect = QRectF((self.width() - s) / 2 + 8, 10, s - 16, s - 16)
        p.setPen(QPen(T.color(T.BORDER), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, 225 * 16, -270 * 16)
        p.setPen(QPen(T.color(self.color), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(rect, 225 * 16, int(-270 * 16 * self.value))
        p.setPen(T.color(T.TEXT))
        p.setFont(T.font(22, 700, mono=True))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.value*100:.0f}%")
        p.setFont(T.font(10))
        p.setPen(T.color(T.TEXT2))
        p.drawText(QRectF(0, rect.bottom() - 8, self.width(), 18), Qt.AlignmentFlag.AlignHCenter, self.label)


class MiniChart(QWidget):
    """带填充的折线图。points 为 0..1 列表。"""
    def __init__(self, points: list[float] | None = None, color: str = T.CYAN, parent=None):
        super().__init__(parent)
        self.points = points or []
        self.color = color
        self.setMinimumHeight(90)

    def set_points(self, pts: list[float], color: str | None = None):
        self.points = pts
        if color:
            self.color = color
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(T.color(T.BORDER), 1))
        for i in range(4):
            y = 6 + (h - 18) * i / 3
            p.drawLine(QPointF(4, y), QPointF(w - 4, y))
        if not self.points:
            return
        n = len(self.points)
        path = QPainterPath()
        for i, v in enumerate(self.points):
            x = 4 + (w - 8) * i / max(1, n - 1)
            y = h - 10 - (h - 18) * max(0, min(1, v))
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        fill = QPainterPath(path)
        fill.lineTo(w - 4, h - 6)
        fill.lineTo(4, h - 6)
        fill.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, T.color(self.color, 70))
        grad.setColorAt(1, T.color(self.color, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawPath(fill)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(T.color(self.color), 2))
        p.drawPath(path)


class DieSchematic(QWidget):
    """图鉴用的简化 die 俯视图。"""
    def __init__(self, layout: list[dict] | None = None, aspect: float = 1.0, parent=None):
        super().__init__(parent)
        self.layout = layout or []
        self.aspect = max(0.55, min(1.8, float(aspect)))
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin = 6
        avail_w, avail_h = w - 2 * margin, h - 2 * margin
        if avail_w / max(1.0, avail_h) > self.aspect:
            draw_h = avail_h
            draw_w = draw_h * self.aspect
        else:
            draw_w = avail_w
            draw_h = draw_w / self.aspect
        ox = (w - draw_w) / 2
        oy = (h - draw_h) / 2
        p.setPen(QPen(T.color(T.BORDER_HI), 1))
        p.setBrush(T.color(T.BG2))
        p.drawRoundedRect(QRectF(ox, oy, draw_w, draw_h), 5, 5)
        colors = {
            "big": "#ff7a6b", "mid": "#ffc46b", "little": "#7ee7c7",
            "gpu": "#ff6bd6", "npu": "#b98cff", "l3": "#3d7fe0",
            "isp": "#57d6c7", "modem": "#ffb86b", "io": "#8a93a6",
        }
        for b in self.layout:
            x = ox + draw_w * b.get("x", 0) / 100
            y = oy + draw_h * b.get("y", 0) / 100
            bw = draw_w * b.get("w", 10) / 100
            bh = draw_h * b.get("h", 10) / 100
            c = QColor(colors.get(b.get("k"), "#5aa8ff"))
            c.setAlpha(52)
            p.setBrush(c)
            p.setPen(QPen(QColor(colors.get(b.get("k"), "#5aa8ff")), 1))
            p.drawRoundedRect(QRectF(x, y, bw, bh), 3, 3)
            p.setPen(T.color(T.TEXT, 190))
            p.setFont(T.font(9))
            if bw > 34 and bh > 14:
                p.drawText(QRectF(x, y, bw, bh), Qt.AlignmentFlag.AlignCenter, b.get("label", ""))


class CurveChart(QWidget):
    """能效曲线：横轴功率 W，纵轴性能。"""
    def __init__(self, color: str = T.CYAN, parent=None):
        super().__init__(parent)
        self.points: list[tuple[float, float]] = []
        self.current: tuple[float, float] | None = None
        self.color = color
        self.setMinimumHeight(120)

    def set_points(self, pts: list[tuple[float, float]], current=None):
        self.points = pts
        self.current = current
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        left, bottom, top, right = 44, h - 28, 12, w - 14
        p.setPen(QPen(T.color(T.BORDER), 1))
        p.drawLine(left, top, left, bottom)
        p.drawLine(left, bottom, right, bottom)
        if not self.points:
            p.setPen(T.color(T.DIM))
            p.setFont(T.font(10))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "无数据")
            return
        xs = [x for x, y in self.points]
        ys = [y for x, y in self.points]
        x0, x1 = min(xs), max(xs) or 1.0
        y0, y1 = 0.0, (max(ys) or 1.0) * 1.12
        def sx(x): return left + (right - left) * (x - x0) / max(1e-6, x1 - x0)
        def sy(y): return bottom - (bottom - top) * (y - y0) / max(1e-6, y1 - y0)
        # 网格 + Y 轴刻度（不画 0 标签，避免和 X 轴起点重叠）
        p.setFont(T.font(8, mono=True))
        for i in range(3):
            t = i / 2.0
            yy = bottom - (bottom - top) * t
            p.setPen(QPen(T.color(T.BORDER, 120), 1, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(left + 2, yy), QPointF(right - 2, yy))
            if i > 0:
                p.setPen(T.color(T.DIM))
                p.drawText(QRectF(0, yy - 6, left - 5, 12),
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                           f"{y1 * t:.0f}")
        path = QPainterPath()
        for i, (x, y) in enumerate(self.points):
            if i == 0:
                path.moveTo(sx(x), sy(y))
            else:
                path.lineTo(sx(x), sy(y))
        p.setPen(QPen(T.color(self.color), 2))
        p.drawPath(path)
        if self.current:
            cx, cy = self.current
            p.setBrush(T.color(self.color))
            p.setPen(QPen(T.color(T.BG), 2))
            p.drawEllipse(QPointF(sx(cx), sy(cy)), 4, 4)
        p.setPen(T.color(T.DIM))
        p.setFont(T.font(8, mono=True))
        p.drawText(QRectF(0, bottom + 4, left - 2, 14),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, f"{x0:.1f}W")
        p.drawText(QRectF(right - 42, bottom + 4, 42, 14),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, f"{x1:.1f}W")
        p.drawText(QRectF(2, top - 10, 38, 10),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "MT")
