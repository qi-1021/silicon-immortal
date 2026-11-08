"""由硬件定义生成可选择模块的逻辑图，不允许用任意拖动伪造连接。"""
from PySide6.QtCore import QPointF,QRectF,Qt,Signal
from PySide6.QtGui import QPainter,QPen,QPainterPath
from PySide6.QtWidgets import QWidget,QSizePolicy
from . import theme as T


class CoreGraph(QWidget):
    module_selected=Signal(str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.spec={'nodes':[],'edges':[]};self.selected=None;self.boxes={}
        self.setMinimumSize(340,360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName('核心逻辑结构；选择模块定位参数')

    def set_structure(self,spec):
        self.spec=spec;self._height_for_nodes();self.update()

    def _height_for_nodes(self):
        columns=2 if self.width()<580 else 3
        rows=(len(self.spec['nodes'])+columns-1)//columns
        self.setMinimumHeight(max(340,rows*92+max(0,rows-1)*24+60))

    def resizeEvent(self,event):
        self._height_for_nodes();super().resizeEvent(event)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(),T.color(T.BG2))
        nodes=self.spec['nodes'];self.boxes={}
        if not nodes:return
        columns=2 if self.width()<580 else 3
        rows=(len(nodes)+columns-1)//columns
        gap=24;pad=18;cell=(self.width()-2*pad-(columns-1)*gap)/columns
        height=92;total=rows*height+(rows-1)*gap
        top=max(32,(self.height()-total)/2)
        for index,node in enumerate(nodes):
            row,column=divmod(index,columns)
            self.boxes[node['id']]=QRectF(pad+column*(cell+gap),top+row*(height+gap),cell,height)
        for edge in self.spec['edges']:
            a=self.boxes[edge['source']];b=self.boxes[edge['target']]
            if a.top()==b.top():start=QPointF(a.right(),a.center().y());end=QPointF(b.left(),b.center().y())
            else:start=QPointF(a.center().x(),a.bottom());end=QPointF(b.center().x(),b.top())
            path=QPainterPath(start)
            if a.top()==b.top():path.lineTo(end)
            else:
                middle=(start.y()+end.y())/2
                path.cubicTo(QPointF(start.x(),middle),QPointF(end.x(),middle),end)
            p.setPen(QPen(T.color(T.BLUE if edge['label']=='memory' else T.CYAN_DIM),1.4,Qt.PenStyle.DashLine if edge['label']=='memory' else Qt.PenStyle.SolidLine))
            p.drawPath(path)
            vector=end-path.pointAtPercent(.96)
            length=max(1,(vector.x()**2+vector.y()**2)**.5);ux,uy=vector.x()/length,vector.y()/length
            p.drawLine(end,QPointF(end.x()-7*ux+3*uy,end.y()-7*uy-3*ux))
            p.drawLine(end,QPointF(end.x()-7*ux-3*uy,end.y()-7*uy+3*ux))
        for node in nodes:
            box=self.boxes[node['id']];active=node['group']==self.selected
            p.setPen(QPen(T.color(T.CYAN if active else T.BORDER_HI),1.4 if active else 1))
            p.setBrush(T.color(T.PANEL2 if active else T.PANEL));p.drawRoundedRect(box,9,9)
            p.setFont(T.font(12,weight=600));p.setPen(T.color(T.CYAN if active else T.TEXT))
            p.drawText(box.adjusted(12,9,-10,-52),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,
                       p.fontMetrics().elidedText(node['title'],Qt.TextElideMode.ElideRight,int(box.width()-22)))
            p.setFont(T.font(10));p.setPen(T.color(T.TEXT2))
            p.drawText(box.adjusted(12,38,-10,-8),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop|Qt.TextFlag.TextWordWrap,node['detail'])
        p.setFont(T.font(10));p.setPen(T.color(T.DIM))
        p.drawText(QRectF(18,6,self.width()-36,24),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,'逻辑结构 · 实线数据 / 虚线存储依赖')

    def mousePressEvent(self,event):
        for node in self.spec['nodes']:
            if self.boxes.get(node['id'],QRectF()).contains(event.position()):
                self.selected=node['group'];self.module_selected.emit(self.selected);self.update();return
        super().mousePressEvent(event)

    def keyPressEvent(self,event):
        groups=list(dict.fromkeys(node['group'] for node in self.spec['nodes']))
        if groups and event.key() in (Qt.Key.Key_Left,Qt.Key.Key_Right,Qt.Key.Key_Down,Qt.Key.Key_Up):
            direction=1 if event.key() in (Qt.Key.Key_Right,Qt.Key.Key_Down) else -1
            index=groups.index(self.selected) if self.selected in groups else -1
            self.selected=groups[(index+direction)%len(groups)];self.module_selected.emit(self.selected);self.update();return
        super().keyPressEvent(event)
