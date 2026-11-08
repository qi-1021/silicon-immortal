"""物理实现页：同一份 RTL 的库、VT、密度/时序与长宽比。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ...data.cores import CORES, custom_ip, get_ip
from ...data.nodes import NODES
from ...engine import ppa
from ...engine.types import Impl
from .. import theme as T
from ..widgets import Card, SectionTitle, Segmented, SliderRow, Stat


class PhysicalScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._loading = True
        self.cards: list[dict] = []

        root = QHBoxLayout(self)
        root.setContentsMargins(26, 18, 22, 18)
        root.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        self.left = QVBoxLayout(page)
        self.left.setContentsMargins(0, 0, 8, 0)
        self.left.setSpacing(12)
        scroll.setWidget(page)
        root.addWidget(scroll, 1)

        intro = Card("CPU 物理实现")
        txt = QLabel(
            "CPU IP 还需要综合、布局和布线。标准单元库、阈值电压与时序约束会改变面积、频率和漏电。"
            "这里调整的是物理实现参数，微架构参数另在自研核实验室设置。")
        txt.setWordWrap(True)
        txt.setStyleSheet(f"color:{T.TEXT2}; font-size:12px; line-height:1.65;")
        intro.add(txt)
        self.left.addWidget(intro)

        lab = QPushButton("设计自己的 CPU / GPU / NPU / ISP  →")
        lab.clicked.connect(lambda: win.go("studio"))
        self.left.addWidget(lab)
        self.cards_box = QVBoxLayout()
        self.cards_box.setSpacing(10)
        self.left.addLayout(self.cards_box)
        self.left.addStretch(1)

        side = QVBoxLayout()
        side.setSpacing(10)
        sc = Card("实现结果")
        grid = QGridLayout()
        grid.setSpacing(7)
        self.stats = {}
        for i, (k, title) in enumerate([("area", "DIE mm²"), ("power", "峰值 W"),
                                        ("st", "ST"), ("mt", "MT")]):
            s = Stat(title)
            self.stats[k] = s
            grid.addWidget(s, i // 2, i % 2)
        sc.add_layout(grid)
        side.addWidget(sc)

        oc = Card("取舍")
        self.over = QLabel("—")
        self.over.setWordWrap(True)
        self.over.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; line-height:1.7;")
        oc.add(self.over)
        side.addWidget(oc)
        side.addStretch(1)
        nxt = QPushButton("芯片布局  →")
        nxt.setObjectName("Primary")
        nxt.setFixedHeight(38)
        nxt.clicked.connect(lambda: win.go("floorplan"))
        side.addWidget(nxt)
        side_wrap = QWidget()
        side_wrap.setLayout(side)
        side_wrap.setFixedWidth(340)
        root.addWidget(side_wrap, 0)
        self._loading = False

    def refresh(self):
        if not self.win.design:
            return
        self._loading = True
        while self.cards_box.count():
            it = self.cards_box.takeAt(0)
            w = it.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        self.cards = []
        d = self.win.design
        node = NODES[d.node_id]
        for idx, g in enumerate(d.cores):
            if g.count <= 0:
                continue
            ip = get_ip(d, g.core_id)
            if not ip:
                continue
            card = QFrame()
            card.setObjectName("Panel")
            card.setStyleSheet(f"QFrame#Panel {{ background:{T.PANEL}; border:1px solid {T.BORDER}; border-radius:10px; }}")
            lay = QVBoxLayout(card)
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(8)

            head = QHBoxLayout()
            name = QLabel(f"{ip['name']}  ×{g.count}")
            name.setStyleSheet(f"color:{T.TEXT}; font-size:14px; font-weight:700;")
            head.addWidget(name)
            head.addStretch(1)
            role = QLabel(ip["arch"])
            role.setStyleSheet(f"color:{T.DIM}; font-size:10px; font-family:{T.FONT_MONO};")
            head.addWidget(role)
            lay.addLayout(head)

            row = QHBoxLayout()
            row.setSpacing(14)
            col1 = QVBoxLayout()
            col1.setSpacing(3)
            l1 = QLabel("标准单元库")
            l1.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
            col1.addWidget(l1)
            lib = Segmented([("hd", "HD 密度"), ("sd", "SD 标准"), ("hp", "HP 性能")], g.impl.lib)
            lib.changed.connect(lambda v, i=idx: self._set(i, "lib", v))
            col1.addWidget(lib)
            l2 = QLabel("阈值电压")
            l2.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
            col1.addWidget(l2)
            vt = Segmented([("ulvt", "ULVT"), ("lvt", "LVT"), ("svt", "SVT"), ("hvt", "HVT")], g.impl.vt)
            vt.changed.connect(lambda v, i=idx: self._set(i, "vt", v))
            col1.addWidget(vt)
            row.addLayout(col1, 1)

            col2 = QVBoxLayout()
            col2.setSpacing(4)
            dens = SliderRow("密度优先", 0, 1, g.impl.density, "{:.0%}",
                             "往右收面积，代价是频率。")
            dens.changed.connect(lambda v, i=idx: self._set(i, "density", v))
            col2.addWidget(dens)
            tim = SliderRow("时序优先", 0, 1, g.impl.timing, "{:.0%}",
                            "往右冲频率，代价是面积和功耗。")
            tim.changed.connect(lambda v, i=idx: self._set(i, "timing", v))
            col2.addWidget(tim)
            row.addLayout(col2, 1)
            lay.addLayout(row)

            row2 = QHBoxLayout()
            l3 = QLabel("核心长宽比")
            l3.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
            row2.addWidget(l3)
            asp = Segmented([("1", "1:1"), ("2", "2:1"), ("4", "4:1")], str(int(g.impl.aspect)))
            asp.changed.connect(lambda v, i=idx: self._set(i, "aspect", float(v), True))
            row2.addWidget(asp)
            row2.addStretch(1)
            lay.addLayout(row2)

            metrics = QLabel("—")
            metrics.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; font-family:{T.FONT_MONO};")
            lay.addWidget(metrics)
            self.cards_box.addWidget(card)
            self.cards.append(dict(idx=idx, metrics=metrics, impl=g.impl, ip=ip))

        self._loading = False
        self._update_all()
        self.on_result()




    def _set(self, idx: int, field: str, value, force: bool = False):
        if self._loading or idx >= len(self.win.design.cores):
            return
        setattr(self.win.design.cores[idx].impl, field, value)
        if force:
            self.win.design.placements.clear()
        self._update_all()
        self.win.request_recompute(force_layout=force)

    def _update_all(self):
        d = self.win.design
        node = NODES[d.node_id]
        for c in self.cards:
            g = d.cores[c["idx"]]
            ip = c["ip"]
            default = Impl()
            fmax = ppa.core_fmax(ip, g.impl, node)
            fmax0 = ppa.core_fmax(ip, default, node)
            area = ppa.core_area(ip, g.impl, node, g.l2_mb, g.l2_shared, g.count)
            area0 = ppa.core_area(ip, default, node, g.l2_mb, g.l2_shared, g.count)
            clock = g.clock if g.clock > 0 else fmax * 0.9
            p = ppa.core_power(ip, min(clock, fmax), fmax, area, node, g.impl)
            p0 = ppa.core_power(ip, min(clock, fmax0), fmax0, area0, node, default)
            c["metrics"].setText(
                f"面积 {area:.2f}mm² ({area/area0-1:+.0%})   "
                f"Fmax {fmax:.2f}GHz ({fmax/fmax0-1:+.0%})   "
                f"功耗 {p[0]+p[1]:.1f}W ({(p[0]+p[1])/(p0[0]+p0[1])-1:+.0%})")
            c["metrics"].setStyleSheet(
                f"color:{T.CYAN if fmax > fmax0 else T.TEXT2}; font-size:11px; font-family:{T.FONT_MONO};")

    def on_result(self):
        r = self.win.result
        if not r:
            return
        self.stats["area"].set(f"{r['die_area']:.1f}")
        self.stats["power"].set(f"{r['power']['peak']:.1f}")
        self.stats["st"].set(f"{r['perf']['st_burst']:.0f}")
        self.stats["mt"].set(f"{r['perf']['mt_burst']:.0f}")
        msgs = []
        if r["perf"]["st_sustain"] < r["perf"]["st_burst"] * 0.75:
            msgs.append("持续频率掉得厉害：高性能库 + 高电压换来的峰值，散热撑不住。")
        if r["yield_"]["yield_pct"] < 0.6:
            msgs.append("良率偏低：面积和缺陷密度在吃你的利润。")
        if r["nre"]["custom_groups"] > 0:
            msgs.append(f"你有 {r['nre']['custom_groups']} 组自定义实现，NRE 增加约 "
                        f"${r['nre']['custom']:.0f}M，但换来了差异化。")
        self.over.setText("\n".join("· " + m for m in msgs) if msgs else "当前 PPA 检查没有新增提示。可以到工程验证页检查供电与 PVT 条件。")
