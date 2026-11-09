"""核心设计工作室：硬件草稿→结构/测试→验证发布→IP复用。"""
from copy import deepcopy
import json
import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPixmap
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QComboBox,QListWidget,QListWidgetItem,QTabWidget,QScrollArea,QCheckBox,
    QSpinBox,QDoubleSpinBox,QPlainTextEdit,QFormLayout,QSplitter,QTableWidget,
    QTableWidgetItem,QHeaderView,QFileDialog)

from ...data.core_designs import KINDS,FIELDS,BENCH_FIELDS,default_hardware,default_bench
from ...data.architectures import MODES
from ...engine.core_studio import (SCHEMA,validate_hardware,structure,run_design,
    verify_design,design_model,hardware_from_legacy,hardware_from_template,cpu_performance_report)
from ...engine.core_performance import performance_cases
from ...engine.ip_library import make_design_asset,read_asset,write_asset,attach_asset
from ..core_graph import CoreGraph
from ..observatory import ExecutionObserver
from ..widgets import Card
from .. import theme as T


class StudioScreen(QWidget):
    def __init__(self,win):
        super().__init__();self.win=win;self.current=None;self._loading=True
        self.controls={};self.bench_controls={};self.groups={};self.fields={}
        self.verification=None;self.last_result=None;self.selected_module=None;self.expanded=False
        self.last_performance=None;self.performance_baseline=None;self.observer=None
        outer=QVBoxLayout(self);outer.setContentsMargins(22,18,22,18);outer.setSpacing(12)
        heading=QHBoxLayout()
        title=QLabel('LAB · 核心设计');title.setObjectName('H2');heading.addWidget(title)
        heading.addStretch(1)
        help_button=QPushButton('实验与教学 ↗');help_button.clicked.connect(lambda:win.go('labs'));heading.addWidget(help_button)
        outer.addLayout(heading)
        description=QLabel('设计硬件结构，使用测试台验证，再发布为可复用 IP。CPU / GPU / NPU / ISP 的定义和测试输入分别保存。')
        description.setWordWrap(True);description.setObjectName('Dim');outer.addWidget(description)
        body=QHBoxLayout();body.setSpacing(14);outer.addLayout(body,1)
        rail=QVBoxLayout();rail.setSpacing(8)
        label=QLabel('我的设计');label.setObjectName('H3');rail.addWidget(label)
        self.new_kind=QComboBox()
        for key,title in KINDS.items():self.new_kind.addItem(title,key)
        rail.addWidget(self.new_kind)
        create=QPushButton('+ 新建设计');create.clicked.connect(lambda:self.new_design(self.new_kind.currentData()));rail.addWidget(create)
        self.drafts=QListWidget();self.drafts.setFixedWidth(174)
        self.drafts.currentRowChanged.connect(self._select_draft);rail.addWidget(self.drafts,1)
        duplicate=QPushButton('复制为新设计');duplicate.clicked.connect(self.duplicate);rail.addWidget(duplicate)
        import_button=QPushButton('导入 .cor');import_button.clicked.connect(self.import_dialog);rail.addWidget(import_button)
        library=QPushButton('已发布 IP 库');library.clicked.connect(lambda:self.tabs.setCurrentWidget(self.library_page));rail.addWidget(library)
        body.addLayout(rail)
        workspace=QVBoxLayout();workspace.setSpacing(10);body.addLayout(workspace,1)
        identity=QHBoxLayout()
        self.name_edit=QLineEdit();self.name_edit.setMaxLength(64);self.name_edit.setPlaceholderText('命名核心设计')
        self.name_edit.textChanged.connect(self._rename);identity.addWidget(self.name_edit,1)
        self.kind_label=QLabel();self.kind_label.setObjectName('Cyan');identity.addWidget(self.kind_label)
        self.draft_status=QLabel('草稿');self.draft_status.setObjectName('Muted');identity.addWidget(self.draft_status)
        workspace.addLayout(identity)
        self.tabs=QTabWidget();workspace.addWidget(self.tabs,1)
        self.design_page=QWidget();design_layout=QVBoxLayout(self.design_page);design_layout.setContentsMargins(0,8,0,0)
        self.metrics=QLabel();self.metrics.setWordWrap(True);self.metrics.setObjectName('Dim');design_layout.addWidget(self.metrics)
        split=QSplitter(Qt.Orientation.Horizontal);design_layout.addWidget(split,1)
        self.graph=CoreGraph();self.graph.module_selected.connect(self._select_module)
        graph_scroll=QScrollArea();graph_scroll.setWidgetResizable(True);graph_scroll.setWidget(self.graph);split.addWidget(graph_scroll)
        self.inspector_scroll=QScrollArea();self.inspector_scroll.setWidgetResizable(True)
        self.inspector_scroll.setMinimumWidth(265)
        self.inspector=QWidget();self.inspector_layout=QVBoxLayout(self.inspector)
        self.inspector_layout.setContentsMargins(8,0,4,0)
        self.inspector_scroll.setWidget(self.inspector);split.addWidget(self.inspector_scroll);split.setSizes([600,315])
        self.tabs.addTab(self.design_page,'硬件结构')

        self.validation_page=QWidget();validation=QVBoxLayout(self.validation_page);validation.setContentsMargins(0,8,0,0)
        self.validation_note=QLabel('固定验证覆盖多类功能与资源任务。你的测试台用于探索，不改变核心身份。')
        self.validation_note.setWordWrap(True);self.validation_note.setObjectName('Dim');validation.addWidget(self.validation_note)
        tests_split=QSplitter(Qt.Orientation.Horizontal);validation.addWidget(tests_split,1)
        bench_scroll=QScrollArea();bench_scroll.setWidgetResizable(True)
        self.bench_page=QWidget();self.bench_layout=QVBoxLayout(self.bench_page)
        self.bench_layout.setContentsMargins(0,0,10,0);bench_scroll.setWidget(self.bench_page);tests_split.addWidget(bench_scroll)
        output=QWidget();output_layout=QVBoxLayout(output);output_layout.setContentsMargins(6,0,0,0)
        self.test_summary=QLabel('尚未运行');self.test_summary.setWordWrap(True);self.test_summary.setObjectName('Cyan');output_layout.addWidget(self.test_summary)
        self.output_tabs=QTabWidget();output_layout.addWidget(self.output_tabs,1)
        tests_split.addWidget(output);tests_split.setSizes([300,560])
        self.tabs.addTab(self.validation_page,'验证与测试台')
        self.library_page=QWidget();library_layout=QVBoxLayout(self.library_page)
        info=QLabel('发布的 IP 是不可变快照；继续修改草稿不会改动已经使用它的 SoC。双击资产可建立可编辑设计。')
        info.setWordWrap(True);info.setObjectName('Dim');library_layout.addWidget(info)
        self.library_list=QListWidget();self.library_list.itemDoubleClicked.connect(lambda _:self.load_selected());library_layout.addWidget(self.library_list,1)
        library_actions=QHBoxLayout()
        for title,action in [('编辑选中核心',self.load_selected),('导出选中 .cor',self.export_selected),('实例化选中 IP',self.use_selected)]:
            button=QPushButton(title);button.clicked.connect(action);library_actions.addWidget(button)
        library_layout.addLayout(library_actions);self.tabs.addTab(self.library_page,'已发布 IP')
        self.spec_text=QPlainTextEdit();self.spec_text.setReadOnly(True);self.spec_text.setFont(T.font(11,mono=True))
        self.tabs.addTab(self.spec_text,'设计定义')
        self.status=QLabel('新建设计后编辑模块参数。草稿自动保存。')
        self.status.setWordWrap(True);self.status.setObjectName('Dim');workspace.addWidget(self.status)
        self.replace_cpu=QCheckBox('实例化 CPU 时替换当前应用核集群')
        self.replace_cpu.setToolTip('仅影响CPU；不同ISA不会自动混入同一应用集群。')
        workspace.addWidget(self.replace_cpu)
        actions=QHBoxLayout()
        self.verify_btn=QPushButton('验证核心');self.verify_btn.setObjectName('Primary');self.verify_btn.clicked.connect(self.verify_current);actions.addWidget(self.verify_btn)
        self.publish_btn=QPushButton('发布到 IP 库');self.publish_btn.clicked.connect(self.publish_current);actions.addWidget(self.publish_btn)
        self.export_btn=QPushButton('导出 .cor');self.export_btn.clicked.connect(self.export_current);actions.addWidget(self.export_btn)
        self.use_btn=QPushButton('加入当前 SoC');self.use_btn.clicked.connect(lambda:self.instantiate(self._current_asset()));actions.addWidget(self.use_btn)
        workspace.addLayout(actions)
        self._loading=False

    def _clear(self,layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()

    def restore_workspace(self):
        workspace=self.win.core_workspace
        if not isinstance(workspace,dict):workspace={}
        originals=workspace.get('drafts',[]);drafts=[]
        if isinstance(originals,list):
            for record in originals[:64]:
                if not isinstance(record,dict) or record.get('kind') not in KINDS:continue
                kind=record['kind'];h=default_hardware(kind)
                incoming=record.get('hardware',{})
                if not isinstance(incoming,dict):continue
                # 保留可编辑的范围内无效组合；错误组合仍不允许发布。
                for field in FIELDS[kind]:
                    key=field['key'];value=incoming.get(key,h[key])
                    if 'options' in field:
                        valid=type(value) is type(field['default']) and value in [v for v,_ in field['options']]
                    elif type(field['default']) is bool:valid=type(value) is bool
                    else:valid=type(value) is type(field['default']) and field['min']<=value<=field['max']
                    if valid:h[key]=value
                b=default_bench(kind,h);incoming_b=record.get('bench',{})
                if isinstance(incoming_b,dict):
                    for field in BENCH_FIELDS[kind]:
                        value=incoming_b.get(field['key'],b[field['key']])
                        if field.get('text'):
                            if isinstance(value,str) and len(value)<=100000:b[field['key']]=value
                        elif 'options' in field:
                            if value in [v for v,_ in field['options']]:b[field['key']]=value
                        elif type(value) is type(field['default']) and field['min']<=value<=field['max']:b[field['key']]=value
                drafts.append(dict(id=str(record.get('id') or uuid.uuid4().hex),kind=kind,
                    name=str(record.get('name','未命名'))[:64],hardware=h,bench=b,published_id=record.get('published_id')))
        self.win.core_workspace=dict(drafts=drafts,active=workspace.get('active'))
        if not drafts:self.new_design('cpu');return
        active=next((d for d in drafts if d['id']==workspace.get('active')),drafts[0])
        self._load_draft(active)

    def new_design(self,kind):
        if kind not in KINDS:return
        drafts=self.win.core_workspace.setdefault('drafts',[])
        if len(drafts)>=64:self.status.setText('设计草稿最多64项。');return
        h=default_hardware(kind)
        record=dict(id=uuid.uuid4().hex,kind=kind,name=f'我的 {kind.upper()} {len(drafts)+1:02}',hardware=h,bench=default_bench(kind,h))
        drafts.append(record);self._load_draft(record);self._persist()

    def duplicate(self):
        if not self.current:return
        drafts=self.win.core_workspace['drafts']
        if len(drafts)>=64:self.status.setText('设计草稿最多64项。');return
        record=deepcopy(self.current);record.update(id=uuid.uuid4().hex,name=(record['name']+' 副本')[:64],published_id=None)
        drafts.append(record);self._load_draft(record);self._persist()

    def load_experiment(self,key):
        from ...data.core_experiments import experiment_preset
        if not key:return
        drafts=self.win.core_workspace.setdefault('drafts',[])
        if len(drafts)>=64:self.status.setText('设计草稿最多64项。');return
        record=dict(experiment_preset(key),id=uuid.uuid4().hex)
        drafts.append(record);self._load_draft(record);self._persist()

    def _load_draft(self,record):
        self._loading=True;self.current=record;self.verification=None;self.last_result=None;self.last_performance=None
        self.selected_module=None;self.name_edit.setText(record['name']);self.kind_label.setText(KINDS[record['kind']])
        self.win.core_workspace['active']=record['id']
        self._build_parameters();self._build_bench();self._clear_outputs()
        self._loading=False
        asset=self._current_asset()
        if asset and asset.get('design',{}).get('hardware')==record['hardware'] and asset['name']==record['name']:
            self.verification=deepcopy(asset['verification'])
        else:record['published_id']=None
        self._refresh_drafts();self._preview();self.tabs.setCurrentIndex(0)
        self.status.setText('草稿自动保存；选择结构模块或编辑参数，验证通过后发布 IP。')
        self.refresh()

    def _refresh_drafts(self):
        self.drafts.blockSignals(True);self.drafts.clear()
        for draft in self.win.core_workspace.get('drafts',[]):
            item=QListWidgetItem(f"{draft['name']}\n{draft['kind'].upper()} · {'已发布' if draft.get('published_id') else '设计草稿'}")
            item.setData(Qt.ItemDataRole.UserRole,draft['id']);item.setToolTip(draft['name']);self.drafts.addItem(item)
            if self.current and draft['id']==self.current['id']:self.drafts.setCurrentItem(item)
        self.drafts.blockSignals(False)

    def _select_draft(self,index):
        item=self.drafts.item(index)
        if not item:return
        record=next((d for d in self.win.core_workspace['drafts'] if d['id']==item.data(Qt.ItemDataRole.UserRole)),None)
        if record:self._load_draft(record);self._persist()

    def _control(self,field,value,changed):
        if field.get('text'):
            control=QPlainTextEdit();control.setFont(T.font(12,mono=True));control.setMinimumHeight(130);control.setPlainText(value)
            control.textChanged.connect(changed)
        elif 'options' in field:
            control=QComboBox()
            for key,title in field['options']:control.addItem(title,key)
            control.setCurrentIndex(control.findData(value));control.currentIndexChanged.connect(changed)
        elif type(field['default']) is bool:
            control=QCheckBox();control.setChecked(value);control.toggled.connect(changed)
        else:
            control=QSpinBox() if type(field['default']) is int else QDoubleSpinBox()
            if isinstance(control,QDoubleSpinBox):control.setDecimals(3);control.setSingleStep(.1)
            control.setRange(field['min'],field['max']);control.setValue(value);control.valueChanged.connect(changed)
        control.setAccessibleName(field['label']);control.setToolTip(field.get('hint',''))
        return control

    def _value(self,control):
        if isinstance(control,QPlainTextEdit):return control.toPlainText()
        if isinstance(control,QComboBox):return control.currentData()
        if isinstance(control,QCheckBox):return control.isChecked()
        return control.value()

    def _build_parameters(self):
        self._clear(self.inspector_layout);self.controls={};self.groups={};self.fields={}
        kind=self.current['kind'];h=self.current['hardware']
        for field in FIELDS[kind]:
            group=field['group']
            if group not in self.groups:
                names={'contract':'指令集与能力','frontend':'前端','scheduler':'调度与发射','alu':'运算资源','multiply':'乘除资源',
                       'cache':'数据缓存','processors':'SIMT处理器','interface':'接口与吞吐','array':'MAC阵列',
                       'accumulator':'累加器','scratchpad':'本地存储','black_level':'黑电平','gain':'增益','demosaic':'去马赛克',
                       'gamma':'gamma','quantize':'输出量化','line_buffer':'行缓冲容量'}
                card=Card(names[group]);form=QFormLayout();form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);card.add_layout(form)
                self.groups[group]=(card,form);self.inspector_layout.addWidget(card)
            form=self.groups[group][1];label=QLabel(field['label']);label.setObjectName('Muted');label.setWordWrap(True)
            control=self._control(field,h[field['key']],self._hardware_changed)
            form.addRow(label,control);self.controls[field['key']]=control;self.fields[field['key']]=(field,label,control)
        expand=QPushButton('展开 / 折叠专家参数');expand.clicked.connect(self._expand);self.inspector_layout.addWidget(expand)
        note=QLabel('结构由参数化模型生成。没有生成 RTL；PPA 是教学估算。')
        note.setWordWrap(True);note.setObjectName('Muted');self.inspector_layout.addWidget(note);self.inspector_layout.addStretch(1)
        self.set_learning_mode()

    def _build_bench(self):
        self._clear(self.bench_layout);self.bench_controls={}
        title=QLabel('我的测试台');title.setObjectName('H3');self.bench_layout.addWidget(title)
        note=QLabel('测试汇编、矩阵尺寸、图像与校准值不属于核心硬件。');note.setWordWrap(True);note.setObjectName('Muted');self.bench_layout.addWidget(note)
        from ...data.core_experiments import EXPERIMENTS
        experiments=QComboBox();experiments.addItem('载入资源实验草稿…',None)
        for key,name in EXPERIMENTS.items():experiments.addItem(name,key)
        experiments.currentIndexChanged.connect(lambda:self.load_experiment(experiments.currentData()) if experiments.currentData() else None)
        self.bench_layout.addWidget(experiments)
        if self.current['kind']=='cpu':
            presets=QComboBox();presets.addItem('选择资源测试程序…',None)
            for case in performance_cases(self.current['hardware']['architecture']):presets.addItem(case['name'],case['id'])
            presets.currentIndexChanged.connect(lambda:self._load_performance_case(presets.currentData()));self.bench_layout.addWidget(presets)
            self.performance_btn=QPushButton('运行CPU性能套件 · 逐项比较IPC')
            self.performance_btn.clicked.connect(self.run_performance);self.bench_layout.addWidget(self.performance_btn)
            self.pin_performance=QPushButton('将上次性能套件设为对照')
            self.pin_performance.clicked.connect(self._pin_performance);self.bench_layout.addWidget(self.pin_performance)
        for field in BENCH_FIELDS[self.current['kind']]:
            label=QLabel(field['label']);label.setWordWrap(True);label.setObjectName('Muted');self.bench_layout.addWidget(label)
            control=self._control(field,self.current['bench'][field['key']],self._bench_changed)
            self.bench_controls[field['key']]=control;self.bench_layout.addWidget(control)
        button=QPushButton('运行我的测试');button.clicked.connect(self.run_bench);self.bench_layout.addWidget(button);self.bench_layout.addStretch(1)

    def _hardware_changed(self,*_):
        if self._loading or not self.current:return
        before=self.current['hardware'].get('architecture')
        self.current['hardware']={key:self._value(control) for key,control in self.controls.items()}
        if before!=self.current['hardware'].get('architecture'):
            self.current['bench']=default_bench('cpu',self.current['hardware']);self._loading=True;self._build_bench();self._loading=False
        self.current['published_id']=None;self.verification=None;self.last_result=None;self.last_performance=None
        self._clear_outputs();self._preview();self._refresh_drafts();self._persist();self.set_learning_mode();self.refresh()
        self.status.setText('硬件已修改，旧验证结果失效。草稿已自动保存。')

    def _rename(self,*_):
        if self._loading or not self.current:return
        self.current['name']=self.name_edit.text();self.current['published_id']=None
        self._refresh_drafts();self._preview();self._persist();self.refresh()

    def _bench_changed(self,*_):
        if self._loading or not self.current:return
        self.current['bench']={key:self._value(control) for key,control in self.bench_controls.items()}
        self.last_result=None;self._clear_outputs();self._persist()
        self.test_summary.setText('测试台已修改；硬件与固定验证状态保持，重新运行查看输出。')

    def _persist(self):
        self.win.persist()

    def _preview(self):
        if not self.current:return
        kind=self.current['kind'];h=self.current['hardware']
        try:
            spec=structure(kind,h);self.graph.set_structure(spec)
            model=design_model(kind,self.current['name'],h)
            if kind=='cpu':resource=f"{h['alu_ports']} ALU · L1D {h['cache_kb']}KiB";area=model['logic_area'];extra=f"参考 Fmax {model['fmax_ref']:.2f}GHz"
            elif kind=='gpu':resource=f"{h['processors']}×{h['warp_size']}lane · {h['resident_warps']}驻留warp/处理器";area=model['area_per_unit']*h['processors'];extra=f"目标 {h['frequency_ghz']:g}GHz"
            elif kind=='npu':resource=f"{h['rows']*h['cols']} MAC · INT{h['precision_bits']} / INT{h['accumulator_bits']}";area=model['area'];extra=f"抽象峰值 {model['tops']:.4f}TOPS"
            else:resource=f"{len(spec['nodes'])}模块 · {h['pixels_per_cycle']}pixel/cycle";area=model['area'];extra='RGB' if h['demosaic_enabled'] else 'RAW灰度'
            self.metrics.setText(f'{resource}  ·  面积估算 {area:.3f}mm²  ·  {extra}\n参考节点N3E；资源与PPA映射为游戏假设。选择模块编辑参数。')
        except (ValueError,TypeError,KeyError) as ex:
            self.metrics.setText('设计待修复：'+str(ex));self.graph.set_structure(dict(nodes=[],edges=[]))
        self.spec_text.setPlainText(json.dumps(dict(kind=kind,name=self.current['name'],design=dict(schema=SCHEMA,hardware=h),
            testbench=self.current['bench'],testbench_is_not_identity=True),ensure_ascii=False,indent=2))

    def _select_module(self,module):
        self.selected_module=module;self.graph.selected=module;self.graph.update()
        if module in self.groups:
            card,_=self.groups[module]
            self.expanded=True;self.set_learning_mode()
            self.inspector_scroll.ensureWidgetVisible(card)
            for field in FIELDS[self.current['kind']]:
                if field['group']==module and not self.controls[field['key']].isHidden():self.controls[field['key']].setFocus();break

    def _expand(self):
        self.expanded=not self.expanded;self.set_learning_mode()

    def set_learning_mode(self):
        if not self.current:return
        level=MODES[self.win.learning_mode]['level'];kind=self.current['kind'];h=self.current['hardware']
        visible_groups=set()
        for key,(field,label,control) in self.fields.items():
            visible=self.expanded or level>=field['level']
            if kind=='cpu':
                if key in ('enable_m','enable_zbb') and h['architecture']!='riscv32':visible=False
                if field['group']=='multiply' and h['architecture']=='riscv32' and not h['enable_m']:visible=False
            if kind=='isp' and field['group']=='line_buffer' and not h['demosaic_enabled']:visible=False
            label.setVisible(visible);control.setVisible(visible)
            if visible:visible_groups.add(field['group'])
        for group,(card,_) in self.groups.items():card.setVisible(group in visible_groups)

    def _clear_outputs(self):
        if self.observer:
            self.observer.stop();self.tabs.removeTab(self.tabs.indexOf(self.observer));self.observer.deleteLater();self.observer=None
        while self.output_tabs.count():
            widget=self.output_tabs.widget(0);self.output_tabs.removeTab(0);widget.deleteLater()
        self.test_summary.setText('尚未运行。固定验证与我的测试分别记录。')

    def _table(self,title,columns,rows):
        table=QTableWidget();table.setColumnCount(len(columns));table.setHorizontalHeaderLabels(columns)
        table.setRowCount(min(1500,len(rows)));table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False);table.setAlternatingRowColors(True)
        for i,row in enumerate(rows[:1500]):
            for j,value in enumerate(row):table.setItem(i,j,QTableWidgetItem(str(value)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True);self.output_tabs.addTab(table,title)

    def verify_current(self):
        if not self.current:return
        try:
            self.verification=verify_design(self.current['kind'],self.current['hardware'])
            self._clear_outputs()
            self._table('固定验证',('任务','结果','指令数','周期','IPC','观察'),[(c['name'],'通过' if c['passed'] else '失败',c['instructions'] if c['instructions'] is not None else '—',c['cycles'],f"{c['ipc']:.4f}" if c['ipc'] is not None else '—',c['observation']) for c in self.verification['cases']])
            passed=self.verification['passed']
            self.test_summary.setText(f"{len(self.verification['cases'])}项固定向量 · {'通过' if passed else '失败'}\n周期是资源模型；不是完整ISA、RTL或PDK认证。")
            self.status.setText('核心固定验证通过，可以发布 IP。' if passed else '固定验证失败，请修复硬件资源或约束。')
        except (ValueError,TypeError,KeyError) as ex:self.verification=None;self.status.setText('验证未完成：'+str(ex))
        self.tabs.setCurrentWidget(self.validation_page);self.refresh()

    def run_bench(self):
        if not self.current:return
        try:
            result=run_design(self.current['kind'],self.current['hardware'],self.current['bench']);self.last_result=result
            self._clear_outputs();kind=self.current['kind']
            if kind=='cpu':
                self._table('架构寄存器',('寄存器','HEX','unsigned'),[(name,hex(value),value) for name,value in zip(result['register_names'],result['registers'])])
                self._table('调度时序',('线程','指令','分派','发射','完成','提交'),[(r.get('thread',0),r['instruction'].text,r['dispatch'],r['issue'],r['done'],r['retire']) for r in result['rows']])
                h=result['hardware']
                extra=f"IPC {result['ipc']:.5f} = {result['instructions']}条 / {result['cycles']}周期 · cache hit {result['cache']['hit_rate']:.1%}\n资源：{h['width']}共同宽度 / {h['execution_ports']}总发射 / {h['alu_ports']}ALU / {h['rob_size']}在途 / {h['cache_kb']}KiB cache\n短访存/依赖程序可能不受加宽影响。使用性能套件查看不同资源瓶颈。"
                if 'speedup' in result:
                    extra+=f"\n双线程对比：独跑总计 {result['sequential_cycles']} cycle → 共享核心 {result['cycles']} cycle；加速比 {result['speedup']:.3f}（不保证提升）"
                    self._table('线程结果',('线程','指令数','完成周期','IPC'),[(t['thread'],t['instructions'],t['cycles'],f"{t['ipc']:.5f}") for t in result['threads']])
                if 'prediction' in result:
                    extra+=f"\n分支 {result['prediction']['branches']} / 误预测 {result['prediction']['mispredictions']}；MSHR阻塞 {result['stalls']['mshr_full']} cycle"
            elif kind=='gpu':
                self._table('逐lane输出',('lane','FP32'),list(enumerate(result['output'])))
                self._table('warp资源',('warp','处理器','开始','完成','分歧路径'),[(r['warp'],r['processor'],r['start'],r['finish'],r['paths']) for r in result['warps']])
                extra=f"计算 {result['compute_cycles']} · 传输 {result['transfer_cycles']} · 分歧warp {result['divergence']}"
            elif kind=='npu':
                self._table('矩阵输出',('行','列','结果'),[(i,j,v) for i,row in enumerate(result['output']) for j,v in enumerate(row)])
                extra=f"计算 {result['compute_cycles']} · 传输 {result['transfer_cycles']} · scratchpad {result['scratchpad_bytes']}B / 匹配{result['scratchpad_fits']} · 溢出 {result['overflow_count']}"
            else:
                height=len(result['output']);width=len(result['output'][0]);image=QImage(width,height,QImage.Format.Format_RGB32)
                maximum=(1<<self.current['hardware']['output_bits'])-1
                for y,row in enumerate(result['output']):
                    for x,pixel in enumerate(row):image.setPixel(x,y,0xff000000|sum(round(v/maximum*255)<<shift for v,shift in zip(pixel,(16,8,0))))
                view=QLabel();view.setAlignment(Qt.AlignmentFlag.AlignCenter);view.setPixmap(QPixmap.fromImage(image).scaled(360,260,Qt.AspectRatioMode.KeepAspectRatio));self.output_tabs.addTab(view,'输出图像')
                self._table('像素输出',('y','x','R','G','B'),[(y,x,*pixel) for y,row in enumerate(result['output']) for x,pixel in enumerate(row)])
                extra=f"{result['color_mode']} · 行缓冲分配 {result['allocated_line_buffer_bytes']}B · 计算 {result['compute_cycles']} · 传输 {result['transfer_cycles']}"
            self.observer=ExecutionObserver(result);self.tabs.addTab(self.observer,'执行观测');self.tabs.setCurrentWidget(self.observer)
            self.test_summary.setText(f"我的测试：{result['cycles']} cycle\n{extra}\n自定义测试结果不替代固定验证套件。")
            self.status.setText('测试台运行完成；修改输入不会改变硬件身份。')
        except (ValueError,TypeError,KeyError,OverflowError) as ex:self.last_result=None;self.status.setText('测试未完成：'+str(ex))

    def _load_performance_case(self,key):
        if not key or not self.current or self.current['kind']!='cpu':return
        case=next(c for c in performance_cases(self.current['hardware']['architecture']) if c['id']==key)
        for field,value in case['bench'].items():self.bench_controls[field].setPlainText(value)

    def run_performance(self):
        if not self.current or self.current['kind']!='cpu':return
        try:
            result=cpu_performance_report(self.current['hardware']);self.last_performance=result
            self.last_result=None;self._clear_outputs()
            baseline=self.performance_baseline
            usable=baseline and baseline['hardware']['architecture']==result['hardware']['architecture'] and [c['id'] for c in baseline['cases']]==[c['id'] for c in result['cases']]
            original={c['id']:c for c in baseline['cases']} if usable else {}
            rows=[]
            for c in result['cases']:
                prev=original.get(c['id']);change=f"{(c['ipc']/prev['ipc']-1)*100:+.1f}%" if prev else '未设同任务对照'
                rows.append((c['name'],c['instructions'],c['cycles'],f"{c['ipc']:.5f}",f"{c['cache_hit_rate']:.1%}",change,c['focus']))
            self._table('CPU性能套件',('任务','指令数','周期','IPC','cache命中','IPC对照变化','主要资源'),rows)
            h=result['hardware'];self.test_summary.setText(f"性能套件：{result['instructions']}条 / {result['cycles']}周期 = IPC {result['ipc']:.5f}\n{h['width']}共同宽度 / {h['execution_ports']}发射 / {h['alu_ports']}ALU / {h['rob_size']}在途 / {h['cache_kb']}KiB\n"+result['scope'])
            self.status.setText('按任务观察瓶颈；先设为对照，再修改硬件并重跑。性能套件不替代固定功能验证。')
            self.tabs.setCurrentWidget(self.validation_page)
        except (ValueError,TypeError,KeyError) as ex:self.last_performance=None;self.status.setText('性能测试失败：'+str(ex))

    def _pin_performance(self):
        if self.last_performance:self.performance_baseline=deepcopy(self.last_performance);self.status.setText('已保存性能对照。修改硬件后重跑同ISA同任务套件。')
        else:self.status.setText('先运行CPU性能套件，再保存对照。')

    def publish_current(self):
        if not self.current or not self.verification or not self.verification['passed']:return None
        try:
            asset=make_design_asset(self.current['kind'],self.current['name'],self.current['hardware'])
            if asset['id'] not in self.win.ip_library and len(self.win.ip_library)>=64:raise ValueError('IP库最多64项。')
            self.win.ip_library[asset['id']]=asset;self.current['published_id']=asset['id'];self._persist();self._refresh_drafts();self.refresh()
            self.status.setText('已发布 '+asset['name']+' · '+asset['id'][:12]+'；可导出或加入 SoC。')
            return asset
        except (ValueError,TypeError,KeyError) as ex:self.status.setText('未发布：'+str(ex));return None

    def _current_asset(self):
        return self._available_assets().get(self.current.get('published_id')) if self.current else None

    def _available_assets(self):
        assets=dict(self.win.ip_library)
        if self.win.design:assets.update(self.win.design.embedded_ips)
        return assets

    def _selected_asset(self):
        item=self.library_list.currentItem()
        return self._available_assets().get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def refresh(self):
        self.publish_btn.setEnabled(bool(self.verification and self.verification['passed']))
        asset=self._current_asset();self.export_btn.setEnabled(asset is not None)
        from ...data.segments import SEGMENTS
        sandbox=self.win.design is not None and 'custom' in SEGMENTS[self.win.design.scenario_id]['allowed_licenses']
        self.use_btn.setEnabled(bool(asset and sandbox));self.replace_cpu.setVisible(bool(self.current and self.current['kind']=='cpu'))
        self.draft_status.setText('已发布 / 自动保存' if asset else '已验证 / 自动保存' if self.verification and self.verification['passed'] else '草稿 / 自动保存')
        selected=self._selected_asset();selected_id=selected['id'] if selected else None
        self.library_list.clear()
        for asset in self._available_assets().values():
            source='当前 SoC 内嵌' if asset['id'] not in self.win.ip_library else '本地 IP 库'
            item=QListWidgetItem(f"{asset['name']} · {asset['kind'].upper()}\n{asset['id'][:12]} · {source} · {'硬件设计' if 'design' in asset else '旧实验资产'}")
            item.setData(Qt.ItemDataRole.UserRole,asset['id']);self.library_list.addItem(item)
            if asset['id']==selected_id:self.library_list.setCurrentItem(item)
        self.set_learning_mode()

    def import_path(self,path):
        asset=read_asset(path)
        if asset['id'] not in self.win.ip_library and len(self.win.ip_library)>=64:raise ValueError('IP库最多64项。')
        self.win.ip_library[asset['id']]=asset;self.load_asset(asset);self._persist();return asset

    def load_asset(self,asset):
        if len(self.win.core_workspace['drafts'])>=64:raise ValueError('草稿最多64项。')
        kind=asset['kind']
        hardware=validate_hardware(kind,asset['design']['hardware']) if 'design' in asset else hardware_from_legacy(kind,asset['config'])
        bench=default_bench(kind,hardware)
        if 'design' not in asset:
            bench.update({k:v for k,v in asset['config'].items() if k in bench})
        record=dict(id=uuid.uuid4().hex,name=asset['name'],kind=kind,hardware=hardware,bench=bench,
                    published_id=asset['id'] if 'design' in asset else None)
        self.win.core_workspace['drafts'].append(record);self._load_draft(record)
        self.status.setText('已载入硬件设计。' if 'design' in asset else '旧实验资产已转换为硬件草稿；原资产保留。重新验证后可发布。')
        self._persist()

    def load_template(self,model):
        if len(self.win.core_workspace['drafts'])>=64:raise ValueError('草稿最多64项。')
        hardware=hardware_from_template(model)
        record=dict(id=uuid.uuid4().hex,name=model['name'],kind='cpu',hardware=hardware,bench=default_bench('cpu',hardware),published_id=None)
        self.win.core_workspace['drafts'].append(record);self._load_draft(record);self._persist()
        self.status.setText('已复制教学模板的完整硬件。编辑、验证后发布成自己的核心；原模板不会改变。')

    def load_selected(self):
        asset=self._selected_asset()
        if asset:
            try:self.load_asset(asset)
            except ValueError as ex:self.status.setText(str(ex))

    def import_dialog(self):
        path,_=QFileDialog.getOpenFileName(self,'导入核心设计','','Silicon Core/IP (*.cor *.spip.json *.json)')
        if not path:return
        try:self.import_path(path)
        except (OSError,ValueError,TypeError,KeyError) as ex:self.status.setText('导入失败：'+str(ex))

    def _export_asset(self,asset):
        if not asset:return
        path,_=QFileDialog.getSaveFileName(self,'导出核心设计','exports/'+asset['id']+'.cor','Silicon Core/IP (*.cor)')
        if not path:return
        try:write_asset(path,asset);self.status.setText('已导出 '+asset['name'])
        except (OSError,ValueError) as ex:self.status.setText('导出失败：'+str(ex))

    def export_current(self):self._export_asset(self._current_asset())
    def export_selected(self):self._export_asset(self._selected_asset())
    def use_selected(self):self.instantiate(self._selected_asset())

    def instantiate(self,asset):
        if not asset:return
        from ...data.segments import SEGMENTS
        if not self.win.design or 'custom' not in SEGMENTS[self.win.design.scenario_id]['allowed_licenses']:
            self.status.setText('先进入研究沙盒或开放核心挑战，再选择要实例化的IP。');return
        previous=deepcopy(self.win.design)
        try:
            if asset['kind']=='cpu' and self.replace_cpu.isChecked():self.win.design.cores=[]
            attach_asset(self.win.design,asset);self.win.recompute_now(force_layout=True)
            self.status.setText('已加入SoC：'+asset['name']+'；导出.sil将内嵌定义。');self.win.go('architecture')
        except (ValueError,TypeError,KeyError) as ex:self.win.design=previous;self.status.setText('未实例化：'+str(ex))

    def on_result(self):self.refresh()
