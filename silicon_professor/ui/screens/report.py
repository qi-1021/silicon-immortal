"""发布结果页。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from ... import export
from .. import theme as T
from ..widgets import BarRow, Card, Stat


class ReportScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        self.lay = QVBoxLayout(page)
        self.lay.setContentsMargins(32, 22, 32, 22)
        self.lay.setSpacing(14)
        scroll.setWidget(page)
        outer.addWidget(scroll)

        hero = QFrame()
        hero.setObjectName("Hero")
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(22, 18, 22, 18)
        hl.setSpacing(20)
        self.grade = QLabel("A")
        self.grade.setFixedSize(104, 104)
        self.grade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade.setStyleSheet(
            f"background:{T.rgba(T.CYAN, 0.07)}; border:2px solid {T.CYAN}; border-radius:52px;"
            f"color:{T.CYAN}; font-size:46px; font-weight:800;")
        hl.addWidget(self.grade)
        info = QVBoxLayout()
        info.setSpacing(3)
        self.title = QLabel("流片成功")
        self.title.setStyleSheet(f"color:{T.TEXT}; font-size:28px; font-weight:800;")
        info.addWidget(self.title)
        self.sub = QLabel("—")
        self.sub.setStyleSheet(f"color:{T.AMBER}; font-size:13px;")
        info.addWidget(self.sub)
        self.verdict = QLabel("—")
        self.verdict.setWordWrap(True)
        self.verdict.setStyleSheet(f"color:{T.TEXT2}; font-size:12px;")
        info.addWidget(self.verdict)
        hl.addLayout(info, 1)
        scorebox = QVBoxLayout()
        scorebox.setSpacing(2)
        self.review = QLabel("—")
        self.review.setStyleSheet(f"color:{T.CYAN}; font-size:34px; font-weight:800; font-family:{T.FONT_MONO};")
        scorebox.addWidget(self.review)
        rlab = QLabel("媒体综合评分")
        rlab.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        scorebox.addWidget(rlab)
        hl.addLayout(scorebox)
        self.lay.addWidget(hero)

        grid = QGridLayout()
        grid.setSpacing(8)
        self.stats = {}
        specs = [("profit", "净利润"), ("revenue", "营收"), ("units", "销量"),
                 ("unit", "单颗成本"), ("margin", "毛利率"), ("grade_met", "目标达成")]
        for i, (k, title) in enumerate(specs):
            s = Stat(title)
            self.stats[k] = s
            grid.addWidget(s, i // 3, i % 3)
        self.lay.addLayout(grid)

        mid = QHBoxLayout()
        mid.setSpacing(14)
        bc = Card("跑分 vs 真实体验", "官方数字与媒体实测的差距")
        self.bars = {}
        for k, title, color in [("off_st", "官方 ST", T.CYAN), ("real_st", "实测 ST", T.BLUE),
                                ("off_mt", "官方 MT", T.CYAN), ("real_mt", "实测 MT", T.BLUE)]:
            b = BarRow(title, 0, 0, 1, color=color)
            self.bars[k] = b
            bc.add(b)
        self.tuning = QLabel("—")
        self.tuning.setWordWrap(True)
        self.tuning.setStyleSheet(f"color:{T.AMBER}; font-size:10px;")
        bc.add(self.tuning)
        mid.addWidget(bc, 1)

        qc = Card("质量分解", "按关卡权重归一，1.0 = 达标")
        self.qbars = {}
        for k, title, color in [("q_st", "单核", T.CYAN), ("q_mt", "多核", T.BLUE),
                                ("q_gpu", "GPU", T.PINK), ("q_eff", "能效", T.GREEN),
                                ("q_ai", "AI", T.PURPLE)]:
            b = BarRow(title, 0, 1, 1, color=color, fmt="{:.2f}")
            self.qbars[k] = b
            qc.add(b)
        mid.addWidget(qc, 1)
        self.lay.addLayout(mid)

        low = QHBoxLayout()
        low.setSpacing(14)
        cc = Card("成本结构")
        self.cost = QLabel("—")
        self.cost.setWordWrap(True)
        self.cost.setStyleSheet(f"color:{T.TEXT}; font-size:11px; line-height:1.75; font-family:{T.FONT_MONO};")
        cc.add(self.cost)
        low.addWidget(cc, 1)
        mc = Card("市场")
        self.market = QLabel("—")
        self.market.setWordWrap(True)
        self.market.setStyleSheet(f"color:{T.TEXT}; font-size:12px; line-height:1.8;")
        mc.add(self.market)
        low.addWidget(mc, 1)
        self.lay.addLayout(low)

        btns = QHBoxLayout()
        exp = QPushButton("导出设计文件  ⇩")
        exp.clicked.connect(self._export)
        btns.addWidget(exp)
        again = QPushButton("回到架构继续优化")
        again.clicked.connect(lambda: win.go("architecture"))
        btns.addWidget(again)
        btns.addStretch(1)
        nxt = QPushButton("下一位客户  →")
        nxt.setObjectName("Primary")
        nxt.setFixedHeight(40)
        nxt.clicked.connect(win.next_scenario)
        btns.addWidget(nxt)
        self.lay.addLayout(btns)
        self.lay.addStretch(1)

    def _export(self):
        if not self.win.result or not self.win.design:
            return
        name = self.win.design.name or "chip"
        safe = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "chip"
        default = f"exports/{safe}.sil"
        path, _ = QFileDialog.getSaveFileName(self, "导出设计文件", default,
                                              "Silicon SoC (*.sil)")
        if not path:
            return
        try:
            p = export.export_to(path, self.win.design, self.win.result)
            QMessageBox.information(self, "已导出", f"设计已写入：\n{p}")
        except Exception as ex:
            QMessageBox.warning(self, "导出失败", str(ex))

    def refresh(self):
        r = self.win.result
        if not r:
            return
        m = r["market"]
        p = r["perf"]
        grade = m["grade"]
        col = {"S": T.CYAN, "A": T.GREEN, "B": T.AMBER, "C": T.RED}.get(grade, T.TEXT)
        self.grade.setText(grade)
        self.grade.setStyleSheet(
            f"background:{col}12; border:2px solid {col}; border-radius:52px;"
            f"color:{col}; font-size:46px; font-weight:800;")
        self.title.setText(('自由方案估算 · ' if self.win.design.scenario_id=='sandbox' else "发布结果 · " if self.win.is_released else "发布预估 · ") + self.win.scenario["name"])
        self.sub.setText(f"{m['targets_met']}/{m['targets_total']} 项指标达成 · "
                         f"市场评分 {m['review']:.0f}")
        self.verdict.setText(f"预计净利润 ${m['profit']:.0f} M。持续性能系数 {p['sustain_ratio']:.0%}，目标达成 {m['targets_met']}/{m['targets_total']}。")
        self.review.setText(f"{m['review']:.0f}")

        self.stats["profit"].set(f"${m['profit']:.0f}M", accent=T.GREEN if m["profit"] > 0 else T.RED)
        self.stats["revenue"].set(f"${m['revenue']:.0f}M")
        self.stats["units"].set(f"{m['units']:.1f}M")
        self.stats["unit"].set(f"${r['cost']['total']:.1f}")
        self.stats["margin"].set(f"{m['margin']*100:.0f}%")
        self.stats["grade_met"].set(f"{m['targets_met']}/{m['targets_total']}")

        maxv = max(p["official_st"], p["real_st"], p["official_mt"], p["real_mt"], 1) * 1.15
        self.bars["off_st"].set_values(p["official_st"], 0, maxv)
        self.bars["real_st"].set_values(p["real_st"], 0, maxv)
        self.bars["off_mt"].set_values(p["official_mt"], 0, maxv)
        self.bars["real_mt"].set_values(p["real_mt"], 0, maxv)
        mt_gap = p.get("real_mt", 0) < p.get("official_mt", 0) * 0.85
        if m["caught"]:
            self.tuning.setText("⚠ 跑分优化被媒体识破：评分扣分，官方数字不再被信任。")
            self.tuning.setStyleSheet(f"color:{T.RED}; font-size:10px;")
        elif mt_gap:
            self.tuning.setText("持续性能明显低于峰值：散热/功耗压住了多核，游戏看的是持续不是峰值。")
            self.tuning.setStyleSheet(f"color:{T.AMBER}; font-size:10px;")
        elif self.win.design.bench_isa > 0.25:
            self.tuning.setText("跑分 ISA 扩展偏多：官方分虚高，真实应用没有对应收益。")
            self.tuning.setStyleSheet(f"color:{T.AMBER}; font-size:10px;")
        elif self.win.design.bench_tuning > 0.3:
            self.tuning.setText("调度/提频优化偏激进：官方数字高于真实体验，长期口碑会受损。")
            self.tuning.setStyleSheet(f"color:{T.AMBER}; font-size:10px;")
        else:
            self.tuning.setText("调优在合理范围内：官方数字与实测接近。")
            self.tuning.setStyleSheet(f"color:{T.GREEN}; font-size:10px;")

        for k, b in self.qbars.items():
            b.set_values(min(1.35, m[k]), 1.0, 1.35)

        self.cost.setText(
            f"裸 die          ${r['cost']['die']:>7.1f}\n"
            f"封装            ${r['cost']['package']:>7.1f}\n"
            f"外挂器件        ${r['cost'].get('external_bom', 0):>7.1f}\n"
            f"测试/组装       ${r['cost']['test'] + r['cost']['assembly']:>7.1f}\n"
            + (f"chiplet 组装    ${r['cost'].get('chiplet_assembly', 0):>7.1f}\n" if r['cost'].get('chiplet_assembly') else "")
            + f"单颗成本        ${r['cost']['total']:>7.1f}\n"
            + f"整机配套成本    ${r['cost']['platform_total']:>7.1f}\n"
            f"NRE             ${r['nre']['total']:>7.0f}M\n"
            f"售价            ${self.win.design.price:>7.0f}")
        fail = []
        if m.get("crashed"):
            fail.append("游戏中发生首发缺陷事件，评分下降。")
        elif m.get("p_crash", 0) > 0.25:
            fail.append(f"首发稳定性风险 {m['p_crash']*100:.0f}%：新节点 + 激进频率是功能异常的经典配方。")
        if m.get("stagnant"):
            prev = m.get("prev") or {}
            fail.append(f"相对{prev.get('name','上代')}提升不足 8%：媒体评价“代际提升有限”。")
        if m.get("aging_risk"):
            fail.append(f"教学应力情景下性能系数 {m['aged_ratio']:.0%}，不代表实际寿命预测。")
        if fail:
            self.verdict.setText(f"预计净利润 ${m['profit']:.0f} M。" + " / ".join(fail))
        comp = self.win.scenario["competitor"]
        win_all = p["real_st"] > comp["st"] and p["real_mt"] > comp["mt"]
        self.market.setText(
            f"对手 {comp['name']}：ST {comp['st']} / MT {comp['mt']} / ${comp['price']}\n"
            f"你的实测：ST {p['real_st']:.0f} / MT {p['real_mt']:.0f} / ${self.win.design.price:.0f}\n"
            f"品牌口碑：{self.win.design.reputation*100:.0f}/100 · 需求系数 {m.get('brand',1):.2f}\n"
            f"教学应力情景 MT：{m.get('aged_mt', 0):.0f}（当前持续 {p.get('mt_sustain', 0):.0f}）\n"
            f"零售机复测：ST {m.get('retail_st', 0):.0f} / MT {m.get('retail_mt', 0):.0f}（工程机×{m.get('retail_factor', 1):.0%}）\n"
            + ("✓ 关键指标全部超过对手。" if win_all
               else "⚠ 至少有一项被对手压住——价格或定位需要补。"))
        self.market.setStyleSheet(
            f"color:{T.TEXT if win_all else T.AMBER}; font-size:12px; line-height:1.8;")
