"""开始界面：标题、关卡选择、图鉴入口。"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QPushButton, QVBoxLayout, QWidget)

from ...data.segments import SEGMENT_LIST
from ...data.tutorials import TUTORIALS
from .. import anim
from .. import theme as T
from ..silicon_render import render_silicon
from ..brand import logo_pixmap
from ...version import GAME_VERSION


class ScenarioCard(QFrame):
    clicked = Signal(str)

    def __init__(self, seg: dict, grade: dict | None = None, parent=None):
        super().__init__(parent)
        self.seg = seg
        self.setObjectName("Panel")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(seg["name"])
        self.setMinimumHeight(154)
        self.setStyleSheet(
            f"QFrame#Panel {{ background:{T.PANEL}; border:1px solid {T.BORDER}; border-radius:12px; }}"
            f"QFrame#Panel:hover, QFrame#Panel:focus {{ border-color:{T.CYAN_DIM}; background:{T.PANEL2}; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 13, 16, 13)
        lay.setSpacing(7)
        top = QHBoxLayout()
        name = QLabel(seg["name"].split(" · ")[0])
        name.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        top.addWidget(name)
        top.addStretch(1)
        if grade:
            g = QLabel('已完成' if grade.get('challenge_completed') else f"{grade.get('grade','')} 级")
            g.setStyleSheet(f"color:{T.CYAN}; font-size:10px; border:1px solid {T.rgba(T.CYAN, 0.33)}; border-radius:8px; padding:1px 7px;")
            top.addWidget(g)
        year = QLabel(str(seg["year"]))
        year.setStyleSheet(f"color:{T.DIM}; font-size:11px; font-family:{T.FONT_MONO};")
        top.addWidget(year)
        lay.addLayout(top)

        tag = QLabel(seg["tagline"])
        tag.setWordWrap(True)
        tag.setStyleSheet(f"color:{T.TEXT2}; font-size:12px;")
        lay.addWidget(tag)

        t = seg["targets"]
        stats = QLabel(seg.get('category') or f"ST {t['st']}   MT {t['mt']}   GPU {t['gpu']}   ${seg['ref_price']}")
        stats.setStyleSheet(f"color:{T.TEXT2}; font-size:11px; font-family:{T.FONT_MONO};")
        lay.addWidget(stats)
        lay.addStretch(1)
        budget = QLabel(f"预算 ${seg['budget_m']}M  ·  {seg['limits']['max_die_area']}mm² 上限")
        budget.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        lay.addWidget(budget)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit(self.seg["id"])
        super().mouseReleaseEvent(e)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit(self.seg["id"])
        else:
            super().keyPressEvent(event)


class StartScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        from PySide6.QtWidgets import QScrollArea
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        lay = QVBoxLayout(page)
        scroll.setWidget(page)
        outer.addWidget(scroll)
        lay.setContentsMargins(36, 30, 36, 26)
        lay.setSpacing(18)

        hero = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(8)
        self._entered = False
        mark=QLabel();mark.setPixmap(logo_pixmap(66));left.addWidget(mark)
        kicker = QLabel("SILICON IMMORTAL / "+GAME_VERSION.upper())
        self._kicker = kicker
        kicker.setStyleSheet(f"color:{T.CYAN}; font-size:10px; letter-spacing:2.6px; font-family:{T.FONT_MONO};")
        left.addWidget(kicker)
        title = QLabel("硅仙人")
        self._hero_title = title
        title.setStyleSheet(f"color:{T.TEXT}; font-size:46px; font-weight:700; letter-spacing:2px;")
        left.addWidget(title)
        sub = QLabel("一个人尽可用的芯片设计模拟器")
        self._hero_sub = sub
        sub.setWordWrap(True);sub.setStyleSheet(f"color:{T.TEXT2}; font-size:20px;")
        left.addWidget(sub)
        english=QLabel('a simulate silicon designer for everyone')
        english.setStyleSheet(f'color:{T.DIM};font-size:13px;');left.addWidget(english)
        tiny = QLabel("不要把它当作真实工具，这只是个游戏\ndon't take this for real one,it is just a game")
        tiny.setWordWrap(True)
        tiny.setStyleSheet(f"color:{T.DIM}; font-size:13px;")
        left.addWidget(tiny)
        powered=QLabel('powered by isqi');powered.setStyleSheet(f'color:{T.CYAN};font-size:12px;');left.addWidget(powered)
        hero.addLayout(left, 1)

        right = QVBoxLayout()
        right.setSpacing(8)
        visual = self.preview = QLabel("立项后，这里显示你的芯片")
        visual.setFixedSize(330, 240)
        visual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visual.setObjectName("Dim")
        right.addWidget(visual)
        credit = QLabel("当前设计 · 布局驱动的硅片示意")
        credit.setObjectName("Muted")
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(credit)
        self.cont = QPushButton("继续上次设计  →")
        self.cont.setObjectName("Primary")
        self.cont.setFixedHeight(40)
        self.cont.clicked.connect(lambda: self.win.go("architecture"))
        right.addWidget(self.cont)
        core_design=QPushButton('设计自己的核心 · LAB')
        core_design.clicked.connect(lambda:win.go('studio'));right.addWidget(core_design)
        sandbox=QPushButton('进入自由沙盒 · 独立方案');sandbox.clicked.connect(win.start_sandbox);right.addWidget(sandbox)
        how = QPushButton("教学关卡")
        how.clicked.connect(lambda: self.win.go("tutorial"))
        right.addWidget(how)
        import_soc=QPushButton('导入 .sil 设计')
        import_soc.clicked.connect(win.import_soc);right.addWidget(import_soc)
        hero.addLayout(right, 0)
        lay.addLayout(hero)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{T.BORDER};")
        lay.addWidget(div)

        sect = QHBoxLayout()
        h = QLabel("选择一个项目")
        h.setStyleSheet(f"color:{T.TEXT}; font-size:17px; font-weight:700;")
        sect.addWidget(h)
        sect.addStretch(1)
        hint = QLabel("产品项目与12项委托 · 自由沙盒有独立入口")
        hint.setStyleSheet(f"color:{T.DIM}; font-size:11px;")
        sect.addWidget(hint)
        lay.addLayout(sect)

        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        lay.addLayout(self.grid)
        lay.addStretch(1)

        foot = QHBoxLayout()
        f1 = QLabel("教学模拟 · 性能为模型分 · 公开资料与未核验条目在图鉴中分别标注")
        f1.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        foot.addWidget(f1)
        foot.addStretch(1)
        done = len(self.win.progress.get("tutorials", {}))
        f2 = QLabel(f"教学 {done}/{len(TUTORIALS)} · 数据模型 {len(SEGMENT_LIST)} 个关卡")
        f2.setStyleSheet(f"color:{T.DIM}; font-size:10px; font-family:{T.FONT_MONO};")
        self.learning_count=f2
        foot.addWidget(f2)
        lay.addLayout(foot)


    def _fill_grid(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        for i, seg in enumerate(s for s in SEGMENT_LIST if s['id']!='sandbox'):
            card = ScenarioCard(seg, self.win.progress.get(seg["id"]))
            card.clicked.connect(self.win.start_scenario)
            self.grid.addWidget(card, i // 3, i % 3)

    def refresh(self):
        if self.win.design and self.win.result:
            self.preview.setPixmap(QPixmap.fromImage(render_silicon(
                QSize(330, 240), self.win.result["plan"], seed=self.win.design.seed,
                legend=False, labels=False)))
        else:
            self.preview.setPixmap(logo_pixmap(190))
        from ...data.lab_courses import COURSES
        self.learning_count.setText(f'14 节设计课 · {len(COURSES)} 节实验课 · powered by isqi')
        self._fill_grid()
        if not self._entered:
            self._entered = True
            anim.fade_in(self._hero_title)
        self.cont.setEnabled(self.win.design is not None)
        self.cont.setText("继续上次设计  →" if self.win.design is not None else "尚无设计 · 先选一个项目")
