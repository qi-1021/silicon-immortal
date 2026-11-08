"""硅片风 Die 渲染：看起来像显微镜下的真实 die，而不是设计图纸。

手法（全部确定性，seed 来自设计）：
- 大尺度 mottling：几十个柔边径向渐变椭圆，模拟工艺起伏
- 细颗粒：平铺噪声贴片
- SRAM（L2/L3/SLC）：双尺度阵列网格 + bank 分隔 + 外围电路边带
- GPU：纵向 shader 列条纹；PHY/IO：边缘引脚 tick
- 鞣光（对角柔光）+ 暗角 + 内倒角
- 标注：白字黑影，只在放得下时画；图例/标题烧进图

交互式 floorplan 画布继续用示意图（快、清楚）；展示页与 PNG 导出走这里。
"""
from __future__ import annotations

import math
import random

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QRadialGradient, QLinearGradient

from ..engine.build import _rect
from . import theme as T
from .die_render import KIND_LABEL

_NOISE_CACHE: dict[int, QImage] = {}


def _noise_tile(seed: int, size: int = 192) -> QImage:
    key = (seed ^ 0x9E3779B9) & 0xFFFFFFFF
    hit = _NOISE_CACHE.get(key)
    if hit is not None:
        return hit
    rng = random.Random(key)
    img = QImage(size, size, QImage.Format_ARGB32)
    for y in range(size):
        for x in range(size):
            v = rng.randint(0, 255)
            img.setPixel(x, y, (255 << 24) | (v << 16) | (v << 8) | v)
    if len(_NOISE_CACHE) >= 96:
        _NOISE_CACHE.pop(next(iter(_NOISE_CACHE)))
    _NOISE_CACHE[key] = img
    return img


KIND_TONE = {
    "big": "#9d8971", "mid": "#8c846f", "little": "#788776",
    "l2": "#658882", "l3": "#588b8a", "slc": "#65868c",
    "gpu": "#92849b", "npu": "#887f92", "isp": "#799683",
    "modem": "#9d8b6b", "media": "#818f99", "display": "#81959c",
    "dramphy": "#a49379", "io": "#889186",
}


def _tile(p: QPainter, rect: QRectF, tile: QImage, alpha: float):
    p.save()
    p.setClipRect(rect)
    p.setOpacity(alpha)
    x = rect.x()
    while x < rect.right():
        y = rect.y()
        while y < rect.bottom():
            p.drawImage(QPointF(x, y), tile)
            y += tile.height()
        x += tile.width()
    p.restore()


def render_silicon(size: QSize, plan, *, seed: int = 0, title: str | None = None,
                   subtitle: str | None = None, legend: bool = True,
                   labels: bool = True) -> QImage:
    W, H = size.width(), size.height()
    img = QImage(W, H, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    rng = random.Random((seed ^ 0x51ED) & 0xFFFFFFFF)

    p.fillRect(0, 0, W, H, QColor(T.BG2))
    if plan is None:
        p.setPen(T.color(T.DIM))
        p.drawText(QRectF(0, 0, W, H), Qt.AlignmentFlag.AlignCenter, "等待设计…")
        p.end()
        return img

    top = 0
    if title:
        p.setPen(T.color(T.TEXT))
        p.setFont(T.font(19, 700))
        p.drawText(QRectF(20, 12, W - 40, 26), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        if subtitle:
            p.setPen(T.color(T.TEXT2))
            p.setFont(T.font(10, 400, mono=True))
            p.drawText(QRectF(20, 40, W - 40, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, subtitle)
        top = 64

    pad = 26
    avail_w = W - 2 * pad - (150 if legend else 0)
    avail_h = H - top - pad - 22
    scale = min(avail_w / max(0.1, plan.die_w), avail_h / max(0.1, plan.die_h))
    dw = plan.die_w * scale
    dh = plan.die_h * scale
    ox = (W - (150 if legend else 0) - dw) / 2
    oy = top + (avail_h - dh) / 2
    die = QRectF(ox, oy, dw, dh)

    # 基底
    base = QLinearGradient(die.topLeft(), die.bottomLeft())
    base.setColorAt(0, QColor("#141a26"))
    base.setColorAt(1, QColor("#090c12"))
    p.setBrush(base)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(die, 5, 5)

    # 大尺度 mottling（工艺起伏），裁剪到 die 内
    p.save()
    p.setClipRect(die)
    for _ in range(130):
        cx = ox + rng.random() * dw
        cy = oy + rng.random() * dh
        rad = 40 + rng.random() * max(dw, dh) * 0.22
        tone = rng.choice([(120, 140, 180), (140, 130, 120), (100, 130, 160), (150, 150, 160)])
        g = QRadialGradient(cx, cy, rad)
        g.setColorAt(0, QColor(*tone, int(10 + rng.random() * 14)))
        g.setColorAt(1, QColor(*tone, 0))
        p.setBrush(g)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), rad, rad)
    # 细颗粒
    _tile(p, die, _noise_tile(seed), 0.10)
    p.restore()

    # 各 block（留 1.5px 划片槽；双线 guard ring）
    for bi, b in enumerate(plan.blocks):
        x, y, w, h = _rect(plan, b)
        r = QRectF(ox + x * scale, oy + y * scale,
                   max(1.0, w * scale), max(1.0, h * scale))
        r = r.adjusted(1.5, 1.5, -1.5, -1.5)
        tone = QColor(KIND_TONE.get(b.kind, "#2a3040"))
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        grad.setColorAt(0, tone.lighter(115))
        grad.setColorAt(0.5, tone)
        grad.setColorAt(1, tone.darker(115))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, 2, 2)
        p.setPen(QPen(tone.lighter(165), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), 2, 2)
        p.setPen(QPen(QColor(0, 0, 0, 90), 1))
        p.drawRoundedRect(r.adjusted(2.0, 2.0, -2.0, -2.0), 1, 1)
        # 内倒角：左上亮，右下暗
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        p.drawLine(r.topLeft() + QPointF(2, 1), r.topRight() + QPointF(-2, 1))
        p.setPen(QPen(QColor(0, 0, 0, 60), 1))
        p.drawLine(r.bottomLeft() + QPointF(2, -1), r.bottomRight() + QPointF(-2, -1))

        p.save()
        p.setClipRect(r.adjusted(1, 1, -1, -1))
        if b.kind in ("l2", "l3", "slc"):
            # SRAM 阵列：细网格 + bank 分隔
            step = max(3.0, scale * 0.30)
            p.setPen(QPen(QColor(180, 210, 235, 46), 1))
            gx = r.left()
            while gx <= r.right():
                p.drawLine(QPointF(gx, r.top()), QPointF(gx, r.bottom()))
                gx += step
            gy = r.top()
            while gy <= r.bottom():
                p.drawLine(QPointF(r.left(), gy), QPointF(r.right(), gy))
                gy += step
            nb = 4
            p.setPen(QPen(QColor(200, 225, 245, 70), 1))
            for i in range(1, nb):
                bx = r.left() + r.width() * i / nb
                p.drawLine(QPointF(bx, r.top()), QPointF(bx, r.bottom()))
            # 子阵列：更粗的横向分隔 + 斑点
            p.setPen(QPen(QColor(200, 225, 245, 40), 2))
            nh = max(2, int(r.height() / 26))
            for i in range(1, nh):
                hy = r.top() + r.height() * i / nh
                p.drawLine(QPointF(r.left(), hy), QPointF(r.right(), hy))
            _tile(p, r, _noise_tile(seed + 101 + bi * 17), 0.10)
        elif b.kind == "gpu":
            # shader 列条纹
            step = max(6.0, scale * 0.55)
            p.setPen(QPen(QColor(255, 190, 230, 30), 2))
            gx = r.left() + step / 2
            while gx <= r.right():
                p.drawLine(QPointF(gx, r.top() + 2), QPointF(gx, r.bottom() - 2))
                gx += step
        else:
            _tile(p, r, _noise_tile(seed + 7 + bi * 131), 0.10 + (bi % 3) * 0.03)
            # 重复的标准单元行与局部金属层；纹理只示意，不对应真实晶体管。
            for row in range(int(r.top()) + 3, int(r.bottom()), 4):
                p.setPen(QPen(QColor(35, 40, 35, 65), 0.7))
                p.drawLine(QPointF(r.left(), row), QPointF(r.right(), row))
                for col in range(int(r.left()) + rng.randint(0, 5), int(r.right()), 7):
                    p.setPen(QPen(QColor(220, 205, 164, rng.randint(25, 90)), 0.6))
                    p.drawLine(QPointF(col, row), QPointF(col + rng.randint(2, 6), row + 2))
        if b.edge:
            # 引脚 tick
            p.setPen(QPen(QColor(160, 200, 240, 90), 1))
            n = max(4, int(min(r.width(), r.height()) / 4))
            for i in range(n + 1):
                t = i / n
                if r.width() >= r.height():
                    px = r.left() + r.width() * t
                    p.drawLine(QPointF(px, r.top()), QPointF(px, r.top() + 4))
                    p.drawLine(QPointF(px, r.bottom() - 4), QPointF(px, r.bottom()))
                else:
                    py = r.top() + r.height() * t
                    p.drawLine(QPointF(r.left(), py), QPointF(r.left() + 4, py))
                    p.drawLine(QPointF(r.right() - 4, py), QPointF(r.right(), py))
        p.restore()

    # 鞣光
    sheen = QLinearGradient(die.topLeft(), die.bottomRight())
    sheen.setColorAt(0, QColor(255, 255, 255, 22))
    sheen.setColorAt(0.45, QColor(255, 255, 255, 0))
    sheen.setColorAt(1, QColor(255, 255, 255, 10))
    p.save()
    p.setClipRect(die)
    p.setBrush(sheen)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(die)
    p.restore()

    # seal ring：die 边缘双环
    p.setPen(QPen(QColor(190, 210, 235, 70), 1.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(die.adjusted(2.5, 2.5, -2.5, -2.5), 4, 4)
    p.setPen(QPen(QColor(0, 0, 0, 120), 2))
    p.drawRoundedRect(die.adjusted(4.5, 4.5, -4.5, -4.5), 3, 3)

    # 暗角
    vg = QRadialGradient(W / 2, (top + H) / 2, max(W, H) * 0.62)
    vg.setColorAt(0.55, QColor(0, 0, 0, 0))
    vg.setColorAt(1, QColor(0, 0, 0, 110))
    p.setBrush(vg)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(0, 0, W, H)

    # 标注（白字黑影）
    for b in plan.blocks:
        if not labels:
            break
        x, y, w, h = _rect(plan, b)
        r = QRectF(ox + x * scale, oy + y * scale,
                   max(1.0, w * scale), max(1.0, h * scale))
        if r.width() > 34 and r.height() > 15:
            fnt = T.font(9, 600 if b.kind in ("big", "mid", "little") else 400)
            p.setFont(fnt)
            txt = b.label.replace("Cortex-", "")
            fm = p.fontMetrics()
            if fm.horizontalAdvance(txt) > r.width() - 10:
                txt = fm.elidedText(txt, Qt.TextElideMode.ElideRight, max(8, int(r.width()) - 10))
            tw = fm.horizontalAdvance(txt) + 10
            tag = QRectF(r.left() + 3, r.top() + max(2.0, (r.height() - 15) / 2), min(tw, r.width() - 6), 15)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(4, 8, 14, 150))
            p.drawRoundedRect(tag, 3, 3)
            p.setPen(QPen(QColor(255, 255, 255, 40), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(tag, 3, 3)
            p.setPen(T.color(T.TEXT, 235))
            p.drawText(tag.adjusted(5, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, txt)
        if r.width() > 46 and r.height() > 40:
            p.setFont(T.font(8, 400, mono=True))
            box = r.adjusted(5, 13, -2, -1)
            p.setPen(QColor(0, 0, 0, 190))
            p.drawText(box.translated(0.8, 0.8), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                       f"{b.area:.1f}mm²")
            p.setPen(T.color(T.TEXT2, 185))
            p.drawText(box, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, f"{b.area:.1f}mm²")

    # 尺寸标注
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
        _draw_legend(p, W, H, top, plan)

    p.end()
    return img


def _draw_legend(p: QPainter, W: int, H: int, top: int, plan):
    lx = W - 132
    p.setPen(T.color(T.DIM))
    p.setFont(T.font(10, 600))
    p.drawText(QRectF(lx, top + 4, 120, 16), Qt.AlignmentFlag.AlignLeft, "模块")
    seen: dict[str, str] = {}
    for b in plan.blocks:
        seen.setdefault(b.kind, KIND_TONE.get(b.kind, "#2a3040"))
    y = top + 28
    p.setFont(T.font(10, 400))
    for kind, color in seen.items():
        if y + 14 > H - 20:
            break
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color).lighter(115))
        p.drawRoundedRect(QRectF(lx, y, 10, 10), 2, 2)
        p.setPen(T.color(T.TEXT2))
        p.drawText(QRectF(lx + 15, y - 2, 105, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   KIND_LABEL.get(kind, kind))
        y += 17
