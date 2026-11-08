"""封装与散热页。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QPushButton, QVBoxLayout, QWidget)

from ...data.blocks import COOLING, PACKAGES
from .. import theme as T
from ..widgets import BarRow, Card, CurveChart, Segmented, SliderRow, Stat


class Choice(QPushButton):
    def __init__(self, title: str, desc: str, meta: str):
        super().__init__()
        self.setCheckable(True)
        self.setMinimumHeight(78)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 9, 12, 9)
        lay.setSpacing(2)
        self.t = QLabel(title)
        self.t.setStyleSheet(f"color:{T.TEXT}; font-size:12px; font-weight:600;")
        self.d = QLabel(desc)
        self.d.setWordWrap(True)
        self.d.setStyleSheet(f"color:{T.DIM}; font-size:9px;")
        self.m = QLabel(meta)
        self.m.setStyleSheet(f"color:{T.AMBER}; font-size:10px; font-family:{T.FONT_MONO};")
        lay.addWidget(self.t)
        lay.addWidget(self.d)
        lay.addWidget(self.m)
        self.setStyleSheet(
            f"QPushButton {{ text-align:left; background:{T.BG2}; border:1px solid {T.BORDER};"
            f" border-radius:9px; padding:0; }}"
            f"QPushButton:hover {{ border-color:{T.BORDER_HI}; }}"
            f"QPushButton:checked {{ border:1px solid {T.CYAN_DIM}; background:{T.rgba(T.CYAN, 0.06)}; }}")


class PackageScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._loading = True
        root = QHBoxLayout(self)
        root.setContentsMargins(26, 18, 22, 18)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(10)
        self.pkg_card = Card("封装", "热阻、成本与最大 die 尺寸")
        self.pkg_grid = QGridLayout()
        self.pkg_grid.setSpacing(7)
        self.pkg_card.add_layout(self.pkg_grid)
        left.addWidget(self.pkg_card)

        self.cool_card = Card("设备侧散热场景", "整机厂商的使用条件；不属于核心/IP设计")
        self.cool_grid = QGridLayout()
        self.cool_grid.setSpacing(7)
        self.cool_card.add_layout(self.cool_grid)
        note=QLabel('芯片设计需满足设备给定的热预算；散热器、机身和环境属于整机设计。这里仅作为对照条件，改变它不表示芯片本身变好了。')
        note.setWordWrap(True);note.setObjectName('Muted');self.cool_card.add(note)
        self.device_scene=QPushButton('展开设备厂商的散热假设')
        self.device_scene.setCheckable(True);self.device_scene.toggled.connect(self.cool_card.setVisible)
        left.addWidget(self.device_scene)
        self.cool_card.setVisible(False)
        left.addWidget(self.cool_card)

        mc = Card("金属堆栈", "更多厚金属层 = 更低 RC 延迟，但 mask 更贵")
        self.metal = Segmented([("dense", "高密度"), ("balanced", "均衡"), ("perf", "性能")])
        mc.add(self.metal)
        self.metal_hint = QLabel("")
        self.metal_hint.setObjectName("Muted")
        self.metal_hint.setWordWrap(True)
        mc.add(self.metal_hint)
        left.addWidget(mc)

        cc = Card("Chiplet", "把加速器拆到第二颗 die；良率更好，但中介层/组装更贵")
        self.chiplet = QCheckBox("启用 Chiplet（需要 2.5D 封装）")
        cc.add(self.chiplet)
        self.chiplet_note = QLabel("")
        self.chiplet_note.setWordWrap(True)
        self.chiplet_note.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        cc.add(self.chiplet_note)
        left.addWidget(cc)

        ac = Card("设备使用条件")
        self.ambient = SliderRow("环境温度", 15, 40, 25, "{:.0f} °C",
                                 "25°C 是实验室；35°C 是夏天户外。")
        ac.add(self.ambient)
        left.addWidget(ac)
        left.addStretch(1)
        root.addLayout(left, 1)

        side = QVBoxLayout()
        side.setSpacing(9)
        sc = Card("热结果")
        grid = QGridLayout()
        grid.setSpacing(6)
        self.stats = {}
        for i, (k, title) in enumerate([("peak", "峰值 W"), ("sustain", "持续 W"),
                                        ("skin", "机身 °C"), ("tj", "结温 °C"),
                                        ("throttle", "降频"), ("hot", "热点 °C")]):
            s = Stat(title)
            self.stats[k] = s
            grid.addWidget(s, i // 2, i % 2)
        sc.add_layout(grid)
        side.addWidget(sc)

        bc = Card("目标")
        self.skin_bar = BarRow("机身温度", 0, 45, 55, "°C", T.AMBER)
        bc.add(self.skin_bar)
        self.tdp_bar = BarRow("峰值功耗", 0, 10, 20, "W", T.PINK)
        bc.add(self.tdp_bar)
        side.addWidget(bc)

        ec = Card("能效曲线", "横轴功耗 · 纵轴多核性能")
        self.curve = CurveChart()
        ec.add(self.curve)
        side.addWidget(ec)
        side.addStretch(1)
        nxt = QPushButton("工程验证  →")
        nxt.setObjectName("Primary")
        nxt.setFixedHeight(38)
        nxt.clicked.connect(lambda: win.go("engineering"))
        side.addWidget(nxt)
        side_wrap = QWidget()
        side_wrap.setLayout(side)
        side_wrap.setFixedWidth(340)
        root.addWidget(side_wrap, 0)

        self.chiplet.toggled.connect(self._chiplet)
        self.ambient.changed.connect(lambda v: self._set("ambient_c", v))
        self.metal.changed.connect(lambda v: self._set("metal_stack", v, True))
        self._loading = False

    def _chiplet(self, on: bool):
        if self._loading:
            return
        self.win.design.chiplet = bool(on)
        if on and self.win.design.package_id != "imc25d":
            self.win.design.package_id = "imc25d"
            self.win.request_recompute(force_layout=False)
            self.refresh()
        else:
            self.win.request_recompute(force_layout=False)

    def refresh(self):
        if not self.win.design:
            return
        self._loading = True
        d = self.win.design
        while self.pkg_grid.count():
            it = self.pkg_grid.takeAt(0)
            w = it.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        pkg_group = QButtonGroup(self)
        pkg_group.setExclusive(True)
        for i, p in enumerate(PACKAGES.values()):
            c = Choice(p["name"], p["note"], f"Rθjc {p['rjc']:.2f} · ${p['cost']:.0f} · ≤{p['max_area']}mm²")
            c.setChecked(p["id"] == d.package_id)
            c.clicked.connect(lambda _, pid=p["id"]: self._set("package_id", pid, True))
            pkg_group.addButton(c)
            self.pkg_grid.addWidget(c, i // 3, i % 3)

        while self.cool_grid.count():
            it = self.cool_grid.takeAt(0)
            w = it.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        cool_group = QButtonGroup(self)
        cool_group.setExclusive(True)
        for i, c0 in enumerate(COOLING.values()):
            c = Choice(c0["name"], c0["note"], f"Rθca {c0['rca']:.1f} · ${c0['cost']:.0f}")
            c.setChecked(c0["id"] == d.cooling_id)
            c.clicked.connect(lambda _, cid=c0["id"]: self._set("cooling_id", cid, True))
            cool_group.addButton(c)
            self.cool_grid.addWidget(c, i // 3, i % 3)

        self.metal.select(d.metal_stack)
        self.chiplet.setChecked(bool(d.chiplet))
        self.ambient.set_value(d.ambient_c)
        self._loading = False
        self.on_result()

    def _set(self, field: str, value, force: bool = False):
        if self._loading:
            return
        setattr(self.win.design, field, value)
        if field == "package_id" and value != "imc25d" and self.win.design.chiplet:
            self.win.design.chiplet = False
            self.chiplet.blockSignals(True)
            self.chiplet.setChecked(False)
            self.chiplet.blockSignals(False)
        self.win.request_recompute(force_layout=force)

    def on_result(self):
        r = self.win.result
        if not r:
            return
        t = r["thermal"]
        self.stats["peak"].set(f"{t['p_burst_actual']:.1f}")
        self.stats["sustain"].set(f"{t['p_sustain_actual']:.1f}")
        self.stats["skin"].set(f"{t['tskin']:.1f}", accent=T.RED if t["tskin"] > t["skin_limit"] else T.GREEN)
        self.stats["tj"].set(f"{t['tj']:.0f}")
        self.stats["throttle"].set(f"{t['throttle']*100:.0f}%")
        self.stats["hot"].set(f"{t['hotspot']:.0f}")
        self.skin_bar.set_values(t["tskin"], t["skin_limit"], 55)
        self.tdp_bar.set_values(t["p_burst_actual"], self.win.scenario["limits"]["max_tdp"], 22)
        self.metal_hint.setText(
            f"{r['node']['name']} · 金属堆栈会改变面积开销与最高频率；当前估算 die {r['die_area']:.1f}mm²。")
        curve = r["perf"].get("curve", [])
        self.curve.set_points([(x["power"], x["mt"]) for x in curve],
                              current=(t["p_sustain_actual"], r["perf"]["mt_sustain"]))
        self.chiplet_note.setText(
            ("已启用：良率按两颗 die 分别计算，BOM 增加中介层/组装；逻辑布局仍是单张图。"
             if self.win.design.chiplet else "未启用：单 die，良率按整块面积计算。"))
