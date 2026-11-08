"""芯片图鉴与参考文献。"""
from __future__ import annotations

from PySide6.QtCore import QSize as QtCoreQSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from ...data.blueprints import BLUEPRINTS, BLUEPRINT_BY_ID
from ...data.nodes import NODES
from ...data.sources import SOURCES, TIER_LABELS
from .. import theme as T
from ..widgets import Card, DieSchematic, Pill, Stat


class CodexScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 18, 22, 18)
        root.setSpacing(14)

        left = QVBoxLayout()
        title = QLabel("芯片图鉴")
        title.setStyleSheet(f"color:{T.TEXT}; font-size:22px; font-weight:800;")
        left.addWidget(title)
        sub = QLabel("公开资料参考与前瞻实验输入。每项标注数据状态；估算配置不能视为已确认规格。")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        left.addWidget(sub)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("筛选芯片 / 厂商 / 年份 / 制程…")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._populate)
        left.addWidget(self.filter)
        self.list = QListWidget()
        self.list.setMinimumWidth(230)
        self.list.setMaximumWidth(290)
        self.list.currentRowChanged.connect(self._select)
        left.addWidget(self.list, 1)
        back = QPushButton("← 返回")
        back.clicked.connect(lambda: win.go("start"))
        left.addWidget(back)
        root.addLayout(left, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.page = QWidget()
        self.detail = QVBoxLayout(self.page)
        self.detail.setContentsMargins(4, 0, 8, 0)
        self.detail.setSpacing(12)
        self.scroll.setWidget(self.page)
        root.addWidget(self.scroll, 1)

    def _populate(self, q: str = ""):
        cur = self.list.currentItem().data(Qt.ItemDataRole.UserRole) if self.list.currentItem() else None
        terms = [t for t in q.lower().split() if t]
        self.list.blockSignals(True)
        self.list.clear()
        for b in BLUEPRINTS:
            hay = f"{b['name']} {b['vendor']} {b['year']} {b['node']} {b['cpu']} {b['gpu']}".lower()
            if all(t in hay for t in terms):
                it = QListWidgetItem(f"{b['name']}\n{b['vendor']} · {b['year']} · {b['node'].upper()}")
                it.setData(Qt.ItemDataRole.UserRole, b["id"])
                it.setSizeHint(QtCoreQSize(220, 48))
                self.list.addItem(it)
        self.list.blockSignals(False)
        if self.list.count():
            idx = 0
            if cur:
                for i in range(self.list.count()):
                    if self.list.item(i).data(Qt.ItemDataRole.UserRole) == cur:
                        idx = i
                        break
            self.list.setCurrentRow(idx)
            self._select(idx)
        else:
            self._clear_detail()
            empty = QLabel("没有匹配的芯片。可以按厂商、型号或年份重新筛选。")
            empty.setObjectName("Dim")
            self.detail.addWidget(empty)
            self.detail.addStretch(1)

    def _select(self, row: int):
        if row < 0 or row >= self.list.count():
            return
        b = BLUEPRINT_BY_ID[self.list.item(row).data(Qt.ItemDataRole.UserRole)]
        self._clear_detail()
        self._show_detail(b)

    def _clear_detail(self):
        while self.detail.count():
            it = self.detail.takeAt(0)
            w = it.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
            elif it.layout():
                while it.layout().count():
                    x = it.layout().takeAt(0)
                    widget=x.widget()
                    if widget:
                        widget.hide()
                        widget.setParent(None)
                        widget.deleteLater()

    def _show_detail(self, b):
        uncertain = b.get("data_status") == "unverified"
        status = QLabel("游戏研究配置 · 芯片名称不代表参数已获厂商验证；PPA、分数、尺寸和布局为独立假设")
        status.setObjectName("Amber" if uncertain else "Muted")
        status.setWordWrap(True)
        self.detail.addWidget(status)
        head = QHBoxLayout()
        name = QLabel(b["name"])
        name.setStyleSheet(f"color:{T.TEXT}; font-size:26px; font-weight:800;")
        head.addWidget(name)
        head.addStretch(1)
        head.addWidget(Pill(b["vendor"], T.CYAN))
        head.addWidget(Pill(NODES[b["node"]]["name"], T.BLUE))
        head.addWidget(Pill(f"{b['die_area']} mm²", T.AMBER))
        self.detail.addLayout(head)

        meta = QLabel(f"{b['cpu']}   ·   {b['gpu']}   ·   {b['cache']}")
        meta.setWordWrap(True)
        meta.setStyleSheet(f"color:{T.TEXT2}; font-size:12px;")
        self.detail.addWidget(meta)

        top = QHBoxLayout()
        top.setSpacing(12)
        dc = Card("功能布局示意", "不声称真实 die 布局")
        sch = DieSchematic(b.get("layout"), b.get("die_aspect", 1.0))
        dc.add(sch)
        top.addWidget(dc, 3)
        sc = Card("研究参考分数", "非已核验实测记录")
        g = QGridLayout()
        g.setSpacing(6)
        for i, (k, title) in enumerate([("st", "单核"), ("mt", "多核"), ("gpu", "GPU")]):
            s = Stat(title, str(b["scores"].get(k, "—")))
            g.addWidget(s, i // 2, i % 2)
        sc.add_layout(g)
        top.addWidget(sc, 2)
        self.detail.addLayout(top)

        ic = Card("设计解读")
        txt = QLabel(b["insight"])
        txt.setWordWrap(True)
        txt.setStyleSheet(f"color:{T.TEXT2}; font-size:12px; line-height:1.75;")
        ic.add(txt)
        self.detail.addWidget(ic)

        ec = Card("参考来源", "证据类型不等于内容已经核验")
        for sid in b.get("evidence", []):
            src = SOURCES.get(sid)
            if not src:
                continue
            row = QHBoxLayout()
            t = src["tier"]
            row.addWidget(Pill(f"T{t} {TIER_LABELS[t]}", T.TIER_COLORS.get(t, T.DIM)))
            state = "正文已核验" if src["verification"] == "fulltext_checked" else "仅书目已核验"
            lab = QLabel(f"{src['title']} · {state}\n支持：{src['supports']}\n不支持：{src['does_not_support']}")
            lab.setWordWrap(True)
            lab.setStyleSheet(f"color:{T.TEXT2}; font-size:10px;")
            row.addWidget(lab, 1)
            ec.add_layout(row)
        conf = QLabel("参数来源：game_assumption。除上述明确的结构事实外，未进行真实芯片数值校准。")
        conf.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        ec.add(conf)
        self.detail.addWidget(ec)

        if b.get("build"):
            go = QPushButton("载入近似研究配置  →")
            go.setObjectName("Primary")
            go.setFixedHeight(38)
            go.clicked.connect(lambda: self.win.load_blueprint_as_design(b))
            self.detail.addWidget(go)
        self.detail.addStretch(1)

    def select_id(self, bid: str):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole) == bid:
                self.list.setCurrentRow(i)
                self._select(i)
                return
        self.filter.clear()
        self._populate("")
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole) == bid:
                self.list.setCurrentRow(i)
                self._select(i)
                return

    def refresh(self):
        self._populate(self.filter.text())


class SourcesScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 18, 28, 18)
        outer.setSpacing(10)
        head = QHBoxLayout()
        t = QLabel("文献 · 原文定位与使用范围")
        t.setStyleSheet(f"color:{T.TEXT}; font-size:24px; font-weight:800;")
        head.addWidget(t)
        head.addStretch(1)
        back = QPushButton("← 返回")
        back.clicked.connect(lambda: win.go("start"))
        head.addWidget(back)
        outer.addLayout(head)
        note = QLabel("正式资料逐项区分正文核验和仅书目核验。展开的支持/不支持内容限定其使用范围；模型数字没有自动获得文献背书。原有 99 条引用的处置可查看审计记录。")
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{T.DIM}; font-size:11px; line-height:1.6;")
        outer.addWidget(note)
        archive = QPushButton("查看 99 条遗留引用的逐项审计")
        archive.clicked.connect(self._audit)
        outer.addWidget(archive)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(2, 2, 10, 2)
        lay.setSpacing(8)
        scroll.setWidget(page)
        outer.addWidget(scroll, 1)

        for tier in (1, 2, 3, 4):
            h = QLabel(f"T{tier} · {TIER_LABELS[tier]}")
            h.setStyleSheet(f"color:{T.TIER_COLORS[tier]}; font-size:14px; font-weight:700; margin-top:8px;")
            lay.addWidget(h)
            for sid, s in SOURCES.items():
                if s["tier"] != tier:
                    continue
                card = QFrame()
                card.setObjectName("Panel2")
                card.setStyleSheet(f"QFrame#Panel2 {{ background:{T.PANEL}; border:1px solid {T.BORDER}; border-radius:8px; }}")
                cl = QVBoxLayout(card)
                cl.setContentsMargins(12, 9, 12, 9)
                cl.setSpacing(3)
                title = QLabel(s["title"])
                title.setWordWrap(True)
                title.setStyleSheet(f"color:{T.TEXT}; font-size:12px; font-weight:600;")
                cl.addWidget(title)
                state = "正文与范围已核验" if s["verification"] == "fulltext_checked" else "仅书目已核验 · 全文结论不背书"
                meta = QLabel(f"{s.get('authors','')} · {s.get('venue','')} · {s.get('year','')} · {state}")
                meta.setWordWrap(True)
                meta.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
                cl.addWidget(meta)
                for key,title in (("locator","原文定位"),("supports","支持"),("does_not_support","不支持"),("model_use","本作使用")):
                    n = QLabel(title+"："+s[key])
                    n.setWordWrap(True)
                    n.setStyleSheet(f"color:{T.TEXT2}; font-size:10px;")
                    cl.addWidget(n)
                if s.get("url"):
                    u = QLabel(f'<a href="{s["url"]}" style="color:{T.BLUE}; text-decoration:none;">{s["url"]}</a>')
                    u.setOpenExternalLinks(True)
                    u.setStyleSheet("font-size:10px;")
                    cl.addWidget(u)
                lay.addWidget(card)
        lay.addStretch(1)

    def _audit(self):
        from pathlib import Path
        from ..search import InfoDialog
        path=Path(__file__).resolve().parents[3]/"docs/research/LEGACY_AUDIT.md"
        InfoDialog(self,"遗留证据审计","每项处置与原因；未把未知内容判为不存在",path.read_text("utf-8")).exec()

    def refresh(self):
        pass
