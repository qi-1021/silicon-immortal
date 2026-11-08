"""独立自由方案入口；诊断提示不伪装成可制造性认证。"""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QScrollArea,QFileDialog
from ..widgets import Card


class SandboxScreen(QWidget):
    def __init__(self,win):
        super().__init__();self.win=win
        outer=QVBoxLayout(self);outer.setContentsMargins(28,24,28,24)
        heading=QLabel('自由沙盒 · 独立工作区');heading.setObjectName('H1');outer.addWidget(heading)
        info=QLabel('不设产品通关门槛，可选择全部已实现的制程和核心。签核解释风险，允许继续生成预览。方案单独保存，切换产品项目不会覆盖。软件资源上限与模型无法解释的输入仍有边界。')
        info.setWordWrap(True);info.setObjectName('Dim');outer.addWidget(info)
        actions=QHBoxLayout()
        for title,action in [('编辑架构',lambda:win.go('architecture')),('设计核心 · LAB',lambda:win.go('studio')),
                             ('签核诊断',lambda:win.go('signoff')),('生成设计预览',win.tape_out),('导出.sil',self.export)]:
            button=QPushButton(title);button.clicked.connect(action);actions.addWidget(button)
        outer.addLayout(actions)
        scroll=QScrollArea();scroll.setWidgetResizable(True);page=QWidget();body=QVBoxLayout(page);scroll.setWidget(page);outer.addWidget(scroll,1)
        summary=Card('当前自由方案');self.summary=QLabel();self.summary.setWordWrap(True);summary.add(self.summary);body.addWidget(summary)
        diagnostic=Card('可能的问题 · 原因 · 解决方向','诊断不是阻塞，也不代表物理设计已经验证')
        self.issues=QLabel();self.issues.setWordWrap(True);diagnostic.add(self.issues);body.addWidget(diagnostic)
        boundary=Card('谁负责什么')
        label=QLabel('芯片侧：核心资源、缓存、互连、功耗、金属供电网、封装热阻。\n设备侧：机身、散热器、环境温度、负载与持续功耗预算。\n本版PDN可设置等效电阻或投入映射，散热器作为设备场景。无真实电源网提取、热机械或PDK签核。')
        label.setWordWrap(True);boundary.add(label);body.addWidget(boundary);body.addStretch(1)
        bottom=QHBoxLayout()
        fresh=QPushButton('新建自由方案');fresh.clicked.connect(lambda:win.start_sandbox(fresh=True));bottom.addWidget(fresh)
        self.back=QPushButton('返回之前的产品方案');self.back.clicked.connect(win.return_to_project);bottom.addWidget(self.back);outer.addLayout(bottom)

    def refresh(self):
        d=self.win.design;r=self.win.result
        if not d or d.scenario_id!='sandbox' or not r:return
        self.summary.setText(f"{d.name or '未命名'}\n{len(d.cores)}个CPU组 · {sum(g.count for g in d.cores)}实例 · Die {r['die_area']:.1f}mm² · 峰值{r['power']['peak']:.2f}W\n核心模板和自定义IP随.sil携带，草稿与产品项目分开。")
        issues=r['signoff']['diagnostics']
        self.issues.setText('\n\n'.join('○ '+c['title']+'\n原因：'+c['explanation']+'\n方向：'+c['remedy'] for c in issues) if issues else '当前参考条件下未发现签核代理项问题。实际芯片仍需要RTL/PDK与设备验证。')
        if r['warnings']:
            self.issues.setText(self.issues.text()+'\n\n其它模型观察：\n'+'\n'.join('· '+w for w in r['warnings']))
        self.back.setEnabled(bool(self.win.project_workspace))

    def on_result(self):self.refresh()

    def export(self):
        from ...export import export_to
        path,_=QFileDialog.getSaveFileName(self,'导出自由方案','自由设计.sil','Silicon SoC (*.sil)')
        if path:export_to(path,self.win.design,self.win.result)
