"""历史档案、修复试验与独立保存的案例进度。"""
from datetime import datetime

from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter,QColor,QPen
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QListWidget,QListWidgetItem,
    QTabWidget,QPlainTextEdit,QScrollArea,QFormLayout,QComboBox,QCheckBox,QDoubleSpinBox,
    QPushButton,QTableWidget,QTableWidgetItem,QHeaderView,QFileDialog,QSplitter)

from ...data.rescue import RESCUE_CASES,FIELDS,default_controls,reference_controls
from ...data.sources import SOURCES,source_text
from ...data.core_experiments import EXPERIMENTS
from ...engine.rescue import run_rescue,validate_controls,export_rescue,read_rescue,MODEL
from .. import theme as T


class ThermalChart(QWidget):
    def __init__(self):super().__init__();self.result=None;self.setMinimumWidth(300);self.setFixedHeight(185)

    def paintEvent(self,event):
        if not self.result:return
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),QColor(T.BG2))
        points=self.result['thermal_points'];baseline=self.result['baseline_points']
        maximum=max(80,max(t for _,t in points+baseline));minimum=min(t for _,t in points+baseline)-5
        rect=QRectF(45,16,self.width()-62,self.height()-45)
        def point(time,value):return (rect.left()+time/60*rect.width(),rect.bottom()-(value-minimum)/(maximum-minimum)*rect.height())
        p.setFont(T.font(10,mono=True));p.setPen(QColor(T.DIM))
        p.drawText(8,20,'C');p.drawText(self.width()-44,self.height()-5,'60 s')
        for value in (25,70):
            _,y=point(0,value);p.setPen(QPen(QColor(T.BORDER),1));p.drawLine(int(rect.left()),int(y),int(rect.right()),int(y))
            p.setPen(QColor(T.DIM));p.drawText(8,int(y)+4,str(value))
        for series,color in ((baseline,T.RED),(points,T.CYAN)):
            p.setPen(QPen(QColor(color),2))
            for a,b in zip(series,series[1:]):
                x1,y1=point(*a);x2,y2=point(*b);p.drawLine(int(x1),int(y1),int(x2),int(y2))
        p.setPen(QColor(T.TEXT2));p.drawText(55,29,'初始 / 我的方案 · 恒功率RC（不是闭环降频）');p.end()


class RescueScreen(QWidget):
    def __init__(self,win):
        super().__init__();self.win=win;self.cid=None;self.last_result=None;self.controls={};self._loading=False
        outer=QVBoxLayout(self);outer.setContentsMargins(24,18,24,18);outer.setSpacing(10)
        heading=QHBoxLayout();title=QLabel('拯救芯片');title.setObjectName('H2');heading.addWidget(title)
        heading.addStretch(1);self.progress_label=QLabel();self.progress_label.setObjectName('Dim');heading.addWidget(self.progress_label);outer.addLayout(heading)
        self.list=QListWidget();self.list.setFixedWidth(235);self.list.currentItemChanged.connect(self._selected)
        for cid,c in RESCUE_CASES.items():
            item=QListWidgetItem(f"{c['name']}\n{c['year']} · {c['category']}");item.setData(Qt.ItemDataRole.UserRole,cid);self.list.addItem(item)
        body=QHBoxLayout();body.addWidget(self.list);outer.addLayout(body,1)
        work=QVBoxLayout();body.addLayout(work,1)
        self.title=QLabel();self.title.setObjectName('H3');self.title.setWordWrap(True);work.addWidget(self.title)
        self.tabs=QTabWidget();work.addWidget(self.tabs,1)
        self.case_text=QPlainTextEdit();self.case_text.setReadOnly(True);self.tabs.addTab(self.case_text,'历史与边界')
        self.test_page=QWidget();layout=QVBoxLayout(self.test_page)
        split=QSplitter(Qt.Orientation.Horizontal);layout.addWidget(split,1)
        scroll=QScrollArea();scroll.setWidgetResizable(True);page=QWidget();self.form=QFormLayout(page)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);scroll.setWidget(page);scroll.setMinimumWidth(230);split.addWidget(scroll)
        self.parameter_scroll=scroll
        result_scroll=QScrollArea();result_scroll.setWidgetResizable(True);result_page=QWidget();result_layout=QVBoxLayout(result_page);result_scroll.setWidget(result_page);split.addWidget(result_scroll);split.setSizes([260,600])
        self.summary=QLabel('尚未运行');self.summary.setTextFormat(Qt.TextFormat.PlainText);self.summary.setWordWrap(True);self.summary.setObjectName('Cyan');result_layout.addWidget(self.summary)
        self.chart=ThermalChart();result_layout.addWidget(self.chart)
        self.table=QTableWidget();self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.setMinimumHeight(170)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False);self.table.setAlternatingRowColors(True);result_layout.addWidget(self.table,1)
        self.consequence=QLabel();self.consequence.setTextFormat(Qt.TextFormat.PlainText);self.consequence.setWordWrap(True);self.consequence.setObjectName('Dim');result_layout.addWidget(self.consequence)
        actions=QHBoxLayout();layout.addLayout(actions)
        for name,callback in [('运行试验',self.run),('载入参考方案',self.load_reference),('恢复初始方案',self.reset)]:
            b=QPushButton(name);b.clicked.connect(callback);actions.addWidget(b)
            if callback==self.run:self.run_btn=b
            elif callback==self.load_reference:self.reference_btn=b
            else:self.reset_btn=b
        self.finish_btn=QPushButton('记录完成');self.finish_btn.setObjectName('Primary');self.finish_btn.clicked.connect(self.complete);actions.addWidget(self.finish_btn)
        self.tabs.addTab(self.test_page,'修复试验')
        sources_page=QWidget();sources_layout=QVBoxLayout(sources_page)
        self.source_picker=QComboBox();self.source_picker.currentIndexChanged.connect(self._source_changed);sources_layout.addWidget(self.source_picker)
        self.source_body=QPlainTextEdit();self.source_body.setReadOnly(True);sources_layout.addWidget(self.source_body);self.tabs.addTab(sources_page,'原始资料')
        lab=QHBoxLayout();work.addLayout(lab);self.lab_picker=QComboBox()
        for key,name in EXPERIMENTS.items():self.lab_picker.addItem(name,key)
        lab.addWidget(self.lab_picker,1);button=QPushButton('载入 LAB 实验');button.clicked.connect(self.open_lab);lab.addWidget(button)
        footer=QHBoxLayout();work.addLayout(footer)
        for name,callback in [('导出实验 JSON',self.export_dialog),('导入实验 JSON',self.import_dialog)]:
            b=QPushButton(name);b.clicked.connect(callback);footer.addWidget(b)
        footer.addStretch(1);self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.TextFormat.PlainText);work.addWidget(self.status)

    def restore_workspace(self):
        raw=self.win.rescue_workspace;cases={}
        if isinstance(raw,dict) and isinstance(raw.get('cases'),dict):
            for cid,record in raw['cases'].items():
                if cid not in RESCUE_CASES:continue
                try:cases[cid]=validate_controls(cid,record)
                except (ValueError,TypeError):continue
        active=raw.get('active') if isinstance(raw,dict) else None
        self.win.rescue_workspace=dict(cases=cases,active=active)
        self.select_case(active if isinstance(active,str) and active in RESCUE_CASES else next(iter(RESCUE_CASES)))

    def select_case(self,cid):
        if cid not in RESCUE_CASES:return
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole)==cid:
                if self.list.currentRow()==i:self._load_case(cid)
                else:self.list.setCurrentRow(i)
                break

    def _selected(self,item,previous):
        if item:self._load_case(item.data(Qt.ItemDataRole.UserRole))

    def _load_case(self,cid):
        self._loading=True;self.cid=cid;c=RESCUE_CASES[cid];self.title.setText(c['name'])
        pending=c.get('experiment_status')=='model_pending'
        self.parameter_scroll.setVisible(not pending);self.reset_btn.setVisible(not pending)
        self.run_btn.setText('查看测量记录' if pending else '运行试验')
        self.reference_btn.setVisible(not pending)
        self.tabs.setTabText(self.tabs.indexOf(self.test_page),'记录与性能条件' if pending else '修复试验')
        text='历史 / 设计目标\n'+c['history']+'\n\n条件与设备\n'+'\n'.join(c['conditions'])+'\n\n模型边界\n'+c['scope']
        if c.get('experiment_status')=='model_pending':
            from ...data.rescue_measurements import chip_record
            chip=chip_record(cid)
            text+='\n\n芯片本体\n'+chip['name']+'\n制程：'+chip['process']+'\nCPU：'+' + '.join(f'{count}×{name} @{clock:g}GHz' for name,count,clock in chip['cpu'])+'\nGPU：'+chip['gpu']+'\n内存：'+chip['memory']
            text+='\n\n具体问题与修复约束\n'+chip['constraints']+'\n\n原始工作负载记录（不是反事实预测）\n'
            text+='\n'.join(f"{o['test']}：{o['value']} {o['unit']} · {o['version'] or '版本未披露/不适用'}\n{SOURCES[o['source']]['title']} · {o['locator']}\n{o['notes']}" for o in chip['observations']) or '尚未取得可复核的测量。'
            text+='\n\nGB6：已有实测单独展示；没有分项校准时不转换SP分，也不按单核×核数估计多核。'
            from ...engine.rescue_performance import performance_contract
            rules=performance_contract(cid)
            text+='\n\n同负载性能交付下限（教学合同）\n'
            text+='\n'.join(f"{key}：原始记录缺失，不能据稳定性比值或其他版本分数判断修复。" if r['minimum'] is None else
                f"{key}：原记录 {r['baseline']:.2f} → 至少 {r['minimum']:.2f} {r['unit']}\n版本：{r['version'] or '未披露/不适用'}"+('\n'+r['assumption'] if r.get('derived') else '') for key,r in rules.items()) or '测量不足，不猜测分数或验收下限。'
            text+='\n\n当前不提供通用C/V/f通关；后续芯片级反事实估计必须保留单核≥90%、多核/GPU≥85%，持续绝对性能不得退步。'
        else:text+='\n\n性能门槛与周期是教学约束，不是原厂实测或完整修复认证。'
        self.case_text.setPlainText(text)
        while self.form.rowCount():self.form.removeRow(0)
        self.controls={};p=self.win.rescue_workspace.setdefault('cases',{}).get(cid,default_controls(cid))
        for f in ([] if c.get('experiment_status')=='model_pending' else FIELDS[c['kind']]):
            if 'options' in f:
                control=QComboBox()
                for key,name in f['options']:control.addItem(name,key)
                control.setCurrentIndex(control.findData(p[f['key']]));control.currentIndexChanged.connect(self._changed)
            elif type(f['default']) is bool:
                control=QCheckBox();control.setChecked(p[f['key']]);control.toggled.connect(self._changed)
            else:
                control=QDoubleSpinBox();control.setDecimals(2);control.setSingleStep(.05);control.setRange(f['min'],f['max']);control.setValue(p[f['key']]);control.valueChanged.connect(self._changed)
            label=QLabel(f['label']);label.setWordWrap(True);control.setAccessibleName(f['label']);self.form.addRow(label,control);self.controls[f['key']]=control
        self.source_picker.blockSignals(True);self.source_picker.clear()
        for sid in c['sources']:self.source_picker.addItem(SOURCES[sid]['title'],sid)
        self.source_picker.blockSignals(False);self._source_changed()
        self._loading=False;self.win.rescue_workspace['active']=cid;self._invalidate();self.tabs.setCurrentIndex(0);self.refresh();self.win.persist()

    def _values(self):
        return {key:control.currentData() if isinstance(control,QComboBox) else control.isChecked() if isinstance(control,QCheckBox) else control.value() for key,control in self.controls.items()}

    def _changed(self,*_):
        if self._loading:return
        self.win.rescue_workspace['cases'][self.cid]=self._values();self._invalidate();self.win.persist()

    def _invalidate(self):
        self.last_result=None;self.finish_btn.setEnabled(False);self.summary.setText('尚未运行当前方案。')
        self.chart.result=None;self.chart.hide();self.table.clear();self.table.setRowCount(0);self.consequence.clear()

    def _source_changed(self,*_):
        sid=self.source_picker.currentData();self.source_body.setPlainText(source_text(sid) if sid else '')

    def run(self):
        if not self.cid:return
        try:
            r=self.last_result=run_rescue(self.cid,self._values())
            def display(value):return f'{value:.3f}' if type(value) is float else str(value)
            self.summary.setText(('通过教学验收' if r['ready'] else '方案仍有问题')+'\n'+'\n'.join(('通过 · ' if c['ok'] else '未通过 · ')+c['title']+'：'+display(c['value']) for c in r['checks']))
            self.table.setColumnCount(len(r['columns']));self.table.setHorizontalHeaderLabels(r['columns']);self.table.setRowCount(len(r['rows']))
            for i,row in enumerate(r['rows']):
                for j,value in enumerate(row):self.table.setItem(i,j,QTableWidgetItem(f'{value:.4f}' if type(value) is float else str(value)))
            self.chart.result=r if 'thermal_points' in r else None;self.chart.setVisible(self.chart.result is not None);self.chart.update()
            self.consequence.setText(r['consequence']+'\n'+r['scope']);self.finish_btn.setEnabled(r['ready'])
            self.win.rescue_workspace['cases'][self.cid]=r['parameters'];self.win.persist();self.tabs.setCurrentWidget(self.test_page)
            self.status.setText('当前参数已保存；验收不代表实际芯片认证。')
        except (ValueError,TypeError,KeyError) as ex:self._invalidate();self.status.setText('试验未完成：'+str(ex))

    def load_reference(self):
        if RESCUE_CASES[self.cid].get('experiment_status')=='model_pending':self.run();return
        self.win.rescue_workspace['cases'][self.cid]=reference_controls(self.cid);self._load_case(self.cid);self.run()

    def reset(self):
        self.win.rescue_workspace['cases'][self.cid]=default_controls(self.cid);self._load_case(self.cid)

    def complete(self):
        if not self.last_result:return
        current=run_rescue(self.cid,self._values())
        if not current['ready']:self._invalidate();return
        progress=self.win.progress.setdefault('rescues',{})
        if not isinstance(progress,dict):progress={};self.win.progress['rescues']=progress
        progress[self.cid]=dict(completed=True,model=MODEL,parameters=current['parameters'],date=datetime.now().isoformat(timespec='seconds'))
        self.win.persist();self.refresh();self.status.setText('已记录教学案例完成；参考方案不是实物修复认证。')

    def refresh(self):
        progress=self.win.progress.get('rescues',{})
        if not isinstance(progress,dict):progress={}
        count=sum(isinstance(progress.get(cid),dict) and progress[cid].get('completed') is True and progress[cid].get('model')==MODEL and RESCUE_CASES[cid].get('experiment_status')!='model_pending' for cid in RESCUE_CASES)
        self.progress_label.setText(f'{count} / {len(RESCUE_CASES)} 已完成')

    def open_lab(self):
        s=self.win.screens['studio'];s.load_experiment(self.lab_picker.currentData());self.win.go('studio');s.run_bench()

    def export_dialog(self):
        path,_=QFileDialog.getSaveFileName(self,'导出拯救芯片试验',self.cid+'.json','实验记录 (*.json)')
        if path:
            try:export_rescue(path,self.cid,self._values());self.status.setText('实验参数、结果与资料已导出。')
            except (ValueError,OSError) as ex:self.status.setText('导出未完成：'+str(ex))

    def import_path(self,path):
        r=read_rescue(path);self.win.rescue_workspace['cases'][r['id']]=r['parameters'];self.select_case(r['id']);self.run();return self.last_result

    def import_dialog(self):
        path,_=QFileDialog.getOpenFileName(self,'导入拯救芯片试验','','实验记录 (*.json)')
        if path:
            try:self.import_path(path)
            except (ValueError,OSError) as ex:self.status.setText('导入未完成：'+str(ex))
