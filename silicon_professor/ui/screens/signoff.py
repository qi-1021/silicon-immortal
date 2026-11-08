"""签核页：良率、成本、NRE、阻塞项与流片。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractSpinBox, QDoubleSpinBox, QFileDialog, QFrame,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from .. import theme as T
from ..widgets import Card, Gauge, SliderRow, Stat


class SignoffScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._loading = True
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 18, 24, 18)
        root.setSpacing(12)

        head = QHBoxLayout()
        t = QLabel("签核 · TAPE-OUT")
        t.setStyleSheet(f"color:{T.TEXT}; font-size:22px; font-weight:800; letter-spacing:1px;")
        head.addWidget(t)
        head.addStretch(1)
        self.badge = QLabel("—")
        self.badge.setStyleSheet(f"color:{T.AMBER}; font-size:11px;")
        head.addWidget(self.badge)
        root.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(14)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_page = QWidget()
        left = QVBoxLayout(left_page)
        left.setContentsMargins(0, 0, 6, 0)
        left.setSpacing(12)
        left_scroll.setWidget(left_page)

        top = QHBoxLayout()
        top.setSpacing(12)
        yc = Card("预计良率")
        self.gauge = Gauge(0.8, "Murphy + bin")
        self.gauge.setFixedSize(190, 132)
        yc.body.addWidget(self.gauge, 0, Qt.AlignmentFlag.AlignHCenter)
        top.addWidget(yc, 1)
        sc = Card("面积与成本")
        g = QGridLayout()
        g.setSpacing(6)
        self.stats = {}
        for i, (k, title) in enumerate([("area", "DIE mm²"), ("dpw", "每片 die"),
                                        ("die", "裸 die $"), ("unit", "单颗 $")]):
            s = Stat(title)
            self.stats[k] = s
            g.addWidget(s, i // 2, i % 2)
        sc.add_layout(g)
        top.addWidget(sc, 1)
        left.addLayout(top)

        nc = Card("NRE 明细", "流片前一次性投入")
        self.nre_grid = QGridLayout()
        self.nre_grid.setSpacing(4)
        nc.add_layout(self.nre_grid)
        self.nre_total = QLabel("—")
        self.nre_total.setStyleSheet(f"color:{T.AMBER}; font-size:13px; font-weight:600; font-family:{T.FONT_MONO};")
        nc.add(self.nre_total)
        left.addWidget(nc)

        bc = Card("Bin 与频率")
        self.bin = QLabel("—")
        self.bin.setWordWrap(True)
        self.bin.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; line-height:1.6; font-family:{T.FONT_MONO};")
        bc.add(self.bin)
        left.addWidget(bc)

        note = Card("怎么读签核")
        nt = QLabel(
            "· 可出售比例 = 缺陷良率 × 频率档位可用率；目标越高，可达标的 die 越少。\n"
            "· 单颗成本含 die、封装、测试与外挂基带方案。外部 DRAM、存储和散热另计。\n"
            "· 检查通过后才能流片：预算、成本、温度、功耗、验证规划、供电与 PVT 档位。\n"
            "· 本作检查的是教学模型，不会运行真实 STA、DRC、LVS 或 ATPG。")
        nt.setWordWrap(True)
        nt.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; line-height:1.8;")
        note.add(nt)
        left.addWidget(note)
        left.addStretch(1)
        body.addWidget(left_scroll, 3)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_page = QWidget()
        right = QVBoxLayout(right_page)
        right.setContentsMargins(0, 0, 6, 0)
        right.setSpacing(10)
        right_scroll.setWidget(right_page)
        cc = Card("签核检查")
        self.checks = QLabel("—")
        self.checks.setWordWrap(True)
        self.checks.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; line-height:1.75;")
        cc.add(self.checks)
        right.addWidget(cc)

        wc = Card("市场预判")
        self.market = QLabel("—")
        self.market.setWordWrap(True)
        self.market.setStyleSheet(f"color:{T.TEXT}; font-size:12px; line-height:1.75;")
        wc.add(self.market)
        right.addWidget(wc)

        qc = Card("媒体会怎么写")
        self.quote = QLabel("—")
        self.quote.setWordWrap(True)
        self.quote.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; font-style:italic; line-height:1.7;")
        qc.add(self.quote)
        right.addWidget(qc)

        strat = Card("商业策略", "命名、价格、跑分调优、生态投入")
        nrow = QHBoxLayout()
        nl = QLabel("芯片名称")
        nl.setStyleSheet(f"color:{T.TEXT2}; font-size:11px;")
        nrow.addWidget(nl)
        self.chip_name = QLineEdit()
        self.chip_name.setPlaceholderText("例如：XRING O4")
        self.chip_name.setMaxLength(40)
        self.chip_name.textChanged.connect(lambda v: self._name(v))
        nrow.addWidget(self.chip_name, 1)
        strat.add_layout(nrow)
        prow = QHBoxLayout()
        pl = QLabel("售价")
        pl.setStyleSheet(f"color:{T.TEXT2}; font-size:11px;")
        prow.addWidget(pl)
        self.price = QDoubleSpinBox()
        self.price.setRange(10, 400)
        self.price.setDecimals(0)
        self.price.setPrefix("$")
        self.price.setMinimumWidth(112)
        self.price.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.price.valueChanged.connect(lambda v: self._set("price", v))
        prow.addWidget(self.price, 1)
        prow.addSpacing(10)
        self.margin = QLabel("—")
        self.margin.setMinimumWidth(70)
        self.margin.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.margin.setStyleSheet(f"color:{T.CYAN}; font-size:12px; font-family:{T.FONT_MONO};")
        prow.addWidget(self.margin)
        strat.add_layout(prow)
        self.tuning = SliderRow("调度 / 提频优化", 0, 1, 0, "{:.0%}",
                                "适度调优合理；过高会拉高官方分、压低实测分，可能被识破。")
        self.tuning.changed.connect(lambda v: self._set("bench_tuning", v))
        strat.add(self.tuning)
        self.isa = SliderRow("跑分 ISA 扩展", 0, 1, 0, "{:.0%}",
                             "为跑分加一些常规应用不用的指令/特化路径：官方分高，实测无收益，且更容易被识破。")
        self.isa.changed.connect(lambda v: self._set("bench_isa", v))
        strat.add(self.isa)
        self.eco = SliderRow("生态适配投入", 0, 1, 0, "{:.0%}",
                             "仅 RISC-V 需要：驱动、兼容层、应用适配。")
        self.eco.changed.connect(lambda v: self._set("eco_invest", v))
        strat.add(self.eco)
        right.addWidget(strat)

        rc = Card("卡住了？")
        rt = QLabel("回架构页降频/砍 L3，或换更大 VC；也可以把跑分优化降回 30% 以内。")
        rt.setWordWrap(True)
        rt.setStyleSheet(f"color:{T.TEXT2}; font-size:10px; line-height:1.65;")
        rc.add(rt)
        right.addWidget(rc)

        self.tape = QPushButton("流片并发布  →")
        self.tape.setObjectName("Primary")
        self.tape.setFixedHeight(46)
        self.tape.clicked.connect(self.win.tape_out)
        right.addWidget(self.tape)
        self.reason = QLabel("")
        self.reason.setWordWrap(True)
        self.reason.setStyleSheet(f"color:{T.RED}; font-size:10px;")
        self.reason.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.reason)
        right.addStretch(1)
        body.addWidget(right_scroll, 2)
        root.addLayout(body, 1)

    def refresh(self):
        if not self.win.design:
            return
        self._loading = True
        self.chip_name.setText(self.win.design.name)
        self.price.setValue(self.win.design.price)
        self.tuning.set_value(self.win.design.bench_tuning)
        self.isa.set_value(self.win.design.bench_isa)
        self.eco.set_value(self.win.design.eco_invest)
        self._loading = False
        self.on_result()

    def _set(self, field, value):
        if self._loading:
            return
        setattr(self.win.design, field, value)
        self.win.request_recompute(force_layout=False)

    def _name(self, value: str):
        if self._loading:
            return
        self.win.design.name = value
        self.win.header.update_state(self.win.result, self.win.scenario)
        self.win.persist()

    def on_result(self):
        r = self.win.result
        if not r:
            return
        y = r["yield_"]
        m = r["market"]
        self.gauge.set_value(y["yield_pct"] * r["bin"]["fraction"], "良率 × bin")
        self.stats["area"].set(f"{r['die_area']:.1f}")
        self.stats["dpw"].set(f"{y['dies_per_wafer']:.0f}")
        self.stats["die"].set(f"${r['cost']['die']:.0f}")
        self.stats["unit"].set(f"${r['cost']['total']:.0f}")

        items = [
            ("Mask", r["nre"]["mask"]), ("IP 授权", r["nre"]["license_core"] + r["nre"]["license_gpu"]
                                        + r["nre"]["license_npu"] + r["nre"]["license_fixed"]),
            ("EDA", r["nre"]["eda"]), ("工程", r["nre"]["engineering"]),
            ("定制实现", r["nre"]["custom"]), ("金属/封装", r["nre"]["metal"]),
            ("生态适配", r["nre"]["eco"]), ("验证", r["nre"]["verification"]),
        ]
        while self.nre_grid.count():
            it = self.nre_grid.takeAt(0)
            w = it.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        for i, (k, v) in enumerate(items):
            a = QLabel(k)
            a.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
            b = QLabel(f"${v:.0f}M")
            b.setStyleSheet(f"color:{T.TEXT2}; font-size:10px; font-family:{T.FONT_MONO};")
            self.nre_grid.addWidget(a, i // 2, (i % 2) * 2)
            self.nre_grid.addWidget(b, i // 2, (i % 2) * 2 + 1)
        self.nre_total.setText(f"合计 ${r['nre']['total']:.0f}M / 预算 ${r['budget']['budget']}M")

        lines = []
        for d in r["bin"]["details"]:
            lines.append(f"{d['core']}: 均值 {d['fmax']:.2f}GHz → 目标 {d['target']:.2f}GHz，可用 {d['fraction']*100:.0f}%")
        self.bin.setText("\n".join(lines) if lines else "—")

        lim = self.win.scenario["limits"]
        checks = [(c["ok"], c["title"]) for c in r["signoff"]["checks"]]
        txt = []
        for ok, name in checks:
            txt.append(("✓ " if ok else "✕ ") + name)
        for e in r["errors"][:4]:
            txt.append("✕ " + e)
        self.checks.setText("\n".join(txt))
        self.checks.setStyleSheet(f"color:{T.GREEN if all(c[0] for c in checks) else T.RED}; font-size:11px; line-height:1.9;")

        self.market.setText(
            f"预判评分 {m['review']:.0f} / 100\n"
            f"目标达成 {m['targets_met']}/{m['targets_total']}\n"
            f"官方 ST {r['perf']['official_st']:.0f} / 实测 {r['perf']['real_st']:.0f}\n"
            f"毛利率 {r['market']['margin']*100:.0f}% · 预计净利 ${m['profit']:.0f}M")
        self.margin.setText(f"毛利 {m['margin']*100:.0f}%")
        if m["review"] >= 92:
            self.quote.setText("“这一代终于把持续性能做上来了。”—— 评测样机反馈")
        elif m["review"] >= 84:
            self.quote.setText("“跑分漂亮，长时间游戏会降频，但总体值得买。”")
        elif m["review"] >= 70:
            self.quote.setText("“参数还行，价格和发热让它很难推荐。”")
        else:
            self.quote.setText("“纸面规格和实际体验对不上。”")
        self.margin.setStyleSheet(f"color:{T.GREEN if m['margin'] > 0.3 else T.AMBER}; font-size:11px; font-family:{T.FONT_MONO};")
        ok = r["signoff"]["ready"]
        self.tape.setEnabled(ok)
        self.badge.setText("READY" if ok else "BLOCKED")
        self.badge.setStyleSheet(f"color:{T.GREEN if ok else T.RED}; font-size:11px; letter-spacing:2px;")
        self.reason.setText("\n".join(c["title"] + "：" + c["remedy"] for c in r["signoff"]["blockers"]))
        self.chip_name.setText(self.win.design.name)
