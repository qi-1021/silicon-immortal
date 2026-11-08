"""实验室与进阶课程：有输入、执行轨迹、独立任务判定和来源范围。"""
from __future__ import annotations

import json
from copy import deepcopy

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QListWidget, QListWidgetItem,
    QPlainTextEdit, QPushButton, QScrollArea, QSpinBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLineEdit)

from ...data.cores import custom_ip
from ...data.lab_courses import COURSES, COURSE_BY_ID, evaluate_course
from ...data.sources import SOURCES, source_text
from ...engine.labs import DEFAULTS, KINDS, json_result, run_experiment
from ...engine.types import CoreGroup
from ...engine.lab_cpu import architectural_state_at
from ...engine.isa import instruction_catalog
from ...data.architectures import ARCHITECTURES,MODES,ISA_OPTIONS
from ...engine.ip_library import make_asset,attach_asset,read_asset,write_asset
from ...version import producer
from .. import theme as T
from ..search import InfoDialog
from ..widgets import Card


NUMBERS = {
    "cpu": [("width","获取/提交宽度",1,12), ("execution_ports","发射端口数",1,12),
        ("rob_size","ROB 项目数",1,1024), ("pipeline","前端/分支填充周期",2,24),
        ("cache_kb","L1D / KiB",1,256), ("hit_latency","命中总延迟 / 周期",1,100),
        ("miss_latency","miss 总延迟 / 周期",1,1000), ("multiply_latency","乘除总延迟 / 周期",1,100)],
    "cache": [("capacity_kb","容量 / KiB",1,256), ("line_bytes","行大小 / B",16,256),
        ("ways","相联度",1,16), ("hit_latency","命中总延迟 / 周期",1,100), ("miss_latency","miss 总延迟 / 周期",1,1000)],
    "network": [("count","端点数",2,64), ("link_latency","链路延迟 / 周期",1,100)],
    "timing": [("clock_ghz","时钟 / GHz",.1,10.0), ("setup_ps","Setup / ps",0.0,1000.0), ("skew_ps","时钟不确定度 / ps",0.0,1000.0)],
    "power": [("capacitance_pf","等效开关电容 / pF",1.0,100000.0), ("activity","活动因子 α",0.0,1.0),
        ("voltage","VDD / V",.1,2.0), ("frequency_ghz","频率 / GHz",.1,10.0), ("leakage_w","恒定漏电 / W",0.0,20.0),
        ("thermal_r","等效热阻 / K·W⁻¹",.1,50.0), ("thermal_c","等效热容 / J·K⁻¹",.1,100.0),
        ("ambient","环境温度 / °C",-20.0,80.0), ("duration","模拟时间 / s",1.0,1000.0)],
    "logic": [("a","输入 A",-2147483648,2147483647), ("b","输入 B",-2147483648,2147483647), ("bits","位宽",1,32)],
    'gpu':[('elements','元素数',1,4096),('warp_size','Warp lanes',4,64),('processors','SIMT处理器',1,64),('bandwidth_gbs','外部带宽 / GB/s',.1,512.0),('frequency_ghz','时钟 / GHz',.1,5.0)],
    'npu':[('m','M 行数',1,64),('n','N 列数',1,64),('k','K 归约长度',1,64),('rows','PE阵列行数',1,64),('cols','PE阵列列数',1,64),('precision_bits','有符号输入精度',8,16),('accumulator_bits','累加器位宽',16,64),('scratchpad_kb','Scratchpad / KiB',1,1024),('bandwidth_gbs','带宽 / GB/s',.1,512.0),('frequency_ghz','时钟 / GHz',.1,5.0)],
    'isp':[('width','图像宽',4,64),('height','图像高',4,64),('black_level','12bit黑电平',0,4095),('gain','增益',.1,8.0),('gamma','Gamma',.1,4.0),('output_bits','输出位宽',8,10),('pixels_per_cycle','像素 / 周期',1,16),('bandwidth_gbs','带宽 / GB/s',.1,128.0),('frequency_ghz','时钟 / GHz',.1,4.0)],
}
CHOICES = {"cache": ("policy", [("lru","LRU"),("fifo","FIFO")]),
           'cpu':('architecture',ISA_OPTIONS),
           'gpu':('task',[('axpy','AXPY / FP32'),('branch','分歧分支 / FP32')]),
           "network": ("topology",[("mesh","Mesh / XY"),("ring","双向 Ring")]),
           "logic": ("op",[("add","加法"),("and","AND"),("xor","XOR"),("or","OR")])}
TEXTS = {"cpu":[("source","原生汇编（RV32用#注释；x86/A64用;注释）",180), ("memory","初始内存：每行 字地址 32bit值；64bit数据由两字组成",60)],
         "cache":[("addresses","字节地址轨迹（空格分隔，支持 0x）",180)],
         "network":[("packets","每行：源端点 目标端点 注入周期",180)],
         "timing":[("delays","各级 tCQ+组合延迟 / ps（空格分隔）",100)]}
LIMITS = {
    "cpu":"执行 RV32I 语义与 M、RV32 Zbb。单 hart、小端、数据内存 64KiB；HALT 为伪指令。时序为无分支推测的动态轨迹调度，访存串行；周期不是真实工艺延迟。",
    "cache":"LRU/FIFO、write-back/write-allocate。3C 分类相对同容量 fully-associative LRU shadow；FIFO 下不是完备的替换策略损失分类。未模拟预取、MSHR、coherence。",
    "network":"单 flit、store-and-forward、无限缓冲、确定性路由与包 ID 仲裁。有向链路每周期接收一个包，无 VC/credit/多 flit 包；不能验证协议死锁。",
    "timing":"按输入路径延迟计算 setup；不执行网表 STA。delay 已含 tCQ，额外加 setup 与时钟不确定度；不检查 hold/OCV/RC。",
    "power":"Pdyn=αCV²f，漏电为恒定输入；单节点热 RC 的阶跃解析解，不保证降压后时序可工作。功率和温度参数不来自代工厂 PDK。",
    "logic":"固定宽度组合 ALU：进位与有符号溢出分别观察。标志是实验输出，RV32I 没有此标志寄存器。没有生成门级网表。",
    'gpu':'逐lane FP32计算与SIMT路径串行；资源时序假设，无真实shader、光栅/纹理或GPU ISA，不把此IP当完整图形GPU。',
    'npu':'有符号INT8/16 GEMM、wrap累加、理想systolic tile；scratchpad和外部带宽约束。非真实TPU/NPU硬件。',
    'isp':'RGGB raw12 → 黑电平/增益 → bilinear demosaic → 幂gamma/量化。缺失通道从邻域同色样本平均，边界缩小邻域；未建模完整相机系统。',
}


class LabsScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.kind = "cpu"
        self.course_id = None
        self.last_result = None
        self.last_inputs = None
        self.controls = {}
        self.editors = {}
        self.ext_checks = {}
        self.parameter_widgets={}
        self.all_parameters=False
        self._building = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22,18,22,18)
        header = QHBoxLayout()
        title = QLabel("LAB · 实验与教学")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)
        studio=QPushButton('返回核心设计 ↗');studio.clicked.connect(lambda:win.go('studio'));header.addWidget(studio)
        self.kind_picker = QComboBox()
        for key,name in KINDS.items(): self.kind_picker.addItem(name,key)
        self.kind_picker.currentIndexChanged.connect(self._kind_changed)
        header.addWidget(self.kind_picker)
        outer.addLayout(header)
        self.mode_note=QLabel()
        self.mode_note.setWordWrap(True);self.mode_note.setObjectName('Muted');outer.addWidget(self.mode_note)

        body = QHBoxLayout()
        body.setSpacing(12)
        outer.addLayout(body,1)
        rail = QVBoxLayout()
        self.courses = QListWidget()
        self.courses.setFixedWidth(205)
        for c in COURSES:
            item = QListWidgetItem(c["title"] + "\n" + KINDS[c["kind"]])
            item.setData(Qt.ItemDataRole.UserRole,c["id"])
            item.setToolTip(c["title"])
            item.setSizeHint(QSize(190,55))
            self.courses.addItem(item)
        self.courses.currentRowChanged.connect(self._select_course)
        rail.addWidget(self.courses,1)
        free = QPushButton("自由实验")
        free.clicked.connect(self._free)
        rail.addWidget(free)
        body.addLayout(rail)

        self.tabs = QTabWidget()
        body.addWidget(self.tabs,1)
        experiment = QWidget()
        expl = QVBoxLayout(experiment)
        expl.setContentsMargins(0,8,0,0)
        self.limit = QLabel()
        self.limit.setWordWrap(True)
        self.limit.setObjectName("Muted")
        expl.addWidget(self.limit)
        split = QSplitter(Qt.Orientation.Horizontal)
        expl.addWidget(split,1)
        input_scroll = QScrollArea()
        input_scroll.setWidgetResizable(True)
        input_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.input_page = QWidget()
        self.input_layout = QVBoxLayout(self.input_page)
        self.input_layout.setContentsMargins(0,0,10,0)
        input_scroll.setWidget(self.input_page)
        split.addWidget(input_scroll)
        output = QWidget()
        outl = QVBoxLayout(output)
        outl.setContentsMargins(8,0,0,0)
        self.goals = QLabel()
        self.goals.setWordWrap(True)
        self.goals.setObjectName("Dim")
        outl.addWidget(self.goals)
        self.summary = QLabel("编辑输入，然后运行实验。")
        self.summary.setWordWrap(True)
        self.summary.setObjectName("Cyan")
        outl.addWidget(self.summary)
        self.results = QTabWidget()
        outl.addWidget(self.results,1)
        replay=QHBoxLayout()
        self.replay_label=QLabel("提交轨迹回放 / 周期")
        self.replay=QSpinBox()
        self.replay.setRange(0,0)
        self.replay.valueChanged.connect(self._replay)
        replay.addWidget(self.replay_label)
        replay.addWidget(self.replay)
        outl.addLayout(replay)
        row = QHBoxLayout()
        self.run_btn = QPushButton("运行实验")
        self.run_btn.setObjectName("Primary")
        self.run_btn.clicked.connect(self.run)
        row.addWidget(self.run_btn)
        self.apply_btn = QPushButton("应用定制核心")
        self.apply_btn.clicked.connect(self._apply)
        row.addWidget(self.apply_btn)
        self.export_btn = QPushButton("导出实验")
        self.export_btn.clicked.connect(self._export)
        row.addWidget(self.export_btn)
        outl.addLayout(row)
        self.apply_note = QLabel()
        self.apply_note.setWordWrap(True)
        self.apply_note.setObjectName("Muted")
        outl.addWidget(self.apply_note)
        split.addWidget(output)
        split.setSizes([430,510])
        self.tabs.addTab(experiment,"实验与轨迹")
        self.guide = QScrollArea()
        self.guide.setWidgetResizable(True)
        guide_page = QWidget()
        guide_l = QVBoxLayout(guide_page)
        self.course_title = QLabel("自由实验")
        self.course_title.setObjectName("H2")
        self.course_title.setWordWrap(True)
        guide_l.addWidget(self.course_title)
        self.lecture = QLabel()
        self.lecture.setWordWrap(True)
        self.lecture.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lecture.setObjectName("Dim")
        guide_l.addWidget(self.lecture)
        self.references = QVBoxLayout()
        guide_l.addLayout(self.references)
        self.solution_btn = QPushButton("查看参考解与解释")
        self.solution_btn.clicked.connect(self._solution)
        guide_l.addWidget(self.solution_btn)
        self.solution_text = QLabel()
        self.solution_text.setWordWrap(True)
        self.solution_text.setObjectName("Dim")
        guide_l.addWidget(self.solution_text)
        self.load_solution = QPushButton("将参考解载入实验")
        self.load_solution.clicked.connect(self._load_solution)
        guide_l.addWidget(self.load_solution)
        next_course=QPushButton('下一节课程 →')
        next_course.clicked.connect(self._next_course);guide_l.addWidget(next_course)
        guide_l.addStretch(1)
        self.guide.setWidget(guide_page)
        self.tabs.addTab(self.guide,"课程讲义与来源")
        catalog=QWidget()
        catl=QVBoxLayout(catalog)
        intro=QLabel("三个可运行子集：RV32I/M/Zbb、x86 IA-32与Arm AArch64。下列指令表列出RV32编码；x86/A64的具体范围见后面的架构卡。所有执行器都从汇编输入运行，没有二进制取指或第三方完整合规认证。RV32 ECALL/EBREAK报告环境异常，HALT是实验终止伪指令。")
        intro.setWordWrap(True);intro.setObjectName("Dim");catl.addWidget(intro)
        for family,instructions in instruction_catalog().items():
            card=Card(f"{family} · {len(instructions)} 条")
            text=QLabel(" · ".join(instructions))
            text.setWordWrap(True);text.setObjectName("Dim");card.add(text)
            catl.addWidget(card)
        for architecture in ('x86_32','aarch64'):
            spec=ARCHITECTURES[architecture]
            card=Card(spec['name'])
            text=QLabel(spec['scope']);text.setWordWrap(True);text.setObjectName('Dim');card.add(text)
            for sid in spec['sources']:
                button=QPushButton('规范与定位：'+SOURCES[sid]['title'])
                button.setProperty('source_id',sid)
                button.clicked.connect(lambda _,s=sid:InfoDialog(self,SOURCES[s]['title'],'原文定位与使用范围',source_text(s)).exec())
                card.add(button)
            catl.addWidget(card)
        unavailable=QLabel("A 原子扩展需要 LR/SC、AMO 和多 hart 内存语义；F/D 需要 IEEE 754 舍入/NaN/异常标志；C 需要16位取指与解码；V 需要 VL/向量寄存器/掩码/向量访存。以上执行语义均尚未实现，不能只勾选功能。\n\nArm ISA 与架构扩展是另外的规范。本 lab 没有执行 Arm NEON/SVE/SME 或 x86 AVX；目录中的芯片模型不代表这些 ISA 已由实验内核支持。")
        unavailable.setWordWrap(True);unavailable.setObjectName("Muted");catl.addWidget(unavailable)
        catl.addStretch(1)
        catalog_scroll=QScrollArea();catalog_scroll.setWidgetResizable(True);catalog_scroll.setWidget(catalog)
        self.tabs.addTab(catalog_scroll,"ISA / 扩展目录")
        self.arch_table=QTableWidget()
        self.arch_table.setColumnCount(4);self.arch_table.setHorizontalHeaderLabels(['架构家族','位宽','执行范围','专业边界'])
        self.arch_table.setRowCount(len(ARCHITECTURES));self.arch_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for i,(key,arch) in enumerate(ARCHITECTURES.items()):
            for j,value in enumerate((arch['name'],arch['width'],'可运行子集' if arch['execution']=='implemented_subset' else '仅历史目录',arch['scope'])):
                item=QTableWidgetItem(value);item.setToolTip(value);self.arch_table.setItem(i,j,item)
        self.arch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.arch_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.arch_table,'历史架构 · 覆盖状态')
        self.library_page=QWidget();lib=QVBoxLayout(self.library_page)
        self.asset_name=QLineEdit();self.asset_name.setMaxLength(64);self.asset_name.setPlaceholderText('给你的CPU/GPU/NPU/ISP命名')
        lib.addWidget(self.asset_name)
        row=QHBoxLayout();self.save_ip=QPushButton('验证并保存当前IP');self.save_ip.clicked.connect(self._save_ip);row.addWidget(self.save_ip)
        import_ip=QPushButton('导入 .cor');import_ip.clicked.connect(self._import_ip);row.addWidget(import_ip);lib.addLayout(row)
        self.library_list=QListWidget();lib.addWidget(self.library_list,1)
        self.library_list.currentRowChanged.connect(self._library_selected)
        row=QHBoxLayout()
        load_ip=QPushButton('载入实验配置');load_ip.clicked.connect(self._load_ip);row.addWidget(load_ip)
        export_ip=QPushButton('导出选中IP');export_ip.clicked.connect(self._export_ip);row.addWidget(export_ip)
        use_ip=QPushButton('在SoC中实例化');use_ip.clicked.connect(self._use_selected);row.addWidget(use_ip);lib.addLayout(row)
        self.replace_cpu=QCheckBox('实例化CPU时替换当前CPU集群（其他IP不受影响）');lib.addWidget(self.replace_cpu)
        self.library_status=QLabel('保存前运行固定验证向量；导入不信任外部评分，重新运行。SoC内嵌IP定义；当前仅研究沙盒支持。')
        self.library_status.setWordWrap(True);self.library_status.setObjectName('Dim');lib.addWidget(self.library_status)
        rtl_note=QLabel('真实RTL：PicoRV32（ISC许可，固定上游提交）。它与本作解析核心模型独立，未将其PPA计入SP分。源码及自检可用于学习。')
        rtl_note.setWordWrap(True);rtl_note.setObjectName('Muted');lib.addWidget(rtl_note)
        rtl_test=QPushButton('运行真实 PicoRV32 RTL 冒烟测试')
        rtl_test.clicked.connect(self._rtl_test);lib.addWidget(rtl_test)
        rtl_sources=QPushButton('查看真实 RTL 源码与许可')
        rtl_sources.clicked.connect(self._rtl_sources);lib.addWidget(rtl_sources)
        self.tabs.addTab(self.library_page,'命名 IP 库')
        self._build_inputs(deepcopy(DEFAULTS["cpu"]))
        self._guide()

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget=item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout(): self._clear(item.layout())

    def _build_inputs(self, inputs):
        self._building = True
        self._clear(self.input_layout)
        self.controls, self.editors, self.ext_checks = {}, {}, {}
        self.parameter_widgets={}
        self.limit.setText(LIMITS[self.kind])
        if self.kind=='cpu':self.limit.setText(ARCHITECTURES[inputs['architecture']]['scope']+'共同时序模型按依赖调度，非真实厂商微架构。')
        card = Card("输入配置")
        if self.kind in CHOICES:
            key, choices = CHOICES[self.kind]
            picker = QComboBox()
            for value,label in choices: picker.addItem(label,value)
            picker.setCurrentIndex(max(0,picker.findData(inputs[key])))
            picker.currentIndexChanged.connect(lambda _:self._architecture_changed(picker.currentData()) if self.kind=='cpu' else self._edited())
            self.controls[key] = picker
            card.add(picker)
        if self.kind == "cpu":
            info = QLabel(ARCHITECTURES[inputs['architecture']]['name']+'：'+ARCHITECTURES[inputs['architecture']]['scope'])
            info.setWordWrap(True)
            info.setObjectName("Muted")
            card.add(info)
            for ext,title in (("M","M 乘除（8 条）"),("Zbb","Zbb 位操作（18 条 RV32 指令）")):
                check=QCheckBox(title)
                check.setChecked(ext in inputs["extensions"])
                check.setEnabled(inputs['architecture']=='riscv32')
                check.setVisible(inputs['architecture']=='riscv32')
                check.toggled.connect(self._edited)
                self.ext_checks[ext]=check
                card.add(check)
            unavailable=QLabel("未实现扩展不产生收益。x86/A64只有列明的整数子集，无SSE/AVX、NEON/SVE/SME。资料与原生语义见架构目录。")
            unavailable.setWordWrap(True)
            unavailable.setObjectName("Muted")
            card.add(unavailable)
        for key,title,height in TEXTS.get(self.kind,[]):
            lab=QLabel(title)
            lab.setWordWrap(True)
            lab.setObjectName("Muted")
            card.add(lab)
            editor=QPlainTextEdit()
            editor.setPlainText(str(inputs[key]))
            editor.setMinimumHeight(height)
            editor.setMaximumHeight(height+80)
            editor.setFont(T.font(12,mono=True))
            editor.textChanged.connect(self._edited)
            card.add(editor)
            self.editors[key]=editor
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(6)
        for i,(key,title,lo,hi) in enumerate(NUMBERS[self.kind]):
            lab=QLabel(title)
            lab.setObjectName("Muted")
            grid.addWidget(lab,(i//2)*2,i%2)
            integer=isinstance(lo,int) and isinstance(hi,int)
            control=QSpinBox() if integer else QDoubleSpinBox()
            control.setRange(lo,hi)
            if not integer:
                control.setDecimals(3)
                control.setSingleStep(.1)
            control.setValue(inputs[key])
            control.setAccessibleName(title)
            control.valueChanged.connect(self._edited)
            grid.addWidget(control,(i//2)*2+1,i%2)
            self.controls[key]=control
            self.parameter_widgets[key]=(lab,control)
        card.add_layout(grid)
        expand=QPushButton('展开/折叠全部资源参数')
        expand.clicked.connect(self._toggle_parameters);card.add(expand)
        self.input_layout.addWidget(card)
        self.input_layout.addStretch(1)
        self._building=False
        self.last_result = self.last_inputs = None
        self._empty_results()
        self.summary.setText("输入已载入，等待运行。")
        self._status()
        self.set_learning_mode()

    def _architecture_changed(self,architecture):
        if self._building:return
        p=self.inputs()
        samples={'riscv32':'ADDI x1,x0,42\nHALT','x86_32':'MOV EAX,42\nHALT','aarch64':'MOV X0,#42\nHALT'}
        p.update(source=samples[architecture],memory='',architecture=architecture,extensions=['M'] if architecture=='riscv32' else [])
        self.course_id=None
        self._build_inputs(p);self._guide()

    def _toggle_parameters(self):
        self.all_parameters=not self.all_parameters;self.set_learning_mode()

    def set_learning_mode(self):
        mode=MODES[self.win.learning_mode];level=mode['level']
        self.mode_note.setText(mode['name']+' · '+mode['description']+' 参数折叠不改变其值。推荐先读讲义 → 运行初始输入 → 修改一项 → 比较轨迹 → 验证后保存IP。')
        basic={'width','elements','task','m','n','k','width','height','black_level','gain','op','a','b','bits','count','clock_ghz'}
        middle=basic|{'execution_ports','cache_kb','capacity_kb','ways','bandwidth_gbs','frequency_ghz','processors','rows','cols','gamma','pixels_per_cycle'}
        for field,widgets in self.parameter_widgets.items():
            visible=self.all_parameters or level>=2 or field in (middle if level==1 else basic)
            for widget in widgets:widget.setVisible(visible)

    def inputs(self):
        data=deepcopy(DEFAULTS[self.kind])
        for key,editor in self.editors.items(): data[key]=editor.toPlainText()
        for key,control in self.controls.items():
            data[key]=control.currentData() if isinstance(control,QComboBox) else control.value()
        if self.kind == "cpu": data["extensions"]=[e for e,c in self.ext_checks.items() if c.isChecked()]
        return data

    def _edited(self, *_):
        if self._building:return
        self.summary.setText("输入已修改；当前结果已失效，请重新运行。")
        self.last_result = self.last_inputs = None
        self.win.lab_workspace.setdefault("drafts",{})[self.kind]=self.inputs()
        self.win.persist()
        self._empty_results()
        self._status()

    def _kind_changed(self, *_):
        if self._building:return
        self.course_id=None
        self.kind=self.kind_picker.currentData()
        self.courses.blockSignals(True)
        self.courses.setCurrentRow(-1)
        self.courses.blockSignals(False)
        inputs=self.win.lab_workspace.get("drafts",{}).get(self.kind,DEFAULTS[self.kind])
        self._build_inputs(deepcopy(inputs))
        self._guide()
        self.tabs.setCurrentIndex(0)

    def restore_workspace(self):
        """恢复自己的草稿；额外字段不传给实验内核，损坏字段沿用默认。"""
        workspace=self.win.lab_workspace
        drafts=workspace.get('drafts',{}) if isinstance(workspace,dict) else {}
        if not isinstance(drafts,dict):drafts={}
        cleaned={}
        for kind,default in DEFAULTS.items():
            original=drafts.get(kind,{})
            if not isinstance(original,dict):continue
            values=deepcopy(default)
            for key,value in original.items():
                if key not in default:continue
                expected=default[key]
                if isinstance(expected,str) and isinstance(value,str) and len(value)<=100000:values[key]=value
                elif isinstance(expected,list) and isinstance(value,list):values[key]=[v for v in value if v in ('M','Zbb')]
                elif type(value) in (int,float) and type(expected) in (int,float):
                    import math
                    if math.isfinite(value):values[key]=type(expected)(value)
            cleaned[kind]=values
        self.win.lab_workspace={'drafts':cleaned}
        self._build_inputs(deepcopy(cleaned.get('cpu',DEFAULTS['cpu'])))
        self._refresh_library()

    def _select_course(self, row):
        if row<0:return
        self.select_course(self.courses.item(row).data(Qt.ItemDataRole.UserRole))

    def select_course(self, cid):
        c=COURSE_BY_ID[cid]
        self.course_id,self.kind=cid,c["kind"]
        self.kind_picker.blockSignals(True)
        self.kind_picker.setCurrentIndex(self.kind_picker.findData(self.kind))
        self.kind_picker.blockSignals(False)
        self._build_inputs(deepcopy(c["initial"]))
        self._guide()
        self.tabs.setCurrentIndex(1)

    def _free(self):
        self.course_id=None
        self.courses.blockSignals(True);self.courses.setCurrentRow(-1);self.courses.blockSignals(False)
        self._guide()
        self._status()
        self.tabs.setCurrentIndex(0)

    def _guide(self):
        self._clear(self.references)
        c=COURSE_BY_ID.get(self.course_id)
        self.course_title.setText(c["title"] if c else "自由实验 · 方法与边界")
        self.lecture.setText(c["lecture"] if c else LIMITS[self.kind] + "\n\n运行结果可导出配置与轨迹；定制核心应用仅限研究沙盒。其它实验不自动修改芯片模型中的延迟或功耗参数。")
        self.solution_text.clear()
        for button in (self.solution_btn,self.load_solution):button.setVisible(c is not None)
        if c:
            prerequisites="、".join(COURSE_BY_ID[x]["title"] for x in c["prerequisites"])
            if prerequisites:
                label=QLabel("先修建议："+prerequisites);label.setWordWrap(True);label.setObjectName("Muted")
                self.references.addWidget(label)
            for sid in c["sources"]:
                s=SOURCES[sid]
                b=QPushButton(s["title"])
                b.setToolTip(s["locator"])
                b.clicked.connect(lambda _,key=sid:InfoDialog(self,SOURCES[key]["title"],"原文定位与使用范围",source_text(key)).exec())
                self.references.addWidget(b)
                scope=QLabel(s["locator"]+"\n本实验引用范围："+s["model_use"])
                scope.setWordWrap(True);scope.setObjectName("Muted");self.references.addWidget(scope)

    def _solution(self):
        if self.course_id:
            c=COURSE_BY_ID[self.course_id]
            self.solution_text.setText(c["explanation"] + "\n\n参考输入：\n"+json.dumps(c["solution"],ensure_ascii=False,indent=2))

    def _load_solution(self):
        if self.course_id:
            self._build_inputs(deepcopy(COURSE_BY_ID[self.course_id]["solution"]))
            self.tabs.setCurrentIndex(0)

    def _next_course(self):
        if not self.course_id:self.select_course(COURSES[0]['id']);return
        index=next(i for i,c in enumerate(COURSES) if c['id']==self.course_id)
        self.select_course(COURSES[min(index+1,len(COURSES)-1)]['id'])

    def _empty_results(self):
        while self.results.count():
            widget=self.results.widget(0)
            self.results.removeTab(0)
            widget.deleteLater()

    def _table(self, name, columns, rows):
        table=QTableWidget()
        table.setColumnCount(len(columns));table.setHorizontalHeaderLabels(columns)
        table.setRowCount(min(1500,len(rows)))
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        for i,row in enumerate(rows[:1500]):
            for j,v in enumerate(row):table.setItem(i,j,QTableWidgetItem(str(v)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.setToolTip("界面最多显示 1500 行；导出保留完整记录。")
        self.results.addTab(table,name)
        return table

    def run(self):
        inputs=self.inputs()
        try:
            result=run_experiment(self.kind,inputs)
        except (ValueError,TypeError,KeyError,OverflowError) as ex:
            self.last_result=self.last_inputs=None
            self._empty_results()
            self.summary.setText("实验未完成："+str(ex))
            self.summary.setObjectName("Red")
            self.summary.setStyleSheet(f"color:{T.RED};")
            self._status()
            return
        self.last_result,self.last_inputs=result,deepcopy(inputs)
        self.summary.setStyleSheet(f"color:{T.CYAN};")
        self._empty_results()
        r=result
        if self.kind == "cpu":
            self.summary.setText(f"{r['instructions']} 指令 / {r['cycles']} 周期 · IPC {r['ipc']:.3f}\nCache hit {r['cache']['hit_rate']:.1%} · 按序提交状态与顺序解释器一致（内部自检）。")
            bits=r['register_bits'];sign=1<<(bits-1);mod=1<<bits
            self.register_table=self._table("寄存器",["寄存器","HEX","unsigned","signed"],[(r['register_names'][i],f"0x{v:0{bits//4}x}",v,v if v<sign else v-mod) for i,v in enumerate(r["registers"])])
            self._table("原生编码/表示",["PC","指令","编码"],[(f"0x{x['pc']:04x}",x["text"],x.get('bytes') or (f"0x{x['word']:08x}" if x["word"] is not None else "伪指令/未覆盖编码")) for x in r["listing"]])
            self._table("执行时序",["#","PC","指令","获取","发射","完成","提交","依赖"],[(x["id"],x["pc"],x["instruction"].text,x["dispatch"],x["issue"],x["done"],x["retire"],",".join(str(d) for d in sorted(x["deps"]))) for x in r["rows"]])
            self._table("数据内存",["字地址","值"],[(f"0x{a:04x}",f"0x{v:08x}") for a,v in sorted(r["memory"].items())])
            self.replay.blockSignals(True);self.replay.setRange(0,r['cycles']);self.replay.setValue(r['cycles']);self.replay.blockSignals(False)
        elif self.kind == "cache":
            self.summary.setText(f"{r['hits']} hit / {r['misses']} miss · 命中率 {r['hit_rate']:.1%}\nAMAT {r['amat']:.2f} 周期 · 串行 {r['serial_cycles']} 周期 · 写回 {r['writebacks']} 次\n3C：{r['miss_types']}")
            self._table("访问轨迹",["地址","Set","Tag","Hit","Miss 类别"],[(hex(x["address"]),x["set"],x["tag"],x["hit"],x["miss_type"] or "—") for x in r["rows"]])
        elif self.kind == "network":
            self.summary.setText(f"平均延迟 {r['avg_latency']:.2f} 周期 · 最长 {r['max_latency']} 周期\n链路跳数 {r['hops']} · 排队等待 {r['queue_wait']} 包·周期")
            self._table("包路由",["包","源→目标","路径","注入","到达","等待"],[(x["id"],f"{x['src']}→{x['dst']}","→".join(map(str,x["route"])),x["injection"],x["arrival"],x["waits"]) for x in r["packets"]])
            self._table("链路轨迹",["周期","包","源","目标"],[(x["cycle"],x["packet"],x["src"],x["dst"]) for x in r["timeline"]])
        elif self.kind == "timing":
            self.summary.setText(f"周期 {r['period_ps']:.1f} ps · WNS {r['wns']:+.1f} ps\n给定路径的 Fmax {r['fmax_ghz']:.3f} GHz · Setup {'满足' if r['setup_met'] else '不满足'}")
            self._table("逐级检查",["级","delay / ps","required / ps","slack / ps"],[(x["stage"],x["delay"],x["required"],x["slack"]) for x in r["rows"]])
        elif self.kind == "power":
            self.summary.setText(f"动态 {r['dynamic_w']:.3f} W / 总功率 {r['total_w']:.3f} W\n时间常数 {r['tau_s']:.2f} s · 稳态 {r['steady_c']:.2f}°C · 末态 {r['final_c']:.2f}°C")
            self._table("热 RC 解析轨迹",["时间 / s","温度 / °C"],[(f"{t:.2f}",f"{v:.3f}") for t,v in r["points"]])
        elif self.kind=='gpu':
            self.summary.setText(f"{r['operations']} FP32 ops · {r['cycles']} 假设周期 · 分歧warp {r['divergence']}\n计算 {r['compute_cycles']} + 传输 {r['transfer_cycles']}，不重叠。逐lane功能检查：{r['functional_check']}")
            self._table('Warp调度',['warp','lanes','真路径','假路径','处理器','开始','完成'],[(w['warp'],w['active_lanes'],w['true_lanes'],w['false_lanes'],w['processor'],w['start'],w['finish']) for w in r['warps']])
            self._table('逐lane输出',['lane','x','y','out'],[(i,r['input_x'][i],r['input_y'][i],value) for i,value in enumerate(r['output'])])
        elif self.kind=='npu':
            self.summary.setText(f"{r['macs']} MAC · {r['cycles']} 假设周期 · INT溢出 {r['overflow_count']}\nTile需 {r['scratchpad_bytes']} B，scratchpad {'满足' if r['scratchpad_fits'] else '不足'}。功能检查：{r['functional_check']}")
            self._table('矩阵结果',['row','col','准确整数','累加器结果'],[(i,j,r['exact'][i][j],v) for i,row in enumerate(r['output']) for j,v in enumerate(row)])
            self._table('阵列Tile',['行','列','rows','cols','周期','local B'],[(t['row'],t['col'],t['rows'],t['cols'],t['compute_cycles'],t['scratchpad_bytes']) for t in r['tiles']])
        elif self.kind=='isp':
            self.summary.setText(f"{r['pixels']} 像素 · {r['cycles']} 假设周期 · 行缓存 {r['line_buffer_bytes']} B\nraw12 / RGGB → RGB{inputs['output_bits']} · 输出范围检查：{r['functional_check']}")
            self._table('Raw与RGB',['y','x','raw','R','G','B'],[(y,x,r['input_raw'][y][x],*rgb) for y,row in enumerate(r['output']) for x,rgb in enumerate(row)])
            from PySide6.QtGui import QImage,QPixmap,QColor
            img=QImage(inputs['width'],inputs['height'],QImage.Format.Format_RGB32)
            scale=255/((1<<inputs['output_bits'])-1)
            for y,row in enumerate(r['output']):
                for x,rgb in enumerate(row):img.setPixelColor(x,y,QColor(*[round(v*scale) for v in rgb]))
            picture=QLabel();picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
            picture.setPixmap(QPixmap.fromImage(img.scaled(400,400,Qt.AspectRatioMode.KeepAspectRatio)))
            self.results.addTab(picture,'输出图像')
        else:
            self.summary.setText(f"结果 {r['result']} / signed {r['signed']}\n二进制 {r['binary']} · Carry {r['carry']} / Overflow {r['overflow']}")
            self._table("ALU",["输入 A","输入 B","结果","进位","有符号溢出"],[(r["a"],r["b"],r["result"],r["carry"],r["overflow"])])
        if self.course_id:
            c=COURSE_BY_ID[self.course_id]
            if all(evaluate_course(c,inputs,r)):
                self.win.progress.setdefault("lab_courses",{})[self.course_id]=True
        self.win.lab_workspace.setdefault("drafts",{})[self.kind]=deepcopy(inputs)
        self.win.persist()
        self._status()

    def _status(self):
        c=COURSE_BY_ID.get(self.course_id)
        if c:
            passed=evaluate_course(c,self.last_inputs,self.last_result) if self.last_result else [False]*len(c["goals"])
            self.goals.setText("\n".join(("✓ " if ok else "○ ")+g["label"] for ok,g in zip(passed,c["goals"])))
        else:self.goals.setText("自由实验：用同一份输入比较资源配置，导出完整轨迹。")
        self.export_btn.setEnabled(self.last_result is not None)
        self.replay.setVisible(self.kind=='cpu')
        self.replay_label.setVisible(self.kind=='cpu')
        self.replay.setEnabled(self.kind=='cpu' and self.last_result is not None)
        can_apply=self.kind in ('cpu','gpu','npu','isp') and self.last_result is not None and self.win.design is not None and self.win.design.scenario_id=="sandbox"
        self.apply_btn.setVisible(self.kind in ('cpu','gpu','npu','isp'))
        self.apply_btn.setEnabled(can_apply)
        self.save_ip.setEnabled(self.kind in ('cpu','gpu','npu','isp') and self.last_result is not None)
        self.apply_btn.setText('保存并实例化IP')
        self.apply_note.setText('在「命名IP库」输入名称，验证后保存/导入导出；SoC内嵌定义。CPU跨ISA替换须显式选择，其他IP直接实例化。PPA为假设。')

    def _apply(self):
        if not self.apply_btn.isEnabled():return
        asset=self._save_ip()
        if asset:self._instantiate(asset)

    def _save_ip(self):
        if self.last_result is None or self.kind not in ('cpu','gpu','npu','isp'):return None
        try:
            name=self.asset_name.text().strip() or ('LAB '+(ARCHITECTURES[self.last_inputs['architecture']]['name'] if self.kind=='cpu' else self.kind.upper()))
            asset=make_asset(self.kind,name,self.last_inputs)
            if asset['id'] not in self.win.ip_library and len(self.win.ip_library)>=64:raise ValueError('本地IP库最多64个版本。')
            self.win.ip_library[asset['id']]=asset;self.win.persist();self._refresh_library(asset['id'])
            self.library_status.setText(f"已保存 {name} · {asset['id'][:8]} · 固定验证：{', '.join(asset['verification']['checks'])}\n这是模型检查，不是RTL验证或量产认证。")
            return asset
        except (ValueError,TypeError,KeyError) as ex:
            self.library_status.setText('IP未保存：'+str(ex));self.tabs.setCurrentWidget(self.library_page);return None

    def _refresh_library(self,selected=None):
        if selected is None and self.library_list.currentItem():selected=self.library_list.currentItem().data(Qt.ItemDataRole.UserRole)
        self.library_list.blockSignals(True);self.library_list.clear()
        for record in self.win.ip_library.values():
            arch=record['config'].get('architecture',record['kind'])
            item=QListWidgetItem(f"{record['name']} · {record['kind'].upper()} / {arch}\n{record['id'][:12]} · 验证向量通过")
            item.setData(Qt.ItemDataRole.UserRole,record['id']);self.library_list.addItem(item)
            if record['id']==selected:self.library_list.setCurrentItem(item)
        self.library_list.blockSignals(False)
        self.library_list.setToolTip('选中后载入/导出/实例化；完整名称与验证范围见下方说明。')

    def _selected_asset(self):
        item=self.library_list.currentItem()
        return self.win.ip_library.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _library_selected(self,*_):
        record=self._selected_asset()
        if record:self.library_status.setText(f"{record['name']} · 版本 {record['digest'][:12]}\n{record['verification']['scope']}\n重新导入会校验摘要并重跑固定向量；附带分数不被信任。")

    def _load_ip(self):
        record=self._selected_asset()
        if not record:return
        if 'design' in record:
            try:
                self.win.screens['studio'].load_asset(record);self.win.go('studio')
            except ValueError as ex:self.library_status.setText(str(ex))
            return
        self.kind=record['kind'];self.course_id=None
        self.kind_picker.blockSignals(True);self.kind_picker.setCurrentIndex(self.kind_picker.findData(self.kind));self.kind_picker.blockSignals(False)
        self.asset_name.setText(record['name'])
        config=dict(deepcopy(DEFAULTS[self.kind]),**{k:v for k,v in record['config'].items() if k in DEFAULTS[self.kind]})
        self._build_inputs(config);self._guide();self.tabs.setCurrentIndex(0)

    def _import_path(self,path):
        record=read_asset(path)
        if record['id'] not in self.win.ip_library and len(self.win.ip_library)>=64:raise ValueError('IP库已满64项。')
        self.win.ip_library[record['id']]=record;self.win.persist();self._refresh_library(record['id']);return record

    def _import_ip(self):
        path,_=QFileDialog.getOpenFileName(self,'导入实验IP','','Silicon Core/IP (*.cor *.spip.json *.json)')
        if not path:return
        try:
            record=self._import_path(path);self.library_status.setText('已导入并重新验证：'+record['name'])
        except (OSError,ValueError,TypeError,KeyError) as ex:self.library_status.setText('导入失败：'+str(ex))

    def _export_ip(self):
        record=self._selected_asset()
        if not record:return
        path,_=QFileDialog.getSaveFileName(self,'导出命名IP','exports/'+record['id']+'.cor','Silicon Core/IP (*.cor)')
        if not path:return
        try:write_asset(path,record);self.library_status.setText('已导出：'+record['name'])
        except (OSError,ValueError) as ex:self.library_status.setText('导出失败：'+str(ex))

    def _instantiate(self,record):
        if not self.win.design or self.win.design.scenario_id!='sandbox':
            self.library_status.setText('先从项目首页进入研究沙盒，再实例化实验IP。');self.tabs.setCurrentWidget(self.library_page);return
        previous=self.win.design.cores
        try:
            if record['kind']=='cpu' and self.replace_cpu.isChecked():self.win.design.cores=[]
            attach_asset(self.win.design,record)
            self.win.recompute_now(force_layout=True)
            self.library_status.setText('已实例化 '+record['name']+'；可在架构/布局/签核页查看。SoC导出会包含完整IP定义。')
            self.apply_note.setText('已实例化：'+record['name'])
        except ValueError as ex:
            self.win.design.cores=previous;self.library_status.setText('未实例化：'+str(ex));self.tabs.setCurrentWidget(self.library_page)

    def _use_selected(self):
        record=self._selected_asset()
        if record:self._instantiate(record)

    def _rtl_sources(self):
        from ...engine.rtl import BUNDLE,rtl_info
        info=rtl_info()
        text=f"PicoRV32 · {info['revision']}\n{info['repository']}\n\n"+(BUNDLE/'INTEGRATION.md').read_text('utf-8')+'\n\n'+(BUNDLE/'COPYING').read_text('utf-8')+'\n\n'+(BUNDLE/'picorv32.v').read_text('utf-8')
        InfoDialog(self,'真实PicoRV32 RTL','源码未改动；ISC许可；独立于解析模型',text).exec()

    def _rtl_test(self):
        from ...engine.rtl import test_picorv32
        result=test_picorv32()
        self.library_status.setText('真实RTL测试：'+result['status']+'\n'+result['reason']+'\n只测ADDI/ADDI/SW，不是完整ISA/时序签核。')

    def _replay(self,cycle):
        if self.kind!='cpu' or self.last_result is None:return
        state=architectural_state_at(self.last_result,cycle)
        bits=self.last_result['register_bits'];sign=1<<(bits-1);mod=1<<bits
        for i,v in enumerate(state['registers']):
            for j,text in enumerate((self.last_result['register_names'][i],f"0x{v:0{bits//4}x}",str(v),str(v if v<sign else v-mod))):
                self.register_table.item(i,j).setText(text)
        self.replay_label.setText(f"提交轨迹回放 · 已提交 {state['retired']} / 周期")

    def _export(self):
        if self.last_result is None:return
        path,_=QFileDialog.getSaveFileName(self,"导出实验记录","exports/lab.json","JSON (*.json)")
        if not path:return
        try:
            from pathlib import Path
            p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(dict(format="silicon-professor/lab",version=1,kind=self.kind,
                producer=producer(),
                course=self.course_id,inputs=self.last_inputs,result=json_result(self.last_result),
                boundaries=LIMITS[self.kind]),ensure_ascii=False,indent=2))
        except OSError as ex:self.summary.setText("导出失败："+str(ex))

    def refresh(self):
        self._status()
        self._refresh_library()
        self.set_learning_mode()

    def on_result(self):
        # 芯片重算不会使独立 lab 输入失效。
        self._status()
