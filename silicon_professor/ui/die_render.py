"""Die 静态渲染：floorplan 画布、展示页大图、PNG 导出共用同一套绘制。

与 DieCanvas.paintEvent 像素一致；交互（拖拽/选中）仍在 DieCanvas 里。
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen

from ..engine.build import Plan, _rect
from . import theme as T

KIND_LABEL = {
    "big": "大核", "mid": "中核", "little": "小核",
    "l2": "L2", "l3": "L3", "slc": "SLC",
    "gpu": "GPU", "npu": "NPU", "isp": "ISP",
    "modem": "基带", "media": "媒体", "display": "显示",
    "dramphy": "DRAM PHY", "io": "IO",
}


def render_die(p: QPainter, size: QSize, plan: Plan, *,
               show_heat: bool = True, show_wires: bool = True,
               show_grid: bool = True, selected: str | None = None,
               title: str | None = None, subtitle: str | None = None,
               legend: bool = False) -> None:
    """把 plan 画满 size。title/subtitle 烧进图里（导出用）；legend 画热力+图例。"""
    W, H = size.width(), size.height()
    p.fillRect(0, 0, W, H, QColor(T.BG2))
    if plan is None:
        p.setPen(T.color(T.DIM))
        p.drawText(QRectF(0, 0, W, H), Qt.AlignmentFlag.AlignCenter, "等待设计…")
        return

    top = 0
    if title:
        p.setPen(T.color(T.TEXT))
        p.setFont(T.font(17, 700))
        p.drawText(QRectF(20, 12, W - 40, 26), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        if subtitle:
            p.setPen(T.color(T.TEXT2))
            p.setFont(T.font(10, 400, mono=True))
            p.drawText(QRectF(20, 38, W - 40, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, subtitle)
        top = 62

    pad = 26
    avail_w = W - 2 * pad - (150 if legend else 0)
    avail_h = H - top - pad - 22
    scale = min(avail_w / max(0.1, plan.die_w), avail_h / max(0.1, plan.die_h))
    dw = plan.die_w * scale
    dh = plan.die_h * scale
    ox = (W - (150 if legend else 0) - dw) / 2
    oy = top + (avail_h - dh) / 2

    def s(x, y):
        return QPointF(ox + x * scale, oy + y * scale)

    die = QRectF(ox, oy, dw, dh)
    grad = QLinearGradient(die.topLeft(), die.bottomRight())
    grad.setColorAt(0, QColor("#0d1a2a"))
    grad.setColorAt(1, QColor("#09111c"))
    p.setBrush(grad)
    p.setPen(QPen(T.color(T.BORDER_HI), 1.2))
    p.drawRoundedRect(die, 4, 4)

    if show_grid:
        p.setPen(QPen(T.color(T.BORDER, 110), 1, Qt.PenStyle.DotLine))
        step = 2.0
        x = step
        while x < plan.die_w:
            p.drawLine(s(x, 0), s(x, plan.die_h))
            x += step
        y = step
        while y < plan.die_h:
            p.drawLine(s(0, y), s(plan.die_w, y))
            y += step

    heat_mx = 1.0
    if show_heat:
        heat = plan.metrics.get("heat") or []
        gw = plan.metrics.get("grid_w", 1)
        gh = plan.metrics.get("grid_h", 1)
        heat_mx = max([max(r) for r in heat], default=0.0) or 1.0
        for iy, row in enumerate(heat):
            for ix, v in enumerate(row):
                t = min(1.0, v / heat_mx)
                if t < 0.22:
                    continue
                c = QColor.fromHsvF(0.58 - 0.58 * t, 0.85, 1.0, 0.30 * t + 0.04)
                x = dw * ix / gw
                y = dh * iy / gh
                p.fillRect(QRectF(ox + x, oy + y, dw / gw + 1, dh / gh + 1), c)

    if show_wires:
        for x1, y1, x2, y2, w in plan.metrics.get("segments", []):
            p.setPen(QPen(T.color(T.CYAN, 18 + int(min(30, w * 3))), 1))
            p.drawLine(s(x1, y1), s(x2, y2))

    for b in plan.blocks:
        x, y, w, h = _rect(plan, b)
        bad = False
        for other in plan.blocks:
            if other is b:
                continue
            ox2, oy2, ow, oh = _rect(plan, other)
            if x < ox2 + ow - 0.05 and ox2 < x + w - 0.05 and y < oy2 + oh - 0.05 and oy2 < y + h - 0.05:
                bad = True
                break
        r = QRectF(ox + x * scale, oy + y * scale,
                   max(1.0, w * scale), max(1.0, h * scale))
        c = QColor(b.color)
        c.setAlpha(44 if b.kind in ("big", "mid", "little") else 38)
        p.setBrush(c)
        pen = QPen(QColor(b.color), 1.0)
        if selected is not None and b.id == selected:
            pen = QPen(T.color(T.CYAN), 2.0)
        elif bad:
            pen = QPen(T.color(T.RED), 2.0)
        p.setPen(pen)
        p.drawRoundedRect(r, 3, 3)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(b.color))
        p.drawRoundedRect(QRectF(r.left(), r.top(), 2.0, r.height()), 1, 1)

        if r.width() > 34 and r.height() > 15:
            p.setPen(T.color(T.TEXT, 220))
            fnt = T.font(9, 600 if b.kind in ("big", "mid", "little") else 400)
            p.setFont(fnt)
            txt = b.label.replace("Cortex-", "")
            fm = p.fontMetrics()
            txt = fm.elidedText(txt, Qt.TextElideMode.ElideRight, max(8, int(r.width()) - 8))
            p.drawText(r.adjusted(5, 1, -2, -1), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, txt)
        if r.width() > 46 and r.height() > 40:
            p.setPen(T.color(T.TEXT2, 170))
            p.setFont(T.font(8, 400, mono=True))
            p.drawText(r.adjusted(5, 13, -2, -1), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                       f"{b.area:.1f}mm²")
        if b.edge:
            p.setPen(QPen(T.color(T.BLUE, 160), 1, Qt.PenStyle.DashLine))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(r.adjusted(-2, -2, 2, 2))

    p.setPen(T.color(T.TEXT2))
    p.setFont(T.font(9, 400, mono=True))
    p.drawText(QRectF(ox, oy + dh + 3, dw, 16),
               Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, f"{plan.die_w:.1f} mm")
    p.save()
    p.translate(ox - 4, oy + dh / 2)
    p.rotate(-90)
    p.drawText(QRectF(-dh / 2, -14, dh, 14), Qt.AlignmentFlag.AlignHCenter, f"{plan.die_h:.1f} mm")
    p.restore()

    if legend:
        _draw_legend(p, W, H, top, heat_mx, plan)


def _draw_legend(p: QPainter, W: int, H: int, top: int, heat_mx: float, plan: Plan):
    lx = W - 132
    p.setPen(T.color(T.DIM))
    p.setFont(T.font(10, 600))
    p.drawText(QRectF(lx, top + 4, 120, 16), Qt.AlignmentFlag.AlignLeft, "功率密度")
    # 热力条
    bx, by, bw, bh = lx, top + 26, 14, 120
    for i in range(bh):
        t = 1.0 - i / max(1, bh - 1)
        c = QColor.fromHsvF(0.58 - 0.58 * t, 0.85, 1.0, 0.30 * t + 0.04)
        p.fillRect(QRectF(bx, by + i, bw, 1.2), c)
    p.setPen(QPen(T.color(T.BORDER_HI), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(QRectF(bx, by, bw, bh))
    p.setPen(T.color(T.DIM))
    p.setFont(T.font(8, 400, mono=True))
    p.drawText(QRectF(bx + bw + 4, by - 2, 60, 12), Qt.AlignmentFlag.AlignLeft, "高")
    p.drawText(QRectF(bx + bw + 4, by + bh - 10, 60, 12), Qt.AlignmentFlag.AlignLeft, "低")
    # 模块图例
    seen: dict[str, str] = {}
    for b in plan.blocks:
        seen.setdefault(b.kind, b.color)
    y = by + bh + 14
    p.setFont(T.font(10, 400))
    for kind, color in seen.items():
        if y + 14 > H - 20:
            break
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color))
        p.drawRoundedRect(QRectF(lx, y, 10, 10), 2, 2)
        p.setPen(T.color(T.TEXT2))
        p.drawText(QRectF(lx + 15, y - 2, 105, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   KIND_LABEL.get(kind, kind))
        y += 17
