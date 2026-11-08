"""可拖拽的 die floorplan 画布。"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..engine.build import Plan, _rect
from . import theme as T
from .die_render import render_die


class DieCanvas(QWidget):
    moved = Signal()
    committed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.design = None
        self.plan: Plan | None = None
        self.show_heat = True
        self.show_wires = True
        self.show_grid = True
        self.selected: str | None = None
        self._drag_id: str | None = None
        self._drag_off = (0.0, 0.0)
        self._scale = 10.0
        self._ox = 20.0
        self._oy = 20.0
        self.setMinimumSize(620, 480)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(f"background:{T.BG2}; border:1px solid {T.BORDER}; border-radius:10px;")

    def set_plan(self, design, plan):
        self.design = design
        self.plan = plan
        self.update()

    def _calc(self):
        if not self.plan:
            return
        pad = 26
        self._scale = min((self.width() - 2 * pad) / max(0.1, self.plan.die_w),
                          (self.height() - 2 * pad) / max(0.1, self.plan.die_h))
        dw = self.plan.die_w * self._scale
        dh = self.plan.die_h * self._scale
        self._ox = (self.width() - dw) / 2
        self._oy = (self.height() - dh) / 2

    def _s(self, x, y):
        return QPointF(self._ox + x * self._scale, self._oy + y * self._scale)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(T.BG2))
        if not self.plan:
            p.setPen(T.color(T.DIM))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "等待设计…")
            return
        self._calc()
        render_die(p, self.size(), self.plan,
                   show_heat=self.show_heat, show_wires=self.show_wires,
                   show_grid=self.show_grid, selected=self.selected)
        return

    def _hit(self, pos) -> str | None:
        if not self.plan:
            return None
        mx = (pos.x() - self._ox) / self._scale
        my = (pos.y() - self._oy) / self._scale
        for b in reversed(self.plan.blocks):
            x, y, w, h = _rect(self.plan, b)
            if x <= mx <= x + w and y <= my <= y + h:
                return b.id
        return None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            bid = self._hit(e.position())
            if bid:
                self.rotate_block(bid)
            return
        if e.button() != Qt.MouseButton.LeftButton or not self.plan:
            return
        bid = self._hit(e.position())
        self.selected = bid
        if bid:
            p = self.plan.placements[bid]
            b = self.plan.block_map()[bid]
            x, y, w, h = _rect(self.plan, b)
            mx = (e.position().x() - self._ox) / self._scale
            my = (e.position().y() - self._oy) / self._scale
            self._drag_id = bid
            self._drag_off = (mx - p.x, my - p.y)
        self.update()

    def mouseMoveEvent(self, e):
        if not self._drag_id:
            bid = self._hit(e.position())
            if bid and self.plan:
                b = self.plan.block_map()[bid]
                self.setToolTip(f"{b.label}\n面积 {b.area:.1f} mm² \n功耗 {b.power:.2f} W")
            return
        if not self.plan:
            return
        p = self.plan.placements[self._drag_id]
        mx = (e.position().x() - self._ox) / self._scale - self._drag_off[0]
        my = (e.position().y() - self._oy) / self._scale - self._drag_off[1]
        p.x = max(0.0, round(mx * 4) / 4)
        p.y = max(0.0, round(my * 4) / 4)
        self.update()
        self.moved.emit()

    def mouseReleaseEvent(self, e):
        if self._drag_id:
            self._drag_id = None
            self.committed.emit()

    def rotate_block(self, bid: str):
        if not self.plan:
            return
        p = self.plan.placements[bid]
        p.rot = (p.rot + 90) % 180
        self.update()
        self.committed.emit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_R and self.selected:
            self.rotate_block(self.selected)
        else:
            super().keyPressEvent(e)
