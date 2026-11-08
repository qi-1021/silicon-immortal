"""动效系统：按 Emil Kowalski 动效哲学裁剪后的 Qt 实现。

规则（写死在这里，调用方不用再想）：
- 只做 opacity（QGraphicsOpacityEffect）与数字滚动；不动布局属性。
- 进入类动效一律 ease-out 系；UI 动效 < 300ms。
- 高频路径（滑杆/重算/导航）一律不同效；只在低频时刻用：
  流片展示、教学勾选、首次进入开始页。
- SILICON_PROFESSOR_NO_ANIM=1 或 reduced=True 时全部跳过，直接落终态。
"""
from __future__ import annotations

import os

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QTimer

_enabled = os.environ.get("SILICON_PROFESSOR_NO_ANIM", "") != "1"

# House curves
EASE_ENTER = QEasingCurve(QEasingCurve.OutCubic)      # 进入/显现：快启动
EASE_COUNT = QEasingCurve(QEasingCurve.OutExpo)        # 数字滚动：强 ease-out
DUR_ENTER = 180
DUR_POP = 160
DUR_COUNT = 750
STAGGER_STEP = 50


def set_enabled(on: bool):
    global _enabled
    _enabled = bool(on)


def is_enabled() -> bool:
    return _enabled


def _valid(w) -> bool:
    try:
        from shiboken6 import isValid
        return isValid(w)
    except Exception:
        return w is not None


def fade_in(w, duration: int = DUR_ENTER, delay: int = 0):
    """opacity 0→1。低频进入动效用；高频路径不要调这个。"""
    from PySide6.QtWidgets import QGraphicsOpacityEffect
    if not _enabled or not _valid(w):
        return None
    eff = QGraphicsOpacityEffect(w)
    eff.setOpacity(0.0)
    w.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", w)
    anim.setDuration(max(1, duration))
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(EASE_ENTER)
    anim.finished.connect(lambda: _clear(w, eff, anim))
    if delay > 0:
        QTimer.singleShot(delay, anim.start)
    else:
        anim.start()
    return anim


def _clear(w, eff, anim):
    # widget 拥有 effect：setGraphicsEffect(None) 会直接销毁它，无需 deleteLater
    try:
        if _valid(w) and w.graphicsEffect() is eff:
            w.setGraphicsEffect(None)
    except RuntimeError:
        pass


def stagger_in(widgets, base_delay: int = 0, step: int = STAGGER_STEP,
               duration: int = DUR_ENTER):
    """一组卡片依次淡入（30–80ms 间隔）。只用于低频页面进入。"""
    if not _enabled:
        return []
    anims = []
    for i, w in enumerate(widgets):
        a = fade_in(w, duration=duration, delay=base_delay + i * step)
        if a:
            anims.append(a)
    return anims


def flash(w, duration: int = DUR_POP):
    """状态翻转提示：快速淡入一次。 teaching 勾选这类偶发时刻用。"""
    return fade_in(w, duration=duration)


class _Counter(QObject):
    def __init__(self, label, target: float, fmt: str, duration: int):
        super().__init__(label)
        self._label = label
        self._target = float(target)
        self._fmt = fmt
        self._ticks = max(1, int(duration / 16))
        self._i = 0
        self._start = 0.0
        try:
            txt = label.text().replace(",", "")
            self._start = float(txt)
        except Exception:
            self._start = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.start(16)

    def _step(self):
        # 从当前显示值开始插值：可打断、可重定向
        if not _valid(self._label):
            self._timer.stop()
            return
        self._i += 1
        t = min(1.0, self._i / self._ticks)
        eased = 1.0 - (1.0 - t) ** 4
        v = self._start + (self._target - self._start) * eased
        try:
            self._label.setText(self._fmt.format(v))
        except Exception:
            pass
        if t >= 1.0:
            self._timer.stop()


def count_up(label, target: float, fmt: str = "{:.0f}", duration: int = DUR_COUNT):
    """数字滚动到终值。从当前显示值开始，可被新调用打断重定向。"""
    if not _enabled or not _valid(label):
        try:
            label.setText(fmt.format(float(target)))
        except Exception:
            pass
        return None
    old = getattr(label, "_counter", None)
    if old is not None:
        try:
            old._timer.stop()
        except Exception:
            pass
    c = _Counter(label, target, fmt, duration)
    label._counter = c
    return c
