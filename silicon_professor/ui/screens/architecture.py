"""架构页：制程、CPU 核心组、缓存/总线/内存、GPU/NPU。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QMenu, QPushButton, QScrollArea,
                               QSizePolicy, QSpinBox, QVBoxLayout, QWidget)

from ...data.blocks import DRAMS, GPUS, NPUS, STORAGE, get_gpu, get_npu, get_isp
from ...data.cores import CORES, get_ip
from ...engine.core_bundle import template_catalog
from ...data.tracks import TRACKS, track_of_isa
from ...data.architectures import isa_name
from ...data.nodes import NODES
from ...data.segments import SEGMENTS
from ...engine.types import CoreGroup, Impl
from .. import theme as T
from ..widgets import BarRow, Card, Pill, SectionTitle, Segmented, SliderRow, Stat


def clear_layout(lay):
    while lay.count():
        item = lay.takeAt(0)
        w = item.widget()
        if w:
            w.hide()
            w.setParent(None)
            w.deleteLater()
        elif item.layout():
            clear_layout(item.layout())


class NodeCard(QPushButton):
    def __init__(self, node: dict, allowed: bool, parent=None):
        super().__init__(parent)
        self.node = node
        self.setCheckable(True)
        self.setEnabled(allowed)
        self.setMinimumHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setText(f"{node['name']}\n{node['area_scale']:.2f}× area · ${node['wafer_cost']/1000:.1f}k")
        self.setStyleSheet(
            f"QPushButton {{ text-align:left; padding:7px 10px; font-size:11px; line-height:1.35;"
            f" background:{T.BG2}; border:1px solid {T.BORDER}; border-radius:8px; color:{T.TEXT2}; }}"
            f"QPushButton:hover {{ border-color:{T.BORDER_HI}; }}"
            f"QPushButton:checked {{ border:1px solid {T.CYAN_DIM}; background:{T.rgba(T.CYAN, 0.06)}; color:{T.TEXT}; }}"
            f"QPushButton:disabled {{ color:{T.DIM}; background:{T.BG}; }}")


class ArchitectureScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._loading = True
        self.rows: list[dict] = []

        root = QHBoxLayout(self)
        root.setContentsMargins(26, 18, 22, 18)
        root.setSpacing(16)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        page = QWidget()
        self.left = QVBoxLayout(page)
        self.left.setContentsMargins(0, 0, 8, 0)
        self.left.setSpacing(12)
        self.scroll.setWidget(page)
        self.scroll.setViewportMargins(0, 0, 6, 0)
        root.addWidget(self.scroll, 1)

        self._build_node_card()
        self._build_cpu_card()
        self._build_cache_card()
        self._build_accel_card()
        self.left.addStretch(1)

        # 右侧总览
        side = QVBoxLayout()
        side.setSpacing(10)
        sc = Card("实时评估")
        grid = QGridLayout()
        grid.setSpacing(7)
        self.stats = {}
        for i, (k, title) in enumerate([("st", "单核 ST"), ("mt", "多核 MT"),
                                        ("gpu", "GPU"), ("area", "DIE mm²"),
                                        ("power", "峰值 W"), ("cost", "成本 $")]):
            s = Stat(title)
            self.stats[k] = s
            grid.addWidget(s, i // 2, i % 2)
        sc.add_layout(grid)
        side.addWidget(sc)

        tc = Card("目标进度")
        self.bars = {}
        for k, title, color in [("st", "ST", T.CYAN), ("mt", "MT", T.BLUE),
                                ("gpu", "GPU", T.PINK), ("ai", "AI", T.PURPLE),
                                ("battery_h", "续航 h", T.GREEN)]:
            b = BarRow(title, 0, 1, 1, color=color)
            self.bars[k] = b
            tc.add(b)
        side.addWidget(tc)

        wc = Card("设计检查")
        self.warn = QLabel("—")
        self.warn.setWordWrap(True)
        self.warn.setStyleSheet(f"color:{T.TEXT}; font-size:11px; line-height:1.65;")
        wc.add(self.warn)
        self.budget = QLabel("—")
        self.budget.setWordWrap(True)
        self.budget.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        wc.add(self.budget)
        side.addWidget(wc)
        side.addStretch(1)

        nxt = QPushButton("物理实现  →")
        nxt.setObjectName("Primary")
        nxt.setFixedHeight(38)
        nxt.clicked.connect(lambda: win.go("physical"))
        side.addWidget(nxt)
        side_wrap = QWidget()
        side_wrap.setLayout(side)
        side_wrap.setFixedWidth(340)
        root.addWidget(side_wrap, 0)
        side.setContentsMargins(0, 0, 0, 0)
        self._loading = False

    # ---------- UI builders ----------
    def _build_node_card(self):
        self.node_card = Card("制程", "面积 / 频率 / 晶圆成本 / 良率")
        self.node_grid = QGridLayout()
        self.node_grid.setSpacing(7)
        self.node_card.add_layout(self.node_grid)
        self.node_hint = QLabel("")
        self.node_hint.setObjectName("Muted")
        self.node_hint.setWordWrap(True)
        self.node_card.add(self.node_hint)
        self.left.addWidget(self.node_card)

    def _core_grid(self,layout):
        layout.setContentsMargins(8,6,8,6);layout.setHorizontalSpacing(6)
        layout.setColumnStretch(0,1)
        for column,width in enumerate((66,106,96,116,32),1):layout.setColumnMinimumWidth(column,width)

    def _cpu_head(self):
        head = QGridLayout();self._core_grid(head)
        for column,txt in enumerate(('核心 / 设计类型','实例数','L2容量 / MB','L2共享方式','目标频率 / GHz','删除')):
            l = QLabel(txt)
            l.setStyleSheet(f"color:{T.TEXT2}; font-size:11px;")
            l.setAlignment(Qt.AlignmentFlag.AlignLeft if column==0 else Qt.AlignmentFlag.AlignCenter)
            if column:l.setFixedWidth((66,106,96,116,32)[column-1])
            head.addWidget(l,0,column)
        return head

    def _build_cpu_card(self):
        self.cpu_card = Card("CPU 核心组 · 按指令集赛道独立设计",
                             "Arm / RISC-V / x86 · 模板核心与自己的核心都可组成SoC")
        columns=QLabel('列标题与输入共用宽度。L2在“每核私有”时表示每核容量，“全组共享”时表示整组容量；目标频率0表示自动。小窗口可横向滚动，不能用缩紧标题改变列对应。')
        columns.setWordWrap(True);columns.setObjectName('Muted');self.cpu_card.add(columns)
        self.left.addWidget(self.cpu_card)
        self.arm_card = Card("ARM 阵营", TRACKS["arm"]["tagline"])
        self.arm_card.add_layout(self._cpu_head())
        self.arm_box = QVBoxLayout()
        self.arm_box.setSpacing(6)
        self.arm_card.add_layout(self.arm_box)
        self.arm_add = QPushButton("+ 添加 ARM 核心组")
        self.arm_add.clicked.connect(lambda: self._add_menu("arm"))
        self.arm_card.add(self.arm_add)
        self.left.addWidget(self.arm_card)
        self.rv_card = Card("RISC-V 阵营", TRACKS["riscv"]["tagline"])
        self.rv_card.add_layout(self._cpu_head())
        self.rv_box = QVBoxLayout()
        self.rv_box.setSpacing(6)
        self.rv_card.add_layout(self.rv_box)
        self.rv_add = QPushButton("+ 添加 RISC-V 核心组")
        self.rv_add.clicked.connect(lambda: self._add_menu("riscv"))
        self.rv_card.add(self.rv_add)
        self.rv_eco = QLabel(TRACKS["riscv"]["note"])
        self.rv_eco.setWordWrap(True)
        self.rv_eco.setStyleSheet(f"color:{T.DIM}; font-size:10px; line-height:1.6;")
        self.rv_card.add(self.rv_eco)
        self.left.addWidget(self.rv_card)
        self.x86_card=Card(TRACKS['x86']['name'],TRACKS['x86']['tagline'])
        self.x86_card.add_layout(self._cpu_head())
        self.x86_box=QVBoxLayout()
        self.x86_card.add_layout(self.x86_box)
        x86=QPushButton('+ 添加 x86 核心组')
        x86.clicked.connect(lambda:self._add_menu('x86'))
        self.x86_add=x86
        self.x86_card.add(x86);self.left.addWidget(self.x86_card)
        library=QPushButton('选择已保存 CPU/GPU/NPU/ISP · IP 库')
        library.clicked.connect(lambda:(self.win.go('studio'),self.win.screens['studio'].tabs.setCurrentWidget(self.win.screens['studio'].library_page)))
        self.left.addWidget(library)
        info_card = Card("核心说明", "点核心下拉框查看微架构、IPC、面积与授权")
        self.core_info = QLabel("—")
        self.core_info.setWordWrap(True)
        self.core_info.setStyleSheet(f"color:{T.DIM}; font-size:10px; line-height:1.6;")
        info_card.add(self.core_info)
        self.edit_template=QPushButton('在LAB编辑教学核心')
        self.edit_template.clicked.connect(self._edit_template);info_card.add(self.edit_template)
        self.left.addWidget(info_card)

    def _build_cache_card(self):
        self.cache_card = Card("缓存 / 总线 / 内存", "容量不是越大越好：延迟、面积、功耗都在涨")
        self.l3 = SliderRow("共享 L3 容量", 0, 32, 8, "{:.1f} MB",
                            "L3 喂饱多核，但面积随容量线性增长，延迟也上升。")
        self.cache_card.add(self.l3)
        self.slc = SliderRow("系统级缓存 SLC", 0, 32, 0, "{:.1f} MB",
                             "Apple 式做法：给 GPU/NPU/CPU 共用的大缓存，贵但有效。")
        self.cache_card.add(self.slc)
        row = QHBoxLayout()
        row.setSpacing(10)
        self.l3_shared = QCheckBox("L3 全局共享（否则每簇一份）")
        row.addWidget(self.l3_shared)
        row.addStretch(1)
        self.noc = Segmented([("ring", "环形"), ("mesh", "Mesh"), ("crossbar", "交叉开关")])
        row.addWidget(self.noc)
        self.cache_card.add_layout(row)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        l = QLabel("内存")
        l.setStyleSheet(f"color:{T.TEXT2}; font-size:12px;")
        row2.addWidget(l)
        self.dram = QComboBox()
        for d in DRAMS.values():
            self.dram.addItem(f"{d['name']} · {d['channels']}ch", d["id"])
        row2.addWidget(self.dram, 1)
        self.cache_card.add_layout(row2)
        self.cache_hint = QLabel("")
        self.cache_hint.setObjectName("Muted")
        self.cache_hint.setWordWrap(True)
        self.cache_card.add(self.cache_hint)
        self.left.addWidget(self.cache_card)

        self.l3.changed.connect(lambda v: self._set("l3_mb", v))
        self.slc.changed.connect(lambda v: self._set("slc_mb", v))
        self.l3_shared.toggled.connect(lambda v: self._set("l3_shared", v, force=True))
        self.noc.changed.connect(lambda v: self._set("noc", v, force=True))
        self.dram.currentIndexChanged.connect(
            lambda: self._set("dram", self.dram.currentData(), force=True))

    def _build_accel_card(self):
        self.accel_card = Card("GPU / NPU / 基带", "专用单元决定游戏、AI 与通信体验")
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(QLabel("GPU"), 0, 0)
        self.gpu = QComboBox()
        grid.addWidget(self.gpu, 0, 1)
        self.gpu_units = QSpinBox()
        self.gpu_units.setRange(2, 24)
        self.gpu_units.setToolTip("该 GPU 的单元数量；不同架构的 MC、CU、WGP 不直接等价。")
        grid.addWidget(self.gpu_units, 0, 2)
        grid.addWidget(QLabel("NPU"), 0, 3)
        self.npu = QComboBox()
        for n in NPUS.values():
            self.npu.addItem(f"{n['name']} · {n['tops']}T", n["id"])
        grid.addWidget(self.npu, 0, 4)
        grid.addWidget(QLabel("基带"), 1, 0)
        self.modem = QComboBox()
        self.modem.addItem("5G 集成基带", "modem5g")
        self.modem.addItem("外挂 5G 基带（省 die）", "modem_ext")
        self.modem.addItem("4G 基带", "modem4g")
        grid.addWidget(self.modem, 1, 1)
        grid.addWidget(QLabel("存储"), 2, 0)
        self.storage = QComboBox()
        for st in STORAGE.values():
            self.storage.addItem(f"{st['name']} · 读 {st['seq_read']}GB/s", st["id"])
        grid.addWidget(self.storage, 2, 1)
        self.modem_info = QLabel("—")
        self.modem_info.setWordWrap(True)
        self.modem_info.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        grid.addWidget(self.modem_info, 2, 2, 1, 3)
        self.isp_cb = QCheckBox("ISP")
        self.media_cb = QCheckBox("媒体引擎")
        self.display_cb = QCheckBox("显示")
        row = QHBoxLayout()
        row.addWidget(self.isp_cb)
        row.addWidget(self.media_cb)
        row.addWidget(self.display_cb)
        row.addStretch(1)
        grid.addLayout(row, 1, 2, 1, 3)
        self.accel_card.add_layout(grid)
        self.gpu_info = QLabel("—")
        self.gpu_info.setWordWrap(True)
        self.gpu_info.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        self.accel_card.add(self.gpu_info)
        self.left.addWidget(self.accel_card)

        self.gpu.currentIndexChanged.connect(
            lambda: self._set_gpu())
        self.gpu_units.valueChanged.connect(
            lambda v: (self._set("gpu_units", v, force=True), self._gpu_info()))
        self.npu.currentIndexChanged.connect(self._set_npu)
        self.modem.currentIndexChanged.connect(
            lambda: (self._set("modem_id", self.modem.currentData(), force=True), self._modem_info()))
        self.storage.currentIndexChanged.connect(
            lambda: self._set("storage_id", self.storage.currentData(), force=True))
        self.isp_cb.toggled.connect(lambda v: self._set("isp", v, force=True))
        self.media_cb.toggled.connect(lambda v: self._set("media", v, force=True))
        self.display_cb.toggled.connect(lambda v: self._set("display", v, force=True))

    # ---------- refresh ----------
    def refresh(self):
        if not self.win.design:
            return
        self._loading = True
        d = self.win.design
        seg = self.win.scenario
        allowed = set(seg["allowed_nodes"])

        clear_layout(self.node_grid)
        nodes = [n for n in NODES.values() if n["id"] in allowed or seg["id"] == "sandbox"]
        for i, n in enumerate(nodes):
            b = NodeCard(n, n["id"] in allowed)
            b.setChecked(n["id"] == d.node_id)
            b.clicked.connect(lambda _, nid=n["id"]: self._node(nid))
            self.node_grid.addWidget(b, i // 3, i % 3)
        self.node_hint.setText(f"当前：{NODES[d.node_id]['name']} · {NODES[d.node_id]['note']}")

        self._rebuild_rows()
        if d.cores:
            self._show_core_info(0)
        self.l3.set_value(d.l3_mb)
        self.slc.set_value(d.slc_mb)
        self.l3_shared.setChecked(d.l3_shared)
        self.noc.select(d.noc)
        self.dram.setCurrentIndex(max(0, self.dram.findData(d.dram)))

        self._fill_gpus()
        self.gpu.setCurrentIndex(max(0, self.gpu.findData('ip:'+d.ip_blocks['gpu'] if 'gpu' in d.ip_blocks else d.gpu_id)))
        selected_gpu=get_gpu(d)
        self.gpu_units.setRange(selected_gpu['min_units'],selected_gpu['max_units'])
        self.gpu_units.setValue(d.gpu_units)
        self._gpu_info()
        self.npu.clear()
        for n in template_catalog(d,'npu',NPUS).values():self.npu.addItem(f"{n['name']} · {n['tops']}T",n['id'])
        for record in d.embedded_ips.values():
            if record['kind']=='npu':self.npu.addItem(record['name']+' · 定制IP','ip:'+record['id'])
        self.npu.setCurrentIndex(max(0,self.npu.findData('ip:'+d.ip_blocks['npu'] if 'npu' in d.ip_blocks else d.npu_id)))
        self.npu.setToolTip(get_npu(d).get('note','稠密INT8峰值，每MAC两op。'))
        self.modem.setCurrentIndex(max(0, self.modem.findData(d.modem_id)))
        self.storage.setCurrentIndex(max(0, self.storage.findData(d.storage_id)))
        self._modem_info()
        self.isp_cb.setChecked(d.isp)
        self.isp_cb.setText('ISP · '+get_isp(d)['name'])
        self.media_cb.setChecked(d.media)
        self.display_cb.setChecked(d.display)
        self._loading = False
        self.on_result()

    def _gpu_info(self):
        g = get_gpu(self.win.design)
        if not g:
            return
        cu = g.get("cu_per_unit", 1) * self.win.design.gpu_units
        compat = g.get("compat", 1.0)
        self.gpu_info.setText(
            f"{g['name']}：{self.win.design.gpu_units}×{g['unit_name']} · "
            f"教学驱动适配系数 {compat:.2f}。跨架构的单元数量不直接等价。")

    def _show_core_info(self, idx: int):
        if not self.win.design or idx >= len(self.win.design.cores):
            return
        ip = get_ip(self.win.design, self.win.design.cores[idx].core_id)
        if not ip:
            return
        self.selected_core_index=idx
        self.edit_template.setEnabled('hardware' in ip)
        lic = {"arm": "Arm 授权", "riscv": "RISC-V 授权", "research": "研究档案（不可授权）",
               "custom": "自研"}.get(ip["license"], ip["license"])
        self.core_info.setText(
            f"{ip['name']} · {ip['year']} 年 · {ip['arch']} / {isa_name(ip['isa'])} · "
            f"{ip['decode']} 宽解码 / ROB {ip['rob']} · IPC 指数 {ip['ipc']:.2f}\n"
            f"参考 {ip['ref_node'].upper()}：{ip['fmax_ref']:.2f}GHz · 逻辑面积 {ip['logic_area']:.1f}mm² · "
            f"L2 {ip['l2_default']:g}MB · {lic}\n{ip['note']}")

    def _modem_info(self):
        m = {"modem5g": ("集成 5G：主流选择。", 1.00),
             "modem_ext": ("外挂 5G：信号稳但多一颗芯片的功耗与成本。", 0.97),
             "modem4g": ("4G：便宜省电，但 5G 时代会被差评。", 0.95)}.get(
                 self.win.design.modem_id, ("", 1.0))
        self.modem_info.setText(f"{m[0]} 信号系数 {m[1]:.2f}")

    def _fill_gpus(self):
        self.gpu.blockSignals(True)
        self.gpu.clear()
        d = self.win.design
        sandbox = d and 'research' in self.win.scenario['allowed_licenses']
        year = self.win.scenario["year"]
        for g in template_catalog(d,'gpu',GPUS).values():
            if g["license_cost_m"] is None and not sandbox:
                continue
            if not sandbox and g["year"] > year:
                continue
            self.gpu.addItem(f"{g['name']} · {g['unit_name']}", g["id"])
        for record in d.embedded_ips.values():
            if record['kind']=='gpu':self.gpu.addItem(record['name']+' · 定制IP','ip:'+record['id'])
        self.gpu.blockSignals(False)

    def _rebuild_rows(self):
        clear_layout(self.arm_box)
        clear_layout(self.rv_box)
        clear_layout(self.x86_box)
        self.rows = []
        d = self.win.design
        for i, g in enumerate(d.cores):
            ip = get_ip(self.win.design, g.core_id)
            if not ip:
                continue
            track = track_of_isa(ip.get("isa"))
            box = {'arm':self.arm_box,'riscv':self.rv_box,'x86':self.x86_box}.get(track,self.rv_box)
            row = QFrame()
            row.setObjectName("Panel2")
            row.setStyleSheet(f"QFrame#Panel2 {{ background:{T.BG2}; border:1px solid {T.BORDER}; border-radius:8px; }}")
            lay = QGridLayout(row);self._core_grid(lay)

            combo = QComboBox()
            combo.setMinimumWidth(190)
            sandbox = 'research' in self.win.scenario['allowed_licenses']
            year = self.win.scenario["year"]
            for c in template_catalog(d,'cpu',CORES).values():
                if track_of_isa(c["isa"]) != track:
                    continue
                if c["license"] == "research" and not sandbox:
                    continue
                if not sandbox and c["year"] > year:
                    continue
                combo.addItem(c['name']+' · '+{'little':'精简 / 小核','mid':'均衡核','big':'性能 / 吞吐核'}[c['tier']], c["id"])
                combo.setItemData(combo.count()-1,f"{isa_name(c['isa'])} · {c['year']}\n{c['note']}",Qt.ItemDataRole.ToolTipRole)
            for asset_id,record in d.embedded_ips.items():
                if record['kind']!='cpu':continue
                model=get_ip(d,'ip:'+asset_id)
                if track_of_isa(model['isa'])==track:combo.addItem(model['name']+' · 已保存LAB IP','ip:'+asset_id)
            if sandbox and any(g.core_id == "custom" for g in d.cores):
                combo.addItem("自研核（实验室） · 2026 · ARM/RV  [big]", "custom")
            combo.setCurrentIndex(max(0, combo.findData(g.core_id)))
            lay.addWidget(combo,0,0)

            count = QSpinBox()
            count.setRange(0,256)
            count.setValue(g.count)
            count.setFixedWidth(66);count.setToolTip('本组实例数量；软件布局总上限256，不是真实互连能力保证。')
            count.setAccessibleName('CPU核心组实例数')
            lay.addWidget(count,0,1)

            l2 = QDoubleSpinBox()
            l2.setRange(0,1024)
            l2.setSingleStep(0.128)
            l2.setDecimals(3)
            l2.setValue(g.l2_mb)
            l2.setFixedWidth(106);l2.setToolTip('私有时每核容量；共享时整组容量。单位MB。')
            l2.setAccessibleName('L2缓存容量，单位MB')
            lay.addWidget(l2,0,2)

            shared = QComboBox();shared.addItem('每核私有',False);shared.addItem('全组共享',True)
            shared.setCurrentIndex(1 if g.l2_shared else 0);shared.setFixedWidth(96)
            shared.setAccessibleName('L2缓存共享方式')
            shared.setToolTip("同一组核心共享 L2：省面积，但有交叉开关延迟与争用。")
            lay.addWidget(shared,0,3)

            clk = QDoubleSpinBox()
            clk.setRange(0,100)
            clk.setSingleStep(0.1)
            clk.setDecimals(2)
            clk.setValue(g.clock if g.clock > 0 else 0.0)
            clk.setSpecialValueText("自动")
            clk.setMinimum(0.0)
            clk.setFixedWidth(116);clk.setToolTip('0自动；其它值为目标GHz。高于模型Fmax时诊断分档与频率限制。')
            clk.setAccessibleName('目标频率，单位GHz，0表示自动')
            lay.addWidget(clk,0,4)

            rm = QPushButton("✕")
            rm.setFixedSize(32,32)
            rm.setStyleSheet("padding:0; font-size:13px; color:#ff6b6b;")
            rm.setObjectName("Danger")
            rm.clicked.connect(lambda _, idx=i: self._remove(idx))
            lay.addWidget(rm,0,5)
            box.addWidget(row)

            combo.currentIndexChanged.connect(
                lambda _, idx=i, c=combo: self._core_changed(idx, c.currentData()))
            combo.activated.connect(
                lambda _, idx=i: self._show_core_info(idx))
            count.valueChanged.connect(lambda v, idx=i: self._group(idx, "count", v))
            l2.valueChanged.connect(lambda v, idx=i: self._group(idx, "l2_mb", v, True))
            shared.currentIndexChanged.connect(lambda _, idx=i,c=shared:self._group(idx,"l2_shared",c.currentData(),True))
            clk.valueChanged.connect(lambda v, idx=i: self._group(idx, "clock", v, True))
            self.rows.append(dict(combo=combo, count=count, l2=l2, shared=shared, clock=clk))

    def _add_menu(self, track: str):
        menu=self._make_add_menu(track)
        anchor = {'arm':self.arm_add,'riscv':self.rv_add,'x86':self.x86_add}[track]
        menu.exec(anchor.mapToGlobal(anchor.rect().bottomLeft()))
        menu.deleteLater()

    def _make_add_menu(self,track):
        menu = QMenu(self)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,False)
        sandbox = 'research' in self.win.scenario['allowed_licenses']
        year = self.win.scenario["year"]
        for c in template_catalog(self.win.design,'cpu',CORES).values():
            if track_of_isa(c["isa"]) != track:
                continue
            if c["license"] == "research" and not sandbox:
                continue
            if not sandbox and c["year"] > year:
                continue
            act = menu.addAction(f"{c['name']}  ·  {c['year']}  ·  {isa_name(c['isa'])}")
            act.triggered.connect(lambda _, cid=c["id"]: self._add(cid))
        from ...engine.ip_library import asset_model
        for record in self.win.ip_library.values():
            if record['kind']!='cpu' or track_of_isa(asset_model(record)['isa'])!=track:continue
            act=menu.addAction(record['name']+' · LAB IP')
            act.triggered.connect(lambda _,r=record:self._attach(r))
        if sandbox and track_of_isa(get_ip(self.win.design,'custom')['isa'])==track and not any(g.core_id == "custom" for g in self.win.design.cores):
            act = menu.addAction("自研核（实验室）  ·  custom")
            act.triggered.connect(lambda: self._add("custom"))
        return menu

    def _edit_template(self):
        d=self.win.design;index=getattr(self,'selected_core_index',0)
        if not d or index>=len(d.cores):return
        model=get_ip(d,d.cores[index].core_id)
        if not model or 'hardware' not in model:return
        studio=self.win.screens['studio'];studio.load_template(model);self.win.go('studio')

    # ---------- mutations ----------
    def _attach(self,record):
        from ...engine.ip_library import attach_asset
        try:
            attach_asset(self.win.design,record)
            self.win.recompute_now(force_layout=True)
            self.refresh()
        except ValueError as ex:
            self.warn.setText(str(ex))
    def _node(self, nid: str):
        if self._loading:
            return
        self.win.design.node_id = nid
        self.win.design.placements.clear()
        self.win.request_recompute(force_layout=True)
        self.refresh()

    def _add(self, cid: str):
        ip = get_ip(self.win.design, cid)
        if not ip:
            return
        self.win.design.cores.append(CoreGroup(cid, 2, ip["l2_default"], False, 0.0, Impl()))
        self.win.design.placements.clear()
        self._rebuild_rows()
        self.win.request_recompute(force_layout=True)

    def _remove(self, idx: int):
        if idx < len(self.win.design.cores):
            self.win.design.cores.pop(idx)
            self.win.design.placements.clear()
            self._rebuild_rows()
            self.win.request_recompute(force_layout=True)

    def _core_changed(self, idx: int, cid: str):
        if self._loading or idx >= len(self.win.design.cores):
            return
        g = self.win.design.cores[idx]
        g.core_id = cid
        ip = get_ip(self.win.design, cid)
        if not ip:
            return
        g.l2_mb = ip["l2_default"]
        g.clock = 0.0
        self._show_core_info(idx)
        self.win.design.placements.clear()
        self._rebuild_rows()
        self.win.request_recompute(force_layout=True)

    def _group(self, idx: int, field: str, value, force: bool = False):
        if self._loading or idx >= len(self.win.design.cores):
            return
        setattr(self.win.design.cores[idx], field, value)
        if force:
            self.win.design.placements.clear()
        self.win.request_recompute(force_layout=force)

    def _set(self, field: str, value, force: bool = False):
        if self._loading:
            return
        if field in ('gpu_id','npu_id'):
            self.win.design.ip_blocks.pop('gpu' if field=='gpu_id' else 'npu',None)
        setattr(self.win.design, field, value)
        self.win.request_recompute(force_layout=force)

    def _set_gpu(self):
        if self._loading:
            return
        gid = self.gpu.currentData()
        if not gid:return
        if gid.startswith('ip:'):
            self.win.design.ip_blocks['gpu']=gid[3:]
        else:
            self.win.design.ip_blocks.pop('gpu',None)
            self.win.design.gpu_id=gid
        g=get_gpu(self.win.design)
        self.win.design.gpu_units = g['default_units']
        self.gpu_units.blockSignals(True);self.gpu_units.setRange(g['min_units'],g['max_units'])
        self.gpu_units.setValue(self.win.design.gpu_units)
        self.gpu_units.blockSignals(False)
        self._gpu_info()
        self.win.design.placements.clear()
        self.win.request_recompute(force_layout=True)

    def _set_npu(self,*_):
        if self._loading:return
        ident=self.npu.currentData()
        if not ident:return
        if ident.startswith('ip:'):self.win.design.ip_blocks['npu']=ident[3:]
        else:
            self.win.design.ip_blocks.pop('npu',None)
            self.win.design.npu_id=ident
        self.npu.setToolTip(get_npu(self.win.design).get('note','稠密INT8峰值，每MAC两op。'))
        self.win.request_recompute(force_layout=True)

    # ---------- result ----------
    def on_result(self):
        r = self.win.result
        if not r or not self.rows:
            return
        p = r["perf"]
        vals = {"st": f"{p['st_burst']:.0f}", "mt": f"{p['mt_burst']:.0f}",
                "gpu": f"{p['gpu']:.0f}", "area": f"{r['die_area']:.1f}",
                "power": f"{r['power']['peak']:.1f}", "cost": f"${r['cost']['total']:.0f}"}
        for k, s in self.stats.items():
            s.set(vals.get(k, "—"))
        t = self.win.scenario["targets"]
        bar_vals = {"st": p["st_burst"], "mt": p["mt_burst"], "gpu": p["gpu"],
                    "ai": p["ai"], "battery_h": p["battery_h"]}
        for k, b in self.bars.items():
            val = bar_vals.get(k, 0)
            b.set_values(val, t[k], max(t[k] * 1.5, val * 1.1))
        warnings = r["warnings"][:5]
        self.warn.setText("\n".join("· " + w for w in warnings) if warnings else "当前检查没有新增提示。可继续检查物理实现与工程约束。")
        rem = r["budget"]["remaining"]
        self.budget.setText(f"NRE ${r['nre']['total']:.0f}M / 预算 ${r['budget']['budget']}M · 余 ${rem:.0f}M")
