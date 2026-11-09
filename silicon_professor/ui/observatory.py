"""核心模型的播放、逐周期与状态观测。"""
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QIcon
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QToolButton,
    QComboBox,QSlider,QSpinBox,QTableWidget,QTableWidgetItem,QHeaderView,QStyle,QScrollArea,QFrame)

from ..engine.observatory import execution_snapshot
from . import theme as T

STAGES={'raw':'RAW12','black_level':'黑电平','gain':'增益','demosaic':'去马赛克','gamma':'gamma','quantize':'量化输出'}
COLORS={'等待':T.AMBER,'执行':T.CYAN,'待提交':T.GREEN}


class ExecutionCanvas(QWidget):
    def __init__(self,observer):
        super().__init__();self.observer=observer;self.setMinimumWidth(300);self.setFixedHeight(225)

    def paintEvent(self,event):
        o=self.observer;s=o.snapshot;r=o.result
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),QColor(T.BG2))
        p.setFont(T.font(11,mono=True));p.setPen(QColor(T.TEXT2))
        w=self.width()-32
        if r['kind']=='cpu':
            h=r['hardware']
            for i,(unit,name,limit) in enumerate([('alu','ALU',h['alu_ports']),('multiply','MUL / DIV',h['multiply_ports']),('memory','LSU',1),('branch','BRANCH',1)]):
                x=16+i*w/4;entries=[e for e in s['active'] if e['unit']==unit and e['stage']=='执行']
                p.setPen(QColor(T.TEXT2));p.drawText(QRectF(x,12,w/4-8,22),f'{name}   {len(entries)} 在执行')
                p.setPen(Qt.PenStyle.NoPen)
                for j in range(min(limit,12)):
                    p.setBrush(QColor(T.CYAN if j<len(entries) else T.BORDER));p.drawRect(QRectF(x+j*(w/4-8)/limit,40,(w/4-8)/limit-3,28))
            p.setPen(QColor(T.TEXT2));p.drawText(QRectF(16,86,w,22),f"ROB  {s['rob_occupancy']} / {h['rob_size']}     等待 / 执行 / 待提交")
            columns=16;cell=min(24,(w-15*4)/columns)
            for i,e in enumerate(s['active'][:64]):
                x=16+(i%columns)*(cell+4);y=120+(i//columns)*(cell+4)
                p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(COLORS[e['stage']]));p.drawRect(QRectF(x,y,cell,cell))
                p.setPen(QColor(T.BG));p.drawText(QRectF(x,y,cell,cell),Qt.AlignmentFlag.AlignCenter,str(e['thread']))
        elif r['kind']=='gpu':
            entries=s['active'][:6]
            if not entries:
                p.drawText(QRectF(16,24,w,30),'无在执行的向量指令')
            for i,e in enumerate(entries):
                y=14+i*32;p.setPen(QColor(T.TEXT2))
                p.drawText(QRectF(16,y,160,25),f"P{e['processor']} W{e['warp']} {e['op'].upper()}")
                warp=r['warps'][e['warp']];size=r['hardware']['warp_size'];cell=min(15,(w-160)/size)
                for lane in range(size):
                    index=warp['first_lane']+lane
                    color=T.CYAN if index in e['lanes'] else T.BORDER if lane<warp['active_lanes'] else T.BG
                    p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(color));p.drawRect(QRectF(180+lane*cell,y+3,cell-2,19))
            p.setPen(QColor(T.TEXT2));p.drawText(QRectF(16,205,w,20),f"输出 {s['completed']} / {len(r['output'])} lane   |   在执行 {len(s['active'])}条 · 显示{len(entries)}条")
        elif r['kind']=='npu':
            rows=r['array_rows'];cols=r['array_cols'];size=min(180/rows,(w-190)/cols)
            active={(e['row'],e['col']) for e in s['active']}
            for i in range(rows):
                for j in range(cols):
                    p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor(T.CYAN if (i,j) in active else T.BORDER))
                    p.drawRect(QRectF(16+j*size,18+i*size,max(1,size-1),max(1,size-1)))
            p.setPen(QColor(T.TEXT2));x=32+cols*size
            p.drawText(QRectF(x,20,w-cols*size-16,75),Qt.TextFlag.TextWordWrap,f"Tile {s['tile'] if s['tile'] is not None else '-'}\n{rows} x {cols} PE\n在执行 {len(active)} MAC")
            if s['active']:
                e=s['active'][0]
                p.drawText(QRectF(x,110,w-cols*size-16,90),Qt.TextFlag.TextWordWrap,f"PE [{e['row']},{e['col']}]\nK={e['k']}  {e['a']} x {e['b']}\nACC={e['accumulator']}")
        else:
            key=o.selected_stage;frame=r['stage_outputs'][key];maximum=r['stage_ranges'][key]
            height=len(frame);width=len(frame[0]);image=QImage(width,height,QImage.Format.Format_RGB32)
            visible=s['stages'][key]
            for y,row in enumerate(frame):
                for x,value in enumerate(row):
                    rgb=value if len(value)==3 else value*3
                    rgb=[max(0,min(255,round(v/maximum*255))) for v in rgb] if y*width+x<visible else [22,25,28]
                    image.setPixel(x,y,0xff000000|(rgb[0]<<16)|(rgb[1]<<8)|rgb[2])
            size=min(185/height,(w-140)/width)
            p.drawImage(QRectF(16,18,width*size,height*size),image)
            p.setPen(QColor(T.TEXT2));p.drawText(QRectF(36+width*size,24,w-width*size-20,150),Qt.TextFlag.TextWordWrap,
                f"{STAGES[key]}\n{width} x {height}\n{visible} / {r['pixels']} pixels\n行缓冲 {r['line_buffer_bytes']} B")
        p.end()


class ExecutionObserver(QScrollArea):
    def __init__(self,result,parent=None):
        super().__init__(parent);self.result=result;self.snapshot={};self.selected_stage='quantize'
        self.setWidgetResizable(True);self.setFrameShape(QFrame.Shape.NoFrame)
        page=QWidget();page.setMinimumWidth(300);self.setWidget(page)
        lay=QVBoxLayout(page);lay.setContentsMargins(8,8,8,8);lay.setSpacing(8)
        tools=QHBoxLayout();lay.addLayout(tools)
        self.timer=QTimer(self);self.timer.setInterval(60);self.timer.timeout.connect(self._tick)
        def button(icon,title,action):
            b=QToolButton();b.setIcon(self._icon(icon));b.setToolTip(title);b.setAccessibleName(title)
            b.setFixedSize(30,30);b.clicked.connect(action);tools.addWidget(b);return b
        button(QStyle.StandardPixmap.SP_MediaSkipBackward,'回到开始',lambda:self.cycle.setValue(0))
        button(QStyle.StandardPixmap.SP_MediaSeekBackward,'前一周期',lambda:self.step(-1))
        self.play=button(QStyle.StandardPixmap.SP_MediaPlay,'播放 / 暂停',self.toggle_play)
        button(QStyle.StandardPixmap.SP_MediaSeekForward,'后一周期',lambda:self.step(1))
        button(QStyle.StandardPixmap.SP_MediaSkipForward,'到达结束',lambda:self.cycle.setValue(result['cycles']))
        self.speed=QComboBox()
        for v in (1,4,16,64):self.speed.addItem(f'{v} cycle',v)
        self.speed.setCurrentIndex(1);self.speed.setToolTip('每次播放推进周期');tools.addWidget(self.speed)
        self.thread=QComboBox()
        for i in range(len(result.get('threads',[result]))):self.thread.addItem(f'线程 {i}',i)
        self.thread.setVisible(result['kind']=='cpu' and self.thread.count()>1);self.thread.currentIndexChanged.connect(self._refresh);tools.addWidget(self.thread)
        self.stage=QComboBox()
        for key in result.get('stage_outputs',{}):self.stage.addItem(STAGES[key],key)
        self.stage.setVisible(result['kind']=='isp');self.stage.setCurrentIndex(self.stage.findData('quantize'))
        self.stage.currentIndexChanged.connect(self._refresh);tools.addWidget(self.stage);tools.addStretch(1)
        self.cycle=QSpinBox();self.cycle.setRange(0,result['cycles']);self.cycle.setPrefix('cycle ');self.cycle.setToolTip('当前模型周期');tools.addWidget(self.cycle)
        self.slider=QSlider(Qt.Orientation.Horizontal);self.slider.setRange(0,result['cycles']);self.slider.setAccessibleName('回放周期');lay.addWidget(self.slider)
        self.slider.valueChanged.connect(self.cycle.setValue);self.cycle.valueChanged.connect(self.slider.setValue);self.cycle.valueChanged.connect(self._refresh)
        self.summary=QLabel();self.summary.setWordWrap(True);self.summary.setTextFormat(Qt.TextFormat.PlainText);self.summary.setObjectName('Cyan');lay.addWidget(self.summary)
        self.canvas=ExecutionCanvas(self);lay.addWidget(self.canvas)
        self.table=QTableWidget();self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False);self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True);self.table.setMinimumHeight(170);lay.addWidget(self.table,1)
        note=QLabel(result['assumptions']+(' 计算轴与输入/输出汇总传输账本不表示实际DMA先后顺序。' if result['kind']!='cpu' else ''))
        note.setWordWrap(True);note.setTextFormat(Qt.TextFormat.PlainText);note.setObjectName('Muted');lay.addWidget(note)
        self._refresh()

    def step(self,delta):self.cycle.setValue(max(0,min(self.result['cycles'],self.cycle.value()+delta)))

    def _icon(self,standard):
        pixmap=self.style().standardIcon(standard).pixmap(20,20)
        painter=QPainter(pixmap);painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(),QColor(T.TEXT));painter.end()
        return QIcon(pixmap)

    def toggle_play(self):
        if self.timer.isActive():self.stop()
        else:
            if self.cycle.value()==self.result['cycles']:self.cycle.setValue(0)
            self.timer.start();self.play.setIcon(self._icon(QStyle.StandardPixmap.SP_MediaPause))

    def stop(self):
        self.timer.stop();self.play.setIcon(self._icon(QStyle.StandardPixmap.SP_MediaPlay))

    def _tick(self):
        self.step(self.speed.currentData())
        if self.cycle.value()==self.result['cycles']:self.stop()

    def hideEvent(self,event):
        self.stop();super().hideEvent(event)

    def _refresh(self,*_):
        r=self.result;self.selected_stage=self.stage.currentData() or 'quantize'
        s=self.snapshot=execution_snapshot(r,self.cycle.value(),self.thread.currentData() or 0)
        kind=r['kind'];base=f"{s['phase']}   {s['cycle']} / {r['cycles']} cycle"
        if kind=='cpu':
            text=f"{base}   线程{s['thread']}已提交 {s['retired']}   全核已提交 {s['retired_total']}   ROB {s['rob_occupancy']}"
            columns=('寄存器','HEX','整数');rows=[(name,hex(value),value) for name,value in zip(r['register_names'],s['registers'])]
        elif kind=='gpu':
            text=f"{base}   输出 {s['completed']} / {len(r['output'])} lane"
            columns=('lane','FP32');rows=[(i,'未完成' if v is None else f'{v:.6g}') for i,v in enumerate(s['output'][:64])]
        elif kind=='npu':
            text=f"{base}   Tile {s['tile'] if s['tile'] is not None else '-'}   在执行 {len(s['active'])} MAC"
            columns=('行',*[str(i) for i in range(min(8,len(s['output'][0])))])
            rows=[(i,*['未完成' if v is None else v for v in row[:8]]) for i,row in enumerate(s['output'][:8])]
        else:
            text=f"{base}   输出 {s['emitted_pixels']} / {r['pixels']} pixels"
            frame=r['stage_outputs'][self.selected_stage];width=len(frame[0]);visible=s['stages'][self.selected_stage]
            columns=('y','x',STAGES[self.selected_stage]);rows=[]
            for i in range(min(64,r['pixels'])):
                value=frame[i//width][i%width]
                rows.append((i//width,i%width,'未完成' if i>=visible else ', '.join(f'{v:.5g}' for v in value)))
        self.summary.setText(text);self.canvas.update()
        self.table.setColumnCount(len(columns));self.table.setHorizontalHeaderLabels(columns);self.table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,value in enumerate(row):self.table.setItem(i,j,QTableWidgetItem(str(value)))
