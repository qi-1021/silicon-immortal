"""后台更新查询、镜像设置和退出后的事务安装。"""
import os
from pathlib import Path
import subprocess
import sys

from PySide6.QtCore import QThread,Signal,Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QPlainTextEdit,QProgressBar,QMessageBox,QScrollArea)
from ..paths import resource_root,player_data_dir
from ..updates import DEFAULT_MIRRORS,normalize_mirrors,check_updates,download_update
from ..version import GAME_VERSION


class UpdateWorker(QThread):
    message=Signal(str)
    progress=Signal(int,int)
    checked=Signal(dict)
    downloaded=Signal(dict)
    failed=Signal(str)

    def __init__(self,task,mirrors,release=None,parent=None):
        super().__init__(parent);self.task=task;self.mirrors=mirrors;self.release=release

    def run(self):
        try:
            if self.task=='check':
                self.checked.emit(check_updates(GAME_VERSION,self.mirrors,notify=self.message.emit))
            else:
                self.downloaded.emit(download_update(self.release,player_data_dir()/'updates',self.mirrors,
                    notify=self.message.emit,progress=self.progress.emit))
        except Exception as ex:self.failed.emit(str(ex))


class UpdatesScreen(QWidget):
    def __init__(self,win):
        super().__init__();self.win=win;self.worker=None;self.release=None;self.package=None
        outer=QVBoxLayout(self);outer.setContentsMargins(24,18,24,18)
        heading=QHBoxLayout();title=QLabel('软件更新');title.setObjectName('H2');heading.addWidget(title)
        heading.addStretch(1);current=QLabel('当前 '+GAME_VERSION);current.setObjectName('Cyan');heading.addWidget(current);outer.addLayout(heading)
        scroll=QScrollArea();scroll.setWidgetResizable(True);outer.addWidget(scroll,1)
        page=QWidget();body=QVBoxLayout(page);body.setContentsMargins(12,12,12,12);body.setSpacing(12);scroll.setWidget(page)
        self.version=QLabel('尚未检查');self.version.setObjectName('H3');self.version.setWordWrap(True);body.addWidget(self.version)
        self.status=QLabel('Forgejo优先，GitHub代理镜像与原站备用。');self.status.setTextFormat(Qt.TextFormat.PlainText);self.status.setWordWrap(True);self.status.setObjectName('Dim');body.addWidget(self.status)
        self.progress=QProgressBar();self.progress.setRange(0,100);self.progress.hide();body.addWidget(self.progress)
        buttons=QHBoxLayout();body.addLayout(buttons)
        self.check_btn=QPushButton('检查更新');self.check_btn.setObjectName('Primary');self.check_btn.clicked.connect(self.check);buttons.addWidget(self.check_btn)
        self.download_btn=QPushButton('下载并校验');self.download_btn.clicked.connect(self.download);self.download_btn.setEnabled(False);buttons.addWidget(self.download_btn)
        self.install_btn=QPushButton('安装并重启');self.install_btn.clicked.connect(self.install);self.install_btn.setEnabled(False);buttons.addWidget(self.install_btn);buttons.addStretch(1)
        self.notes=QPlainTextEdit();self.notes.setReadOnly(True);self.notes.setMinimumHeight(180);self.notes.setPlaceholderText('发布说明');body.addWidget(self.notes,1)
        title=QLabel('GitHub代理镜像');title.setObjectName('H3');body.addWidget(title)
        self.mirrors=QPlainTextEdit();self.mirrors.setMaximumHeight(115);self.mirrors.setPlaceholderText('https://mirror.example/');body.addWidget(self.mirrors)
        actions=QHBoxLayout();body.addLayout(actions)
        button=QPushButton('保存镜像设置');button.clicked.connect(self.save_settings);actions.addWidget(button)
        button=QPushButton('恢复默认镜像');button.clicked.connect(self.reset_settings);actions.addWidget(button);actions.addStretch(1)
        note=QLabel('只替换发布清单中的程序文件，保留存档、虚拟环境与个人设计；失败后恢复备份。Git开发目录或本地源码有改动时不自动覆盖。\n代理只填写HTTPS前缀，每行一个。第三方镜像不保证持续可用；SHA-256是完整性校验，不是发布者数字签名。')
        note.setTextFormat(Qt.TextFormat.PlainText);note.setWordWrap(True);note.setObjectName('Muted');body.addWidget(note)

    def restore_settings(self):
        settings=self.win.update_settings
        try:mirrors=normalize_mirrors(settings.get('mirrors',DEFAULT_MIRRORS)) if isinstance(settings,dict) else list(DEFAULT_MIRRORS)
        except ValueError:mirrors=list(DEFAULT_MIRRORS)
        self.win.update_settings=dict(mirrors=mirrors);self.mirrors.setPlainText('\n'.join(mirrors))

    def save_settings(self):
        if self.worker:return False
        try:
            mirrors=normalize_mirrors([line.strip() for line in self.mirrors.toPlainText().splitlines() if line.strip()])
            self.win.update_settings=dict(mirrors=mirrors);self.win.persist()
            self.status.setText('已保存镜像设置；Forgejo优先，所列代理依次备用。');return True
        except ValueError as ex:self.status.setText(str(ex));return False

    def reset_settings(self):
        if not self.worker:self.mirrors.setPlainText('\n'.join(DEFAULT_MIRRORS));self.save_settings()

    def _start(self,task):
        if self.worker or not self.save_settings():return
        self.download_btn.setEnabled(False);self.install_btn.setEnabled(False);self.check_btn.setEnabled(False);self.mirrors.setEnabled(False)
        self.progress.setRange(0,0);self.progress.show()
        worker=self.worker=UpdateWorker(task,list(self.win.update_settings['mirrors']),self.release,self)
        worker.message.connect(self.status.setText);worker.progress.connect(self._progress)
        worker.checked.connect(self._checked);worker.downloaded.connect(self._downloaded);worker.failed.connect(self._failed)
        worker.finished.connect(self._finished);worker.start()

    def check(self):
        if self.worker:return
        self.release=None;self.package=None;self.download_btn.setEnabled(False);self.install_btn.setEnabled(False);self._start('check')

    def download(self):
        if self.release and not self.worker:self._start('download')

    def _progress(self,received,total):
        if total>0:self.progress.setRange(0,100);self.progress.setValue(min(100,received*100//total))
        self.status.setText(f'下载 {received/1048576:.1f} MB'+(f' / {total/1048576:.1f} MB' if total else ''))

    def _checked(self,result):
        release=result['release'];self.release=release if result['available'] else None
        self.version.setText(('可更新至 ' if result['available'] else '当前可获取版本 ')+release['version'])
        self.notes.setPlainText(release.get('notes') or '此镜像只转发版本与附件，未提供发布说明。')
        self.status.setText(('发现新版本。来源：' if result['available'] else '未发现更新。来源：')+release['base']+
            ('\n部分来源不可达：\n'+'\n'.join(result['errors']) if result['errors'] else ''))
        self.download_btn.setEnabled(result['available'])

    def _downloaded(self,package):
        self.package=package;self.progress.setRange(0,100);self.progress.setValue(100)
        guard=(resource_root()/'.git').exists() or getattr(sys,'frozen',False)
        self.install_btn.setEnabled(not guard)
        self.status.setText(f"已校验 {package['version']}\n来源：{package['source']}\nSHA-256：{package['sha256']}\n暂存：{package['stage']}"+
            ('\n当前为Git开发目录或打包程序，禁止自动覆盖。源码安装版可安装并重启。' if guard else '\n可以安装并重启。退出前保存当前存档。'))

    def _failed(self,message):
        self.status.setText(message);self.package=None;self.install_btn.setEnabled(False)

    def _finished(self):
        worker=self.worker;self.worker=None
        if worker:worker.deleteLater()
        self.check_btn.setEnabled(True);self.download_btn.setEnabled(self.release is not None);self.mirrors.setEnabled(True)
        if not self.package:self.progress.hide()

    def busy(self):return self.worker is not None

    def install(self):
        if self.worker or not self.package:return
        root=resource_root()
        if (root/'.git').exists() or getattr(sys,'frozen',False):self.status.setText('Git开发目录或打包程序不自动覆盖。');return
        answer=QMessageBox.question(self,'安装更新',f"安装 {self.package['version']} 并重启？\n程序文件会备份，存档与个人设计保留。",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if answer!=QMessageBox.StandardButton.Yes:return
        try:
            self.win.persist();package=self.package;folder=Path(package['stage']).parent
            with (folder/'install.log').open('ab') as output:
                subprocess.Popen([sys.executable,str(package['installer']),'--root',str(root),'--stage',str(package['stage']),
                    '--wait-pid',str(os.getpid())],cwd=folder,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,
                    start_new_session=True,close_fds=True)
            self.win.close()
        except (OSError,ValueError) as ex:self.status.setText('未安排安装，当前程序未改动：'+str(ex))

    def refresh(self):pass
