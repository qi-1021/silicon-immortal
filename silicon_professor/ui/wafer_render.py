"""将当前布局重复排入 300mm 晶圆，布局与 DPW 计算共用几何函数。"""
from __future__ import annotations

import random

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QRadialGradient

from ..engine.wafer import wafer_sites
from . import theme as T
from .silicon_render import render_silicon


def render_wafer(size: QSize, plan, *, seed=0, title="", yield_fraction=None):
    img = QImage(size, QImage.Format_ARGB32)
    img.fill(QColor(T.BG2))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if plan is None:
        p.end()
        return img
    width, height = size.width(), size.height()
    side = min(width - 60, height - 110)
    side = max(10, side)
    cx, cy = width / 2, 62 + side / 2
    scale = side / 300
    r = side / 2
    disc = QRectF(cx - r, cy - r, side, side)
    grad = QRadialGradient(cx - r * .35, cy - r * .4, side)
    grad.setColorAt(0, QColor("#c9bfad"))
    grad.setColorAt(.4, QColor("#888da0"))
    grad.setColorAt(.75, QColor("#666974"))
    grad.setColorAt(1, QColor("#353f3f"))
    p.setBrush(grad)
    p.setPen(QPen(QColor("#939b9a"), 1))
    p.drawEllipse(disc)
    # 一次渲染缩略单元，重复绘制，避免按 die 数重新生成纹理。
    tile = render_silicon(QSize(180, 160), plan, seed=seed, legend=False, labels=False)
    tw, th = plan.die_w, plan.die_h
    crop_scale = min((180 - 52) / tw, (160 - 48) / th)
    dw, dh = tw * crop_scale, th * crop_scale
    src = QRectF((180 - dw) / 2, 26 + (160 - 48 - dh) / 2, dw, dh)
    sites = wafer_sites(tw, th)
    rng = random.Random(seed ^ 0xA7C3)
    for x, y in sites:
        rect = QRectF(cx + (x - tw / 2) * scale, cy + (y - th / 2) * scale, tw * scale, th * scale)
        p.drawImage(rect, tile, src)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(228, 215, 181, 110), .45))
        p.drawRect(rect)
        if yield_fraction is not None and rng.random() > yield_fraction:
            p.fillRect(rect, QColor(210, 73, 70, 155))
    # 晶圆定位缺口；绘制缺口不会影响排版边界（位于 3mm exclusion 内）。
    p.setBrush(QColor(T.BG2))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy + r), max(2, side * .009), max(2, side * .009))
    p.setFont(T.font(15, 600))
    p.setPen(T.color(T.TEXT))
    p.drawText(QRectF(20, 10, width - 40, 28), Qt.AlignmentFlag.AlignCenter, title or "300 mm 晶圆")
    p.setFont(T.font(11, mono=True))
    p.setPen(T.color(T.TEXT2))
    p.drawText(QRectF(8, cy + r + 12, width - 16, 24), Qt.AlignmentFlag.AlignCenter,
               f"300 mm · edge 3 mm · scribe 80 µm · {len(sites)} complete dies")
    p.end()
    return img
