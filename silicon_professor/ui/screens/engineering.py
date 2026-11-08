"""工程验证工作台：约束、工作负载和方案对照。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget)

from ...engine.engineering import PVT_CORNERS
from .. import theme as T
from ..widgets import Card, SliderRow, Stat


class EngineeringScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._loading = True
        self._baseline = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 24, 20)
        heading = QLabel("工程验证")
        heading.setObjectName("H1")
        outer.addWidget(heading)
        note = QLabel("在目标工作负载和工艺条件下检查设计。所有数值为教学估算；完整签核需要网表、PDK 与实际测试。")
        note.setWordWrap(True)
        note.setObjectName("Dim")
        outer.addWidget(note)
        body = QHBoxLayout()
        body.setSpacing(16)
        outer.addLayout(body, 1)
        self.sliders = {}
        left = self._column(body, 1)
        verify = Card("工艺与供电", "检查角落、验证规划、电源网络")
        self.corner = QComboBox()
        for key, c in PVT_CORNERS.items():
            self.corner.addItem(c["name"], key)
        self.corner.currentIndexChanged.connect(lambda _: self._set("pvt_corner", self.corner.currentData()))
        verify.add(self.corner)
        for field, title, hint in [
            ("verification_effort", "验证投入", "增加 NRE 与验证规划完成度，降低游戏中的缺陷事件风险。"),
            ("pdn_quality", "电源网络投入", "降低估算等效电阻；高峰值电流需要更好的电源网络。"),
        ]:
            self._slider(verify, field, title, 0, 1, "{:.0%}", hint)
        self.corner_result = QLabel()
        self.corner_result.setWordWrap(True)
        self.corner_result.setObjectName("Dim")
        verify.add(self.corner_result)
        left.addWidget(verify)

        memory = Card("内存系统", "x16 通道 · 控制器与外部器件分开计价")
        row = QHBoxLayout()
        row.addWidget(QLabel("通道数"))
        self.channels = QSpinBox()
        self.channels.setRange(0, 8)
        self.channels.setSpecialValueText("按代际默认")
        self.channels.valueChanged.connect(lambda v: self._set("memory_channels", v, True))
        row.addWidget(self.channels)
        row.addWidget(QLabel("DRAM / GB"))
        self.capacity = QSpinBox()
        self.capacity.setRange(2, 64)
        self.capacity.setSingleStep(2)
        self.capacity.valueChanged.connect(lambda v: self._set("memory_gb", v))
        row.addWidget(self.capacity)
        memory.add_layout(row)
        self.memory_result = QLabel()
        self.memory_result.setWordWrap(True)
        self.memory_result.setObjectName("Dim")
        memory.add(self.memory_result)
        left.addWidget(memory)

        workload = Card("工作负载", "Amdahl 并行上限 + Roofline 带宽上限")
        presets = QHBoxLayout()
        for title, values in [("交互", (0.60, 8, 1)), ("编译", (0.92, 48, 4)), ("流式计算", (0.99, 256, 0.25))]:
            b = QPushButton(title)
            b.clicked.connect(lambda _, v=values: self._preset(v))
            presets.addWidget(b)
        workload.add_layout(presets)
        self._slider(workload, "workload_parallel", "可并行比例", 0.10, 0.99, "{:.0%}", "串行部分决定加核心的收益上限。")
        self._slider(workload, "workload_set_mb", "工作集", 1, 512, "{:.0f} MB", "容量比可判断是否放得下，不能直接当作缓存命中率。")
        self._slider(workload, "workload_intensity", "访存运算强度", 0.1, 16, "{:.2f} op/B", "每个 DRAM 字节对应多少抽象运算；低强度负载更依赖带宽。")
        left.addWidget(workload)
        left.addStretch(1)

        right = self._column(body, 1)
        metrics = Card("工作负载结果", "同一任务内比较；不能换算为实际跑分")
        grid = QGridLayout()
        self.stats = {}
        for i, (key, title) in enumerate([
            ("speedup", "并行加速上限"), ("bandwidth", "有效带宽 / GB/s"),
            ("compute", "计算上限 / Gop/s"), ("roof", "带宽上限 / Gop/s"),
            ("ir", "供电压降 / mV"), ("verification", "验证规划完成度"),
        ]):
            s = Stat(title, accent=T.TEXT)
            grid.addWidget(s, i // 2, i % 2)
            self.stats[key] = s
        metrics.add_layout(grid)
        self.bottleneck = QLabel()
        self.bottleneck.setWordWrap(True)
        self.bottleneck.setObjectName("Cyan")
        metrics.add(self.bottleneck)
        right.addWidget(metrics)
        checks = Card("检查结果", "与签核页、流片入口使用相同规则")
        self.checks = QLabel()
        self.checks.setWordWrap(True)
        checks.add(self.checks)
        right.addWidget(checks)
        reference = Card("方案对照")
        self.compare = QLabel("固定一份方案，再修改参数观察变化。")
        self.compare.setWordWrap(True)
        self.compare.setObjectName("Dim")
        reference.add(self.compare)
        pin = QPushButton("将当前方案设为对照")
        pin.clicked.connect(self._pin)
        reference.add(pin)
        right.addWidget(reference)
        scope = Card("还需要哪些真实工程工作？")
        detail = QLabel("RTL 功能验证与形式验证 → 综合与等价检查 → STA / CDC / RDC → DRC / LVS → IR drop / EM → DFT / ATPG → 晶圆测试与可靠性认证。\n\n本页只模拟设计决策和投入，不宣称完成上述检查。角落倍率、80mV 门槛和完成度均为游戏规则，实际门槛由工艺与产品规定。")
        detail.setWordWrap(True)
        detail.setObjectName("Muted")
        scope.add(detail)
        right.addWidget(scope)
        right.addStretch(1)
        nxt = QPushButton("查看签核与成本  →")
        nxt.setObjectName("Primary")
        nxt.clicked.connect(lambda: win.go("signoff"))
        right.addWidget(nxt)
        self._loading = False

    def _column(self, parent, stretch):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)
        scroll.setWidget(page)
        parent.addWidget(scroll, stretch)
        return layout

    def _slider(self, card, field, title, lo, hi, fmt, hint):
        slider = SliderRow(title, lo, hi, lo, fmt, hint)
        slider.changed.connect(lambda v: self._set(field, v))
        self.sliders[field] = slider
        card.add(slider)

    def _set(self, field, value, force=False):
        if self._loading or not self.win.design:
            return
        setattr(self.win.design, field, value)
        self.win.request_recompute(force_layout=force)

    def _preset(self, values):
        for field, value in zip(("workload_parallel", "workload_set_mb", "workload_intensity"), values):
            setattr(self.win.design, field, value)
        self.win.recompute_now()
        self.refresh()

    def _snapshot(self):
        r = self.win.result
        return dict(area=r["die_area"], cost=r["cost"]["total"], nre=r["nre"]["total"],
                    workload=r["engineering"]["workload"]["achievable"])

    def _pin(self):
        self.win.recompute_now()
        self._baseline = (id(self.win.design), self._snapshot())
        self.on_result()

    def refresh(self):
        if not self.win.design:
            return
        self._loading = True
        d = self.win.design
        self.corner.setCurrentIndex(max(0, self.corner.findData(d.pvt_corner)))
        self.channels.setValue(d.memory_channels)
        self.capacity.setValue(d.memory_gb)
        for field, slider in self.sliders.items():
            slider.set_value(getattr(d, field))
        self._loading = False
        self.on_result()

    def on_result(self):
        r = self.win.result
        if not r:
            return
        e = r["engineering"]
        w = e["workload"]
        mem = e["memory"]
        for key, value in dict(speedup=f"{w['amdahl_speedup']:.2f}×", bandwidth=f"{mem['effective_gbs']:.1f}",
                               compute=f"{w['compute_ceiling']:.1f}", roof=f"{w['memory_ceiling']:.1f}",
                               ir=f"{e['ir_drop_v'] * 1000:.0f}", verification=f"{e['verification_completion']:.0%}").items():
            self.stats[key].set(value)
        self.bottleneck.setText(f"当前瓶颈：{w['bottleneck']}。可达到约 {w['achievable']:.1f} Gop/s。\n共享缓存 {w['shared_cache_mb']:g} MB / 工作集 {w['working_set_mb']:g} MB。")
        self.memory_result.setText(f"{mem['data_rate_mts']} MT/s × {mem['width_bits']} bit ÷ 8\n理论 {mem['theoretical_gbs']:.1f} GB/s · 利用率 {mem['efficiency']:.0%}\n整机配套成本 ${r['cost']['platform_total']:.1f}（含外部内存、存储与散热）")
        self.corner_result.setText("\n".join(f"{c['name']}：相对均值裕量 {c['timing_margin']:+.0%}" for c in e["corners"]) + "\n负裕量可选低可用率的高频档位，不等于所有 die 均能达标。")
        self.checks.setText("\n".join(("✓ " if c["ok"] else "× ") + c["title"] + ("\n  " + c["remedy"] if not c["ok"] else "") for c in r["signoff"]["checks"]))
        if self._baseline and self._baseline[0] == id(self.win.design):
            before, now = self._baseline[1], self._snapshot()
            self.compare.setText(f"相对对照：面积 {now['area']-before['area']:+.1f} mm² · 单颗 ${now['cost']-before['cost']:+.1f}\n研发 ${now['nre']-before['nre']:+.1f} M · 任务吞吐 {now['workload']-before['workload']:+.1f} Gop/s")
        else:
            self._baseline = None
            self.compare.setText("固定一份方案，再修改参数观察变化。")
