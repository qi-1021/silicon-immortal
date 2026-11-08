"""全局搜索与详情对话框。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPlainTextEdit,
                               QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from .. import search_index
from . import theme as T

KIND_LABEL = {"chip": "芯片", "core": "核心", "source": "文献", "tutorial": "教学",
              "node": "制程", "gpu": "GPU", "lab_course": "LAB 课程"}
KIND_COLOR = {"chip": T.CYAN, "core": T.AMBER, "source": T.BLUE,
              "tutorial": T.PURPLE, "node": T.GREEN, "gpu": T.PINK}


class InfoDialog(QDialog):
    def __init__(self, parent, title: str, meta: str, body: str,
                 use_label: str | None = None, on_use=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(560, 420)
        self.setStyleSheet(f"QDialog {{ background:{T.BG}; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(8)
        t = QLabel(title)
        t.setWordWrap(True)
        t.setStyleSheet(f"color:{T.TEXT}; font-size:20px; font-weight:800;")
        lay.addWidget(t)
        m = QLabel(meta)
        m.setWordWrap(True)
        m.setStyleSheet(f"color:{T.CYAN}; font-size:11px;")
        lay.addWidget(m)
        b = QPlainTextEdit()
        b.setReadOnly(True)
        b.setPlainText(body)
        b.setFont(T.font(12))
        lay.addWidget(b, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        if use_label and on_use:
            use = QPushButton(use_label)
            use.setObjectName("Primary")
            use.clicked.connect(lambda: (on_use(), self.accept()))
            row.addWidget(use)
        close = QPushButton("关闭")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)


class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("查找")
        self.resize(700, 540)
        self.setStyleSheet(f"QDialog {{ background:{T.BG}; }}")
        self.choice: dict | None = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(8)
        t = QLabel("查找")
        t.setStyleSheet(f"color:{T.TEXT}; font-size:20px; font-weight:800;")
        lay.addWidget(t)
        self.query = QLineEdit()
        self.query.setPlaceholderText("芯片 / 核心 / 文献 / 教学 / 制程 / GPU…")
        self.query.setClearButtonEnabled(True)
        self.query.textChanged.connect(self._search)
        lay.addWidget(self.query)
        self.results = QListWidget()
        self.results.itemActivated.connect(self._activate)
        self.results.itemDoubleClicked.connect(self._activate)
        lay.addWidget(self.results, 1)
        hint = QLabel("双击打开；也可以直接回车。支持多个关键词，例如 “RISC-V 2025”。")
        hint.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        lay.addWidget(hint)
        self.query.setFocus()

    def _search(self, q: str):
        self.results.clear()
        for item in search_index.search(q, 60):
            label = KIND_LABEL.get(item["kind"], item["kind"])
            it = QListWidgetItem(f"[{label}]  {item['title']}\n{item['subtitle']}")
            it.setData(Qt.ItemDataRole.UserRole, item)
            self.results.addItem(it)
        if q.strip() and self.results.count() == 0:
            it = QListWidgetItem("没有找到。试试更短的关键词，例如 “X925” 或 “CACTI”。")
            it.setFlags(Qt.ItemFlag.NoItemFlags)
            self.results.addItem(it)

    def _activate(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.choice = data
            self.accept()
