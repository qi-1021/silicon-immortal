"""流片展示：芯片的“定妆照”。低频高光时刻，进场有编排的淡入 + 数字滚动。"""
from __future__ import annotations

import json

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QMessageBox, QPushButton, QScrollArea, QVBoxLayout,
                               QWidget)

from ... import export
from .. import anim, theme as T
from ..die_render import render_die
from ..silicon_render import render_silicon
from ..wafer_render import render_wafer
from ..image_view import ImageView
from ..widgets import Card, ElidedLabel, Pill, Segmented


class ShowcaseScreen(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self._last_key = None
        self.mode = "silicon"
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._render_hero)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 18, 24, 16)
        outer.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(12)
        self.grade = QLabel("A")
        self.grade.setFixedSize(60, 60)
        self.grade.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade.setStyleSheet(
            f"background:{T.CYAN}12; border:2px solid {T.CYAN}; border-radius:38px;"
            f"color:{T.CYAN}; font-size:34px; font-weight:800;")
        head.addWidget(self.grade)
        titlebox = QVBoxLayout()
        titlebox.setSpacing(2)
        self.title = ElidedLabel("—")
        self.title.setStyleSheet(f"color:{T.TEXT}; font-size:30px; font-weight:800; letter-spacing:1px;")
        titlebox.addWidget(self.title)
        self.pills = QHBoxLayout()
        self.pills.setSpacing(6)
        titlebox.addLayout(self.pills)
        head.addLayout(titlebox, 1)
        scorebox = QVBoxLayout()
        scorebox.setSpacing(0)
        self.review = QLabel("—")
        self.review.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.review.setStyleSheet(f"color:{T.CYAN}; font-size:30px; font-weight:800; font-family:{T.FONT_MONO};")
        scorebox.addWidget(self.review)
        self.review_cap = QLabel("媒体评分 / 100")
        self.review_cap.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.review_cap.setStyleSheet(f"color:{T.DIM}; font-size:10px;")
        scorebox.addWidget(self.review_cap)
        head.addLayout(scorebox)
        outer.addLayout(head)
        toolbar = QHBoxLayout()
        self.views = Segmented([("silicon", "硅片"), ("wafer", "晶圆"), ("layout", "功能布局")], "silicon")
        self.views.changed.connect(self._mode)
        toolbar.addWidget(self.views)
        toolbar.addStretch(1)
        self.status = QLabel("设计预览")
        self.status.setObjectName("Muted")
        toolbar.addWidget(self.status)
        outer.addLayout(toolbar)

        body = QHBoxLayout()
        body.setSpacing(14)

        # 左：大图
        self.hero = QFrame()
        self.hero.setObjectName("Panel")
        hl = QVBoxLayout(self.hero)
        hl.setContentsMargins(12, 12, 12, 12)
        self.die = ImageView()
        self.die.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(self.die, 1)
        self.caption = QLabel()
        self.caption.setWordWrap(True)
        self.caption.setObjectName("Muted")
        from PySide6.QtWidgets import QSizePolicy
        self.caption.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        hl.addWidget(self.caption)
        body.addWidget(self.hero, 3)

        # 右：数据（滚动区，防小屏裁剪）
        side_wrap = QScrollArea()
        side_wrap.setWidgetResizable(True)
        side_wrap.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_wrap.setFixedWidth(310)
        side_page = QWidget()
        side = QVBoxLayout(side_page)
        side.setContentsMargins(0, 0, 6, 0)
        side.setSpacing(10)
        side_wrap.setWidget(side_page)
        sc = Card("关键指标")
        grid = QGridLayout()
        grid.setSpacing(7)
        self.stats: dict[str, object] = {}
        self.stat_targets: dict[str, tuple[float, str]] = {}
        for i, (k, title, fmt) in enumerate([
            ("st", "单核 ST", "{:.0f}"), ("mt", "多核 MT", "{:.0f}"),
            ("gpu", "GPU", "{:.0f}"), ("cost", "单颗 $", "{:.0f}"),
            ("power", "峰值 W", "{:.1f}"), ("yield", "良率", "{:.0%}"),
        ]):
            from ..widgets import Stat
            s = Stat(title)
            self.stats[k] = s
            self.stat_targets[k] = (0.0, fmt)
            grid.addWidget(s, i // 2, i % 2)
        sc.add_layout(grid)
        side.addWidget(sc)

        spec = Card("配置单")
        self.spec = QLabel("—")
        self.spec.setWordWrap(True)
        self.spec.setStyleSheet(f"color:{T.TEXT}; font-size:12px; line-height:1.8; font-family:{T.FONT_MONO};")
        spec.add(self.spec)
        side.addWidget(spec)

        vc = Card("媒体评价")
        self.verdict = QLabel("—")
        self.verdict.setWordWrap(True)
        self.verdict.setStyleSheet(f"color:{T.TEXT}; font-size:12px; line-height:1.7;")
        vc.add(self.verdict)
        side.addWidget(vc)
        side.addStretch(1)

        btns = QGridLayout()
        btns.setSpacing(8)
        self.b_report = QPushButton("查看完整报告  →")
        self.b_report.setObjectName("Primary")
        self.b_report.clicked.connect(lambda: win.go("report"))
        btns.addWidget(self.b_report, 0, 0, 1, 2)
        self.b_png = QPushButton("导出当前视图")
        self.b_png.clicked.connect(self._export_png)
        btns.addWidget(self.b_png, 1, 0)
        self.b_json = QPushButton("导出设计文件")
        self.b_json.clicked.connect(self._export_json)
        btns.addWidget(self.b_json, 1, 1)
        self.b_next = QPushButton("下一颗芯片  →")
        self.b_next.setObjectName("Ghost")
        self.b_next.clicked.connect(win.next_scenario)
        btns.addWidget(self.b_next, 2, 0, 1, 2)
        btns.setColumnStretch(0, 1)
        btns.setColumnStretch(1, 1)
        side.addLayout(btns)
        body.addWidget(side_wrap, 0)
        outer.addLayout(body, 1)

        self._enter_widgets: list = []

    # ---------- export ----------
    def _mode(self, key):
        self.mode = key
        self.die.reset_view()
        self._render_hero()

    def _export_png(self):
        if not self.win.result or not self.win.design:
            return
        name = self.win.design.name or "chip"
        safe = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "chip"
        default = f"exports/{safe}.dieshot.png"
        path, _ = QFileDialog.getSaveFileName(self, "导出 Die Shot", default,
                                              "PNG Image (*.png)")
        if not path:
            return
        try:
            p = export.export_dieshot_png(path, self.win.design, self.win.result, mode=self.mode)
            QMessageBox.information(self, "已导出", f"Die Shot 已写入：\n{p}")
        except Exception as ex:
            QMessageBox.warning(self, "导出失败", str(ex))

    def _export_json(self):
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

    # ---------- refresh ----------
    def _render_hero(self):
        if not self.win.result or not self.win.design:
            return
        w, h = max(640, self.die.width()), max(440, self.die.height())
        self.die.setPixmap(self._die_pixmap(w, h))
        if self.win.design.chiplet and self.mode == "wafer":
            self.caption.setText("模拟生成 · Chiplet 的逻辑总图晶圆示意，不能代表两颗 die 的实际生产排版；成本按两颗 die 分别计算。")
        else:
            self.caption.setText("模拟生成 · 模块位置和面积来自当前设计；金属层与单元纹理为示意。滚轮缩放，拖动平移，双击复位。")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(100)

    def _die_pixmap(self, w: int, h: int) -> QPixmap:
        r = self.win.result
        img = QImage(w, h, QImage.Format_ARGB32)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        d = self.win.design
        node = r.get("node", {})
        plan = r.get("plan")
        title = d.name or "未命名芯片"
        subtitle = (f"{node.get('name', '')} · {plan.die_w:.1f}×{plan.die_h:.1f}mm · "
                    f"{plan.die_area:.1f}mm²" if plan is not None else "")
        if self.mode == "layout":
            render_die(p, QSize(w, h), plan, title=title, subtitle=subtitle, legend=True)
        p.end()
        if self.mode == "silicon":
            img = render_silicon(QSize(w, h), plan, seed=d.seed, title=title, subtitle=subtitle, legend=True)
        elif self.mode == "wafer":
            img = render_wafer(QSize(w, h), plan, seed=d.seed, title=title + " / 300 mm")
        return QPixmap.fromImage(img)

    def refresh(self):
        r = self.win.result
        if not r or not self.win.design:
            return
        d = self.win.design
        m = r["market"]
        p = r["perf"]

        grade = m["grade"]
        col = {"S": T.CYAN, "A": T.GREEN, "B": T.AMBER, "C": T.RED}.get(grade, T.TEXT)
        self.grade.setText(grade)
        self.grade.setStyleSheet(
            f"background:{T.rgba(col, 0.08)}; border:1px solid {T.rgba(col, 0.3)}; border-radius:10px;"
            f"color:{col}; font-size:28px; font-weight:600;")
        self.title.setText(d.name or "未命名芯片")
        while self.pills.count():
            it = self.pills.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for txt, color in [
            (r["node"]["name"], T.BLUE), (self.win.scenario["name"], T.PURPLE),
            (f"{r['die_area']:.1f} mm²", T.AMBER),
        ]:
            self.pills.addWidget(Pill(txt, color))
        self.pills.addStretch(1)
        self.review.setText(f"{m['review']:.0f}")
        self.status.setText('自由方案预览 · 诊断不阻塞，未完成物理签核' if self.win.design.scenario_id=='sandbox' else "已流片 · 游戏发布结果" if self.win.is_released else "设计预览 · 尚未发布此版本")

        vals = {
            "st": (p["st_burst"], "{:.0f}"), "mt": (p["mt_burst"], "{:.0f}"),
            "gpu": (p["gpu"], "{:.0f}"), "cost": (r["cost"]["total"], "{:.0f}"),
            "power": (r["power"]["peak"], "{:.1f}"),
            "yield": (r["yield_"]["yield_pct"], "{:.0%}"),
        }
        for k, s in self.stats.items():
            v, fmt = vals[k]
            s.set(fmt.format(v))
        key = json.dumps(d.to_dict(), sort_keys=True)
        self._render_hero()
        if key != self._last_key:
            self._last_key = key
            if self.win.is_released:
                anim.fade_in(self.hero)

        lines = []
        for g in r["groups"]:
            lines.append(f"{g['ip']['name']} ×{g['count']} @ {g['clock']:.2f}GHz")
        lines.append(f"L3 {d.l3_mb:g}MB{' + SLC ' + str(d.slc_mb) + 'MB' if d.slc_mb else ''} · {d.noc} · {d.dram.upper()}")
        lines.append(f"{r['node']['name']} · {d.package_id.upper()} · {d.cooling_id}")
        self.spec.setText("\n".join(lines))
        self.verdict.setText(f"预计净利润 ${m['profit']:.0f} M，毛利率 {m['margin']:.0%}。\n持续多核性能为峰值的 {p['sustain_ratio']:.0%}，达成 {m['targets_met']}/{m['targets_total']} 项产品目标。")

    def on_result(self):
        self.refresh()
