"""项目简报页。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget,QScrollArea)

from .. import theme as T
from ..widgets import Card, Pill, Stat


class BriefScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0)
        scroll=QScrollArea();scroll.setWidgetResizable(True);page=QWidget();scroll.setWidget(page);root.addWidget(scroll)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(40, 26, 40, 24)
        outer.setSpacing(16)

        top = QHBoxLayout()
        self.kicker = QLabel("PROJECT BRIEF")
        self.kicker.setStyleSheet(f"color:{T.CYAN}; font-size:10px; letter-spacing:2px; font-family:{T.FONT_MONO};")
        top.addWidget(self.kicker)
        top.addStretch(1)
        self.budget = Pill("预算 —")
        top.addWidget(self.budget)
        outer.addLayout(top)

        self.title = QLabel("—")
        self.title.setStyleSheet(f"color:{T.TEXT}; font-size:34px; font-weight:800;")
        outer.addWidget(self.title)
        self.tag = QLabel("—")
        self.tag.setStyleSheet(f"color:{T.AMBER}; font-size:15px;")
        outer.addWidget(self.tag)

        body = QHBoxLayout()
        body.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(14)
        c1 = Card("项目背景")
        self.brief = QLabel("—")
        self.brief.setWordWrap(True)
        self.brief.setStyleSheet(f"color:{T.TEXT2}; font-size:13px; line-height:1.7;")
        c1.add(self.brief)
        left.addWidget(c1)

        c2 = Card("设计提示")
        self.tutorial = QLabel("—")
        self.tutorial.setWordWrap(True)
        self.tutorial.setStyleSheet(f"color:{T.CYAN}; font-size:12px;")
        c2.add(self.tutorial)
        left.addWidget(c2)
        self.challenge_card=Card('项目委托验收','全部满足后才能完成本关')
        self.challenge_checks=QLabel();self.challenge_checks.setWordWrap(True);self.challenge_card.add(self.challenge_checks)
        self.source_note=QLabel();self.source_note.setWordWrap(True);self.source_note.setObjectName('Muted');self.challenge_card.add(self.source_note)
        self.solution_button=QPushButton('载入参考方案 · 替换当前设计')
        self.solution_button.clicked.connect(self._load_solution);self.challenge_card.add(self.solution_button);left.addWidget(self.challenge_card)
        body.addLayout(left, 3)

        right = QVBoxLayout()
        right.setSpacing(10)
        tc = Card("目标")
        grid = QGridLayout()
        grid.setSpacing(8)
        self.targets = {}
        for i, (k, title, unit) in enumerate([
            ("st", "单核 ST", ""), ("mt", "多核 MT", ""), ("gpu", "GPU", ""),
            ("ai", "AI 综合分", ""), ("battery_h", "续航", "h"), ("price", "建议价", "$"),
        ]):
            s = Stat(title, "—", unit)
            self.targets[k] = s
            grid.addWidget(s, i // 2, i % 2)
        tc.add_layout(grid)
        right.addWidget(tc)

        cc = Card("对手")
        self.comp = QLabel("—")
        self.comp.setWordWrap(True)
        self.comp.setStyleSheet(f"color:{T.TEXT2}; font-size:12px;")
        cc.add(self.comp)
        right.addWidget(cc)
        right.addStretch(1)

        go = QPushButton("进入设计工作台  →")
        go.setObjectName("Primary")
        go.setFixedHeight(42)
        go.clicked.connect(lambda: self.win.go("architecture"))
        right.addWidget(go)
        body.addLayout(right, 2)

        outer.addLayout(body, 1)
        outer.addStretch(1)

    def refresh(self):
        seg = self.win.scenario
        if not seg:
            return
        self.title.setText(seg["name"])
        self.tag.setText(seg["tagline"])
        self.budget.setText(f"预算 ${seg['budget_m']}M")
        self.brief.setText(seg["brief"])
        self.tutorial.setText("总师笔记 · " + seg["tutorial"])
        t = seg["targets"]
        for k, s in self.targets.items():
            if k == "price":
                s.set(f"${seg['ref_price']}")
            else:
                s.set(f"{t[k]:g}")
        c = seg["competitor"]
        self.comp.setText(
            f"{c['name']}：ST {c['st']} / MT {c['mt']} / GPU {c['gpu']}，定价 ${c['price']}。\n"
            f"你的芯片必须在这几项上给出取舍，而不是全部赢。")
        self.kicker.setText(f"PROJECT BRIEF · {seg['year']}")
        challenge=(self.win.result or {}).get('challenge')
        self.challenge_card.setVisible(bool(challenge))
        if challenge:
            from ...data.challenges import CHALLENGES
            from ...data.sources import SOURCES
            self.challenge_checks.setText('\n'.join(('✓ ' if r['ok'] else '○ ')+r['title']+' · 当前 '+(f"{r['value']:.3f}" if type(r['value']) in (float,int) else str(r['value'])) for r in challenge['checks']))
            self.source_note.setText('虚构设计委托；预算、门槛和PPA为游戏假设。来源支持相关概念，不证明本关参数：\n'+'\n'.join(SOURCES[s]['title'] for s in CHALLENGES[seg['id']]['sources']))

    def _load_solution(self):
        from ...engine.challenges import challenge_design
        self.win.design=challenge_design(self.win.design.scenario_id,solution=True)
        self.win.published_design=None;self.win.recompute_now(force_layout=True);self.win.persist();self.refresh()
