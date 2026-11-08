"""教学关卡：一课一个决策，实时勾选目标。"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ...data.tutorials import TUTORIALS, TUTORIAL_BY_ID
from .. import anim
from .. import theme as T
from ..widgets import Card, Pill


def _clear(lay):
    while lay.count():
        it = lay.takeAt(0)
        w = it.widget()
        if w:
            w.hide()
            w.setParent(None)
            w.deleteLater()
        elif it.layout():
            _clear(it.layout())


class TutorialScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.preview_id: str | None = None
        self.step_widgets: list[dict] = []
        self.success: QLabel | None = None
        self._marked = set()

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 16, 22, 16)
        root.setSpacing(14)

        left = QVBoxLayout()
        title = QLabel("教学关卡")
        title.setStyleSheet(f"color:{T.TEXT}; font-size:22px; font-weight:800;")
        left.addWidget(title)
        sub = QLabel("每课只教一个决策；目标会随你的修改实时勾选。")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        left.addWidget(sub)
        advanced = QPushButton("进阶课程 · ISA / 微架构 LAB")
        advanced.clicked.connect(lambda: win.go("labs"))
        left.addWidget(advanced)
        self.list = QListWidget()
        self.list.setMinimumWidth(250)
        self.list.setMaximumWidth(300)
        self.list.currentRowChanged.connect(self._select)
        left.addWidget(self.list, 1)
        back = QPushButton("← 返回主菜单")
        back.clicked.connect(lambda: win.go("start"))
        left.addWidget(back)
        root.addLayout(left, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.page = QWidget()
        self.detail = QVBoxLayout(self.page)
        self.detail.setContentsMargins(2, 0, 8, 0)
        self.detail.setSpacing(10)
        scroll.setWidget(self.page)
        root.addWidget(scroll, 1)

    # ---------- list ----------
    def _fill_list(self):
        self.list.blockSignals(True)
        self.list.clear()
        done = self.win.progress.get("tutorials", {})
        current = self.win.tutorial_id or self.preview_id
        for i, t in enumerate(TUTORIALS):
            mark = "✓ " if done.get(t["id"]) else f"{i+1:02d} "
            it = QListWidgetItem(f"{mark}{t['title']}\n{t['tag']}")
            it.setData(Qt.ItemDataRole.UserRole, t["id"])
            it.setSizeHint(QSize(240, 52))
            self.list.addItem(it)
            if t["id"] == current:
                self.list.setCurrentRow(i)
        if self.list.currentRow() < 0 and self.list.count():
            self.list.setCurrentRow(0)
        if self.list.currentRow() >= 0:
            self.preview_id = self.list.currentItem().data(Qt.ItemDataRole.UserRole)
        self.list.blockSignals(False)

    def _select(self, row: int):
        if row < 0 or row >= self.list.count():
            return
        self.preview_id = self.list.item(row).data(Qt.ItemDataRole.UserRole)
        if self.win.tutorial_id == self.preview_id:
            self._show_run()
        else:
            self._show_preview()

    # ---------- preview ----------
    def _show_preview(self):
        _clear(self.detail)
        self.step_widgets = []
        t = TUTORIAL_BY_ID.get(self.preview_id or "")
        if not t:
            lab = QLabel("选择左侧一节课。")
            lab.setStyleSheet(f"color:{T.DIM}; font-size:12px;")
            self.detail.addWidget(lab)
            return
        head = QHBoxLayout()
        h = QLabel(t["title"])
        h.setStyleSheet(f"color:{T.TEXT}; font-size:26px; font-weight:800;")
        head.addWidget(h)
        head.addStretch(1)
        head.addWidget(Pill(t["tag"], T.CYAN))
        self.detail.addLayout(head)

        c = Card("本课概念")
        lab = QLabel(t["concept"])
        lab.setWordWrap(True)
        lab.setStyleSheet(f"color:{T.TEXT2}; font-size:13px; line-height:1.7;")
        c.add(lab)
        intro = QLabel(t["intro"])
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color:{T.DIM}; font-size:11px; line-height:1.7;")
        c.add(intro)
        self.detail.addWidget(c)

        sc = Card("目标")
        for i, s in enumerate(t["steps"]):
            row = QLabel(f"{i+1}. {s['title']}")
            row.setStyleSheet(f"color:{T.TEXT2}; font-size:12px; padding:2px 0;")
            sc.add(row)
        self.detail.addWidget(sc)

        start = QPushButton("开始这一课  →")
        start.setObjectName("Primary")
        start.setFixedHeight(42)
        start.clicked.connect(lambda: self.win.start_tutorial(t["id"]))
        self.detail.addWidget(start)
        self.detail.addStretch(1)

    # ---------- run ----------
    def _show_run(self):
        self._prev_done = []
        _clear(self.detail)
        self.step_widgets = []
        t = TUTORIAL_BY_ID.get(self.win.tutorial_id or "")
        if not t:
            self._show_preview()
            return
        head = QHBoxLayout()
        h = QLabel(t["title"])
        h.setStyleSheet(f"color:{T.TEXT}; font-size:25px; font-weight:800;")
        head.addWidget(h)
        head.addStretch(1)
        head.addWidget(Pill(t["tag"], T.AMBER))
        self.detail.addLayout(head)

        intro = QLabel(t["intro"])
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color:{T.TEXT2}; font-size:12px; line-height:1.7;")
        self.detail.addWidget(intro)

        if t.get("lecture"):
            lc = Card("讲义")
            lec = QLabel(t["lecture"])
            lec.setWordWrap(True)
            lec.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; line-height:1.85;")
            lc.add(lec)
            self.detail.addWidget(lc)

        self.success = QLabel("")
        self.success.setWordWrap(True)
        self.success.setStyleSheet(
            f"color:{T.GREEN}; background:{T.rgba(T.GREEN, 0.08)};"
            f"border:1px solid {T.rgba(T.GREEN, 0.3)}; border-radius:8px;"
            f"padding:10px 12px; font-size:12px;")
        self.success.hide()
        self.detail.addWidget(self.success)

        for i, s in enumerate(t["steps"]):
            frame = QFrame()
            frame.setObjectName("Panel2")
            row = QHBoxLayout(frame)
            row.setContentsMargins(12, 10, 12, 10)
            row.setSpacing(10)
            icon = QLabel("○")
            icon.setFixedWidth(22)
            icon.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            icon.setStyleSheet(f"color:{T.DIM}; font-size:17px; font-weight:700;")
            row.addWidget(icon)
            box = QVBoxLayout()
            box.setSpacing(2)
            title = QLabel(f"{i+1}. {s['title']}")
            title.setStyleSheet(f"color:{T.TEXT}; font-size:13px; font-weight:600;")
            box.addWidget(title)
            text = QLabel(s["text"])
            text.setWordWrap(True)
            text.setStyleSheet(f"color:{T.TEXT2}; font-size:11px;")
            box.addWidget(text)
            hint = QLabel("提示：" + s["hint"])
            hint.setWordWrap(True)
            hint.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
            box.addWidget(hint)
            row.addLayout(box, 1)
            go = QPushButton("去操作 →")
            go.setFixedWidth(92)
            go.clicked.connect(lambda _, scr=s["screen"]: self.win.go(scr))
            row.addWidget(go, 0, Qt.AlignmentFlag.AlignTop)
            self.detail.addWidget(frame)
            self.step_widgets.append(dict(frame=frame, icon=icon, title=title))

        btns = QHBoxLayout()
        restart = QPushButton("重新开始")
        restart.clicked.connect(lambda: self.win.start_tutorial(t["id"]))
        btns.addWidget(restart)
        lst = QPushButton("教学列表")
        lst.clicked.connect(self._back_list)
        btns.addWidget(lst)
        btns.addStretch(1)
        self.next_btn = QPushButton("下一课  →")
        self.next_btn.setObjectName("Primary")
        self.next_btn.setFixedHeight(38)
        self.next_btn.clicked.connect(self._next)
        self.next_btn.hide()
        btns.addWidget(self.next_btn)
        self.detail.addLayout(btns)
        self.detail.addStretch(1)
        self._update_checks()

    def _back_list(self):
        self.win.tutorial_id = None
        self._fill_list()
        self._show_preview()

    def _next(self):
        done = [t["id"] for t in TUTORIALS]
        cur = self.win.tutorial_id
        if cur in done:
            i = done.index(cur)
            nxt = done[(i + 1) % len(done)]
            self.win.start_tutorial(nxt)

    def _update_checks(self):
        t = TUTORIAL_BY_ID.get(self.win.tutorial_id or "")
        if not t or not self.win.result or not self.step_widgets:
            return
        d, r = self.win.design, self.win.result
        done = []
        for s in t["steps"]:
            try:
                done.append(bool(s["check"](d, r)))
            except Exception:
                done.append(False)
        prev = getattr(self, "_prev_done", [])
        for i, w in enumerate(self.step_widgets):
            if i < len(prev) and not prev[i] and done[i]:
                anim.flash(w["icon"])
        self._prev_done = list(done)
        first_open = next((i for i, v in enumerate(done) if not v), len(done))
        for i, w in enumerate(self.step_widgets):
            if i < first_open:
                w["icon"].setText("✓")
                w["icon"].setStyleSheet(f"color:{T.GREEN}; font-size:15px; font-weight:800;")
                w["frame"].setStyleSheet(
                    f"QFrame#Panel2 {{ background:{T.rgba(T.GREEN, 0.045)};"
                    f"border:1px solid {T.rgba(T.GREEN, 0.22)}; border-radius:8px; }}")
                w["title"].setStyleSheet(f"color:{T.GREEN}; font-size:13px; font-weight:600;")
            elif i == first_open:
                w["icon"].setText("●")
                w["icon"].setStyleSheet(f"color:{T.CYAN}; font-size:15px;")
                w["frame"].setStyleSheet(
                    f"QFrame#Panel2 {{ background:{T.rgba(T.CYAN, 0.045)};"
                    f"border:1px solid {T.rgba(T.CYAN, 0.45)}; border-radius:8px; }}")
                w["title"].setStyleSheet(f"color:{T.TEXT}; font-size:13px; font-weight:600;")
            else:
                w["icon"].setText("○")
                w["icon"].setStyleSheet(f"color:{T.DIM}; font-size:16px;")
                w["frame"].setStyleSheet(
                    f"QFrame#Panel2 {{ background:{T.PANEL}; border:1px solid {T.BORDER}; border-radius:8px; }}")
                w["title"].setStyleSheet(f"color:{T.TEXT2}; font-size:13px; font-weight:600;")
        if all(done):
            self.success.setText("✓ 本课完成。你已经掌握了这个决策；可以进入下一课，或回到主菜单选关卡。")
            self.success.show()
            self.next_btn.show()
            if t["id"] not in self._marked:
                self._marked.add(t["id"])
                self.win.progress.setdefault("tutorials", {})[t["id"]] = True
                self.win.persist()
                self._fill_list()
        else:
            self.success.hide()
            self.next_btn.hide()

    def select_id(self, tid: str):
        self.win.tutorial_id = None
        self.preview_id = tid
        self._fill_list()
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole) == tid:
                self.list.setCurrentRow(i)
                break
        self._show_preview()

    def refresh(self):
        self._fill_list()
        if self.win.tutorial_id:
            self._show_run()
        else:
            self._show_preview()

    def on_result(self):
        self._update_checks()
