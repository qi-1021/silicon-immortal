"""布局页：可拖拽 die floorplan + 热图/走线/拥塞。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from .. import theme as T
from ..die_canvas import DieCanvas
from ..widgets import Card, Stat


class FloorplanScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 22, 16)
        root.setSpacing(10)

        bar = QHBoxLayout()
        title = QLabel("芯片布局")
        title.setStyleSheet(f"color:{T.TEXT}; font-size:20px; font-weight:800;")
        bar.addWidget(title)
        sub = QLabel("拖动模块改变走线长度与热点；PHY 必须贴边。右键旋转。")
        sub.setStyleSheet(f"color:{T.DIM}; font-size:11px;")
        bar.addWidget(sub)
        bar.addStretch(1)
        self.b_heat = QPushButton("热图")
        self.b_wire = QPushButton("走线")
        self.b_grid = QPushButton("网格")
        for b, on in [(self.b_heat, True), (self.b_wire, True), (self.b_grid, True)]:
            b.setCheckable(True)
            b.setChecked(on)
            bar.addWidget(b)
        self.rotate = QPushButton("旋转 90°")
        self.rotate.clicked.connect(self._rotate)
        bar.addWidget(self.rotate)
        auto = QPushButton("自动布局")
        auto.clicked.connect(self._auto)
        bar.addWidget(auto)
        root.addLayout(bar)

        body = QHBoxLayout()
        body.setSpacing(12)
        self.canvas = DieCanvas()
        body.addWidget(self.canvas, 1)

        side_page = QWidget()
        side = QVBoxLayout(side_page)
        side.setContentsMargins(0, 0, 6, 0)
        side.setSpacing(8)
        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_scroll.setFixedWidth(348)
        side_scroll.setWidget(side_page)
        sc = Card("布局指标")
        grid = QHBoxLayout()
        grid.setSpacing(6)
        self.stats = {}
        for k, title in [("area", "面积"), ("util", "利用率"), ("wire", "走线功耗")]:
            s = Stat(title)
            self.stats[k] = s
            grid.addWidget(s)
        sc.add_layout(grid)
        grid2 = QHBoxLayout()
        grid2.setSpacing(6)
        for k, title in [("hot", "热点 °C"), ("cong", "拥塞")]:
            s = Stat(title)
            self.stats[k] = s
            grid2.addWidget(s)
        sc.add_layout(grid2)
        side.addWidget(sc)

        mc = Card("模块", "在布局页直接加减模块")
        self.mods = {}
        for field, label in [("isp", "ISP"), ("media", "媒体引擎"),
                             ("display", "显示/视频"), ("npu", "NPU"),
                             ("modem", "5G 基带")]:
            cb = QCheckBox(label)
            cb.toggled.connect(lambda v, f=field: self._toggle_mod(f, v))
            mc.add(cb)
            self.mods[field] = cb
        side.addWidget(mc)

        vc = Card("签核检查")
        self.checks = QLabel("—")
        self.checks.setWordWrap(True)
        self.checks.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; line-height:1.6;")
        vc.add(self.checks)
        side.addWidget(vc)

        lc = Card("怎么读这张图")
        legend = QLabel(
            "· 亮色 = 功率密度高。大核和 GPU 挨在一起会互相加热。\n"
            "· 线 = 自动生成的逻辑连线；越短越省功耗。\n"
            "· 蓝虚线框 = 必须贴边的 PHY/IO。\n"
            "· 利用率低说明 die 上有太多空白，成本会变差。")
        legend.setWordWrap(True)
        legend.setStyleSheet(f"color:{T.DIM}; font-size:10px; line-height:1.7;")
        lc.add(legend)
        side.addWidget(lc)
        side.addStretch(1)
        nxt = QPushButton("封装与散热  →")
        nxt.setObjectName("Primary")
        nxt.setFixedHeight(38)
        nxt.clicked.connect(lambda: win.go("package"))
        side.addWidget(nxt)
        body.addWidget(side_scroll, 0)
        root.addLayout(body, 1)

        self.b_heat.toggled.connect(self._toggle)
        self.b_wire.toggled.connect(self._toggle)
        self.b_grid.toggled.connect(self._toggle)
        self.canvas.moved.connect(self._live)
        self.canvas.committed.connect(self._commit)

    def _toggle(self):
        self.canvas.show_heat = self.b_heat.isChecked()
        self.canvas.show_wires = self.b_wire.isChecked()
        self.canvas.show_grid = self.b_grid.isChecked()
        self.canvas.update()

    def _toggle_mod(self, field: str, on: bool):
        d = self.win.design
        if field == "npu":
            d.npu_id = "npu30" if on else "none"
        elif field == "modem":
            d.modem_id = "modem5g" if on else "modem_ext"
        else:
            setattr(d, field, bool(on))
        d.placements.clear()
        self.win.request_recompute(force_layout=True)
        self.win.recompute_now(force_layout=True)
        self.refresh()

    def _rotate(self):
        if self.canvas.selected:
            self.win.design.rotated_once = True
            self.canvas.rotate_block(self.canvas.selected)
        else:
            self.checks.setText("先点选一个模块，再点“旋转 90°”。")

    def _auto(self):
        self.win.design.placements.clear()
        self.win.request_recompute(force_layout=True)
        self.win.recompute_now(force_layout=True)
        self.refresh()

    def _live(self):
        self.canvas.update()

    def _commit(self):
        self.win.request_recompute(force_layout=False)

    def refresh(self):
        if not self.win.result:
            return
        r = self.win.result
        self.canvas.set_plan(self.win.design, r["plan"])
        d = self.win.design
        self.mods["isp"].blockSignals(True); self.mods["isp"].setChecked(d.isp); self.mods["isp"].blockSignals(False)
        self.mods["media"].blockSignals(True); self.mods["media"].setChecked(d.media); self.mods["media"].blockSignals(False)
        self.mods["display"].blockSignals(True); self.mods["display"].setChecked(d.display); self.mods["display"].blockSignals(False)
        self.mods["npu"].blockSignals(True); self.mods["npu"].setChecked(d.npu_id != "none"); self.mods["npu"].blockSignals(False)
        self.mods["modem"].blockSignals(True); self.mods["modem"].setChecked(d.modem_id != "modem_ext"); self.mods["modem"].blockSignals(False)
        self.on_result()

    def on_result(self):
        r = self.win.result
        if not r:
            return
        m = r["metrics"]
        self.stats["area"].set(f"{r['die_area']:.1f}", "mm²")
        self.stats["util"].set(f"{m['utilization']*100:.0f}%", "已用 / die")
        self.stats["wire"].set(f"{m['wire_power']*1000:.0f}", "mW")
        self.stats["hot"].set(f"{r['thermal']['hotspot']:.0f}", "°C")
        self.stats["cong"].set(f"{m['congestion']*100:.0f}%", "布线压力")
        msgs = []
        for e in r["errors"][:4]:
            msgs.append("✕ " + e)
        for w in r["warnings"][:4]:
            msgs.append("· " + w)
        if not msgs:
            msgs = ["✓ 布局通过基本约束。", "· 试着把同类核心靠近 L3，GPU 远离大核。"]
        self.checks.setText("\n".join(msgs))
        self.checks.setStyleSheet(
            f"color:{T.RED if r['errors'] else T.TEXT2}; font-size:11px; line-height:1.6;")
        self.canvas.set_plan(self.win.design, r["plan"])
