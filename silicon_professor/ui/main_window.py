"""主窗口：顶部 HUD、步骤导航、页面栈、状态与存档。"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QDialog, QFrame, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QStackedWidget, QVBoxLayout,
                               QWidget,QScrollArea,QLayout)

from ..data.segments import SEGMENTS, SEGMENT_LIST
from ..data.tutorials import TUTORIAL_BY_ID
from ..data.cores import CORES
from ..data.blocks import GPUS
from ..data.nodes import NODES
from ..data.sources import SOURCES, TIER_LABELS, source_text
from ..engine.simulate import simulate
from ..engine.types import CoreGroup, Design, empty_design
from .. import save as savemod
from . import anim, theme as T
from .screens.architecture import ArchitectureScreen
from .screens.brief import BriefScreen
from .screens.codex import CodexScreen, SourcesScreen
from .screens.floorplan import FloorplanScreen
from .screens.package import PackageScreen
from .screens.physical import PhysicalScreen
from .screens.report import ReportScreen
from .screens.showcase import ShowcaseScreen
from .screens.signoff import SignoffScreen
from .screens.tutorial import TutorialScreen
from .screens.start import StartScreen
from .screens.sandbox import SandboxScreen
from .screens.engineering import EngineeringScreen
from .screens.labs import LabsScreen
from .screens.studio import StudioScreen
from .screens.rescue import RescueScreen
from .updates import UpdatesScreen
from .search import InfoDialog, SearchDialog
from .widgets import ElidedLabel
from ..data.architectures import MODES

STEPS = [
    ("brief", "01 立项"),
    ("architecture", "02 架构"),
    ("physical", "03 物理实现"),
    ("floorplan", "04 布局"),
    ("package", "05 封装散热"),
    ("engineering", "06 工程验证"),
    ("signoff", "07 签核"),
    ("report", "08 发布报告"),
    ("showcase", "09 样片展示"),
]


class Header(QFrame):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.setFixedHeight(72)
        self.setObjectName("Header")
        self.setStyleSheet(f"QFrame#Header {{ background:{T.BG2}; border-bottom:1px solid {T.BORDER}; }}")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 8, 18, 8)
        lay.setSpacing(18)

        brand = QVBoxLayout()
        brand.setSpacing(0)
        t1 = QLabel("硅仙人")
        t1.setStyleSheet(f"color:{T.TEXT}; font-size:19px; font-weight:800; letter-spacing:1px;")
        t2 = QLabel("SILICON / DESIGN STUDIO")
        t2.setStyleSheet(f"color:{T.DIM}; font-size:9px; letter-spacing:1.1px; font-family:{T.FONT_MONO};")
        brand.addWidget(t1)
        brand.addWidget(t2)
        brand_wrap = QWidget()
        brand_wrap.setLayout(brand)
        brand.setContentsMargins(0, 0, 0, 0)
        brand_wrap.setMinimumWidth(155)
        lay.addWidget(brand_wrap)
        lay.addSpacing(8)

        self.scenario = ElidedLabel("未立项")
        self.scenario.setMinimumWidth(120)
        self.scenario.setMaximumWidth(250)
        self.scenario.setStyleSheet(
            f"color:{T.CYAN}; background:{T.rgba(T.CYAN, 0.07)}; border:1px solid {T.rgba(T.CYAN, 0.27)};"
            f"border-radius:9px; padding:3px 10px; font-size:11px;")
        lay.addWidget(self.scenario, 1)
        lay.addStretch(1)

        self.stats = {}
        for key, title, unit in [
            ("area", "DIE", "mm²"), ("power", "PEAK", "W"),
            ("st", "ST", ""), ("mt", "MT", ""), ("cost", "BOM", "$"),
        ]:
            box = QVBoxLayout()
            box.setSpacing(0)
            l1 = QLabel(title)
            l1.setStyleSheet(f"color:{T.DIM}; font-size:9px; letter-spacing:0.8px;")
            l2 = QLabel("—")
            l2.setMinimumWidth(70 if key == "area" else 54)
            l2.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:600; font-family:{T.FONT_MONO};")
            box.addWidget(l1)
            box.addWidget(l2)
            w = QWidget()
            w.setLayout(box)
            lay.addWidget(w)
            self.stats[key] = (l2, unit)

        self.valid = QLabel("● 设计就绪")
        self.valid.setStyleSheet(f"color:{T.GREEN}; font-size:11px;")
        lay.addWidget(self.valid)

        self.search_btn = QPushButton("查找  ⌘ K")
        self.search_btn.setObjectName("Ghost")
        self.search_btn.clicked.connect(win.open_search)
        lay.addWidget(self.search_btn)
        self.tutorial = QPushButton("教学")
        self.tutorial.setObjectName("Ghost")
        self.tutorial.clicked.connect(lambda: win.go("tutorial"))
        self.codex = QPushButton("图鉴")
        self.codex.setObjectName("Ghost")
        self.codex.clicked.connect(lambda: win.go("codex"))
        self.sources = QPushButton("文献")
        self.sources.setObjectName("Ghost")
        self.sources.clicked.connect(lambda: win.go("sources"))

    def update_state(self, result, scenario):
        if scenario:
            name = self.win.design.name if self.win.design else ""
            self.scenario.setText(name or scenario['name'])
            self.scenario.setToolTip(scenario['name'])
        if not result:
            for l2, _ in self.stats.values():
                l2.setText("—")
            return
        p = result["perf"]
        vals = {
            "area": f"{result['die_area']:.1f}mm²",
            "power": f"{result['power']['peak']:.1f}W",
            "st": f"{p['st_burst']:.0f}",
            "mt": f"{p['mt_burst']:.0f}",
            "cost": f"${result['cost']['total']:.0f}",
        }
        for k, (l2, unit) in self.stats.items():
            l2.setText(vals.get(k, "—"))
        if result['signoff'].get('mode')=='advisory':
            self.valid.setText(f"● 自由设计 · {len(result['signoff']['diagnostics'])}项建议")
            self.valid.setStyleSheet(f"color:{T.AMBER}; font-size:11px;")
        elif result["signoff"]["ready"]:
            self.valid.setText("● 可签核")
            self.valid.setStyleSheet(f"color:{T.GREEN}; font-size:11px;")
        else:
            self.valid.setText(f"● {len(result['signoff']['blockers'])} 项待修复")
            self.valid.setStyleSheet(f"color:{T.RED}; font-size:11px;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        from ..version import GAME_VERSION
        self.setWindowTitle("硅仙人 Silicon Immortal · "+GAME_VERSION)
        from .brand import app_icon
        self.setWindowIcon(app_icon())
        self.resize(1500, 940)
        self.setMinimumSize(1180, 760)

        self.design: Design | None = None
        self.result = None
        self.scenario = None
        self.tutorial_id: str | None = None
        self.progress: dict = {}
        self.lab_workspace: dict = {}
        self.core_workspace: dict = {}
        self.rescue_workspace: dict = {}
        self.update_settings: dict = {}
        self.sandbox_workspace: dict = {};self.project_workspace: dict = {}
        self.published_design = None
        self._save = savemod.load()
        self.ip_library={}
        self.learning_mode=(self._save or {}).get('learning_mode','beginner')
        if self.learning_mode not in MODES:self.learning_mode='beginner'
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._do_recompute)
        self._force_layout = False

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.header = Header(self)
        outer.addWidget(self.header)
        self.mode_picker=QComboBox()
        for key,mode in MODES.items():self.mode_picker.addItem(mode['name'],key)
        self.mode_picker.setCurrentIndex(self.mode_picker.findData(self.learning_mode))
        self.mode_picker.setToolTip('模式控制引导与参数展开程度；不改变仿真规则和设计。')
        self.header.layout().addWidget(self.mode_picker)
        self.mode_picker.currentIndexChanged.connect(self._set_mode)

        workbench = QHBoxLayout()
        workbench.setContentsMargins(0, 0, 0, 0)
        workbench.setSpacing(0)
        outer.addLayout(workbench, 1)
        nav = QFrame()
        nav.setObjectName("Sidebar")
        nav.setMinimumWidth(150)
        navl = QVBoxLayout(nav)
        navl.setContentsMargins(12, 20, 12, 14)
        navl.setSpacing(4)
        home = QPushButton("项目首页")
        home.setObjectName("Nav")
        home.clicked.connect(lambda: self.go("start"))
        navl.addWidget(home)
        cap = QLabel("设计流程")
        cap.setObjectName("Muted")
        cap.setContentsMargins(12, 16, 0, 8)
        navl.addWidget(cap)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = {}
        for key, text in STEPS:
            b = QPushButton(text)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setObjectName("Nav")
            b.clicked.connect(lambda _, k=key: self.go(k))
            navl.addWidget(b)
            self.nav_group.addButton(b)
            self.nav_buttons[key] = b
        navl.addStretch(1)
        for button in (self.header.tutorial, self.header.codex, self.header.sources):
            button.setParent(nav)
            button.setObjectName("Nav")
            navl.addWidget(button)
        self.studio_button = QPushButton("LAB 核心设计")
        self.studio_button.setObjectName("Nav")
        self.studio_button.clicked.connect(lambda: self.go("studio"))
        navl.addWidget(self.studio_button)
        self.rescue_button=QPushButton('拯救芯片');self.rescue_button.setObjectName('Nav')
        self.rescue_button.clicked.connect(lambda:self.go('rescue'));navl.addWidget(self.rescue_button)
        free=QPushButton('自由沙盒');free.setObjectName('Nav');free.clicked.connect(self.start_sandbox);navl.addWidget(free)
        manual=QPushButton('玩家手册 ↗');manual.setObjectName('Nav')
        manual.clicked.connect(self.open_manual);navl.addWidget(manual)
        self.hint = QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setObjectName("Muted")
        navl.addWidget(self.hint)
        motion = QPushButton("动效：开" if anim.is_enabled() else "动效：关")
        motion.setObjectName("Nav")
        motion.clicked.connect(lambda: self._toggle_motion(motion))
        navl.addWidget(motion)
        self.update_button=QPushButton('软件更新');self.update_button.setObjectName('Nav')
        self.update_button.clicked.connect(lambda:self.go('updates'));navl.addWidget(self.update_button)
        for button in nav.findChildren(QPushButton):button.setFixedHeight(42)
        navl.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        navigation=QScrollArea();navigation.setObjectName('NavigationScroll');navigation.setFixedWidth(174)
        navigation.setWidgetResizable(True);navigation.setFrameShape(QFrame.Shape.NoFrame)
        navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        navigation.setWidget(nav);workbench.addWidget(navigation)

        self.stack = QStackedWidget()
        workbench.addWidget(self.stack, 1)

        self.screens = {}
        for key, cls in [
            ("start", StartScreen), ("brief", BriefScreen), ("architecture", ArchitectureScreen),
            ("physical", PhysicalScreen), ("floorplan", FloorplanScreen), ("package", PackageScreen),
            ("engineering", EngineeringScreen), ("signoff", SignoffScreen), ("report", ReportScreen), ("showcase", ShowcaseScreen), ("tutorial", TutorialScreen),
            ("codex", CodexScreen), ("sources", SourcesScreen), ("labs", LabsScreen), ("studio", StudioScreen),('sandbox',SandboxScreen),('rescue',RescueScreen),('updates',UpdatesScreen),
        ]:
            s = cls(self)
            self.screens[key] = s
            self.stack.addWidget(s)

        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.open_search)
        QShortcut(QKeySequence("Meta+K"), self, activated=self.open_search)
        self._restore()
        self.screens['labs'].restore_workspace()
        self.screens['studio'].restore_workspace()
        self.screens['rescue'].restore_workspace()
        self.screens['updates'].restore_settings()
        self.go("start")
        self.header.update_state(self.result, self.scenario)

    # ---------- state ----------
    def _restore(self):
        data = self._save or {}
        self.progress = data.get("progress", {})
        self.lab_workspace = data.get("lab_workspace", {})
        self.core_workspace = data.get("core_workspace", {})
        self.rescue_workspace=data.get('rescue_workspace',{})
        self.update_settings=data.get('update_settings',{})
        self.sandbox_workspace=data.get('sandbox_workspace',{});self.project_workspace=data.get('project_workspace',{})
        from ..engine.ip_library import validate_asset
        self.ip_library={}
        library=data.get('ip_library',{})
        if isinstance(library,dict):
            for record in list(library.values())[:64]:
                try:
                    asset=validate_asset(record);self.ip_library[asset['id']]=asset
                except (ValueError,TypeError,KeyError):pass
        self.tutorial_id = data.get("tutorial_id")
        self.published_design = data.get("published_design")
        if data.get("design"):
            try:
                self.design = Design.from_dict(data["design"])
                self.scenario = SEGMENTS.get(self.design.scenario_id, SEGMENTS["mid2019"])
                self.result = simulate(self.design)
                self.header.update_state(self.result, self.scenario)
            except Exception:
                self.design = None

    def persist(self):
        if self.design:
            snapshot=dict(design=self.design.to_dict(),published_design=self.published_design,tutorial_id=self.tutorial_id)
            if self.design.scenario_id=='sandbox':self.sandbox_workspace=snapshot
            else:self.project_workspace=snapshot
        savemod.save(dict(design=self.design.to_dict() if self.design else None, progress=self.progress,
                          tutorial_id=self.tutorial_id, published_design=self.published_design,
                          lab_workspace=self.lab_workspace,core_workspace=self.core_workspace,rescue_workspace=self.rescue_workspace,update_settings=self.update_settings,
                          ip_library=self.ip_library,learning_mode=self.learning_mode,
                          sandbox_workspace=self.sandbox_workspace,project_workspace=self.project_workspace))

    def _set_mode(self,*_):
        self.learning_mode=self.mode_picker.currentData()
        if hasattr(self,'screens') and 'labs' in self.screens:
            self.screens['labs'].set_learning_mode()
            self.screens['studio'].set_learning_mode()
        self.persist()

    def _toggle_motion(self, button):
        from . import anim
        anim.set_enabled(not anim.is_enabled())
        button.setText("动效：开" if anim.is_enabled() else "动效：关")

    @property
    def is_released(self):
        return self.design is not None and self.published_design == self.design.to_dict()

    def start_scenario(self, sid: str):
        if sid=='sandbox':self.start_sandbox();return
        self.persist()
        self.tutorial_id = None
        self.design = empty_design(sid)
        self.design.name = f"{SEGMENTS[sid]['name']} SoC"
        reviews = [v.get("review", 75) for v in self.progress.values() if isinstance(v, dict)]
        if reviews:
            self.design.reputation = max(0.0, min(1.0, sum(reviews) / len(reviews) / 100.0))
        self.scenario = SEGMENTS[sid]
        self.result = simulate(self.design)
        self.header.update_state(self.result, self.scenario)
        self.go("brief")
        self.persist()

    def open_search(self):
        dlg = SearchDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.choice:
            self.open_result(dlg.choice)

    def start_sandbox(self,checked=False,fresh=False):
        self.persist()
        saved=self.sandbox_workspace if not fresh else {}
        try:self.design=Design.from_dict(saved['design']) if isinstance(saved,dict) and saved.get('design') else empty_design('sandbox')
        except (ValueError,TypeError,KeyError):self.design=empty_design('sandbox')
        self.design.scenario_id='sandbox'
        if not self.design.name:self.design.name='我的自由设计'
        self.published_design=saved.get('published_design') if isinstance(saved,dict) else None;self.tutorial_id=None
        self.scenario=SEGMENTS['sandbox'];self.recompute_now();self.go('sandbox')

    def return_to_project(self):
        if not isinstance(self.project_workspace,dict) or not self.project_workspace.get('design'):return
        self.persist();saved=self.project_workspace
        self.design=Design.from_dict(saved['design']);self.published_design=saved.get('published_design');self.tutorial_id=saved.get('tutorial_id')
        self.scenario=SEGMENTS[self.design.scenario_id];self.recompute_now();self.go('architecture')

    def open_manual(self):
        from pathlib import Path
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from ..paths import resource_root
        manual=resource_root()/'docs/player-guide/index.html'
        url=QUrl.fromLocalFile(str(manual)) if manual.is_file() else QUrl('https://github.com/qi-1021/silicon-immortal/blob/main/docs/guide/README.md')
        QDesktopServices.openUrl(url)

    def import_soc(self,path=None):
        from PySide6.QtWidgets import QFileDialog,QMessageBox
        from .. import export
        if not isinstance(path,str):
            path,_=QFileDialog.getOpenFileName(self,'导入SoC设计','','Silicon SoC (*.sil *.spchip.json *.json)')
        if not path:return
        try:
            design,notes=export.read_design(path)
            self.persist()
            self.design=design;self.scenario=SEGMENTS.get(design.scenario_id,SEGMENTS['sandbox'])
            self.tutorial_id=None;self.published_design=None
            self.recompute_now(force_layout=False)
            self.hint.setText('已导入 '+design.name+('；'+'；'.join(notes) if notes else ''))
            self.go('architecture')
        except (OSError,ValueError) as ex:QMessageBox.warning(self,'无法读取SoC',str(ex))

    def open_result(self, item: dict):
        kind, ident = item["kind"], item["id"]
        if kind == "chip":
            self.go("codex")
            self.screens["codex"].select_id(ident)
            return
        if kind == "tutorial":
            self.go("tutorial")
            self.screens["tutorial"].select_id(ident)
            return
        if kind == "source":
            s = SOURCES.get(ident, {})
            body = source_text(ident)
            InfoDialog(self, s.get("title", ident), "文献", body).exec()
            return
        if kind == "lab_course":
            self.go("labs")
            self.screens["labs"].select_course(ident)
            return
        if kind == "core":
            c = CORES.get(ident)
            if not c:
                return
            body = (f"{c['arch']} / {c['isa']} · {c['decode']} 宽解码 / ROB {c['rob']}\n"
                    f"IPC 指数 {c['ipc']:.2f} · 参考 {c['ref_node'].upper()} {c['fmax_ref']:.2f}GHz · "
                    f"逻辑面积 {c['logic_area']:.1f}mm² · L2 {c['l2_default']:g}MB\n"
                    f"授权：{c['license']} · 置信度：{c['confidence']}\n\n{c['note']}")
            can_use = c["license"] in ("arm", "riscv")
            InfoDialog(self, c["name"], f"{c['vendor']} · {c['year']} · {c['tier']}",
                       body, "加入沙盒设计" if can_use else None,
                       (lambda: self.use_core_in_sandbox(ident)) if can_use else None).exec()
            return
        if kind == "node":
            n = NODES.get(ident)
            body = f"{n['note']}\n\n面积倍率 {n['area_scale']:.2f}× · 频率 {n['freq_scale']:.2f}× · "                    f"晶圆 ${n['wafer_cost']:,} · D0 {n['d0']} · 成熟度 {n['maturity']:.0%}"
            InfoDialog(self, n["name"], f"{n['vendor']} · {n['year']}", body).exec()
            return
        if kind == "gpu":
            g = GPUS.get(ident)
            body = f"{g['note']}\n\n默认 {g['default_units']}×{g['unit_name']} · CU/单元 {g.get('cu_per_unit',1)} · "                    f"兼容性 {g.get('compat',1)*100:.0f}%"
            InfoDialog(self, g["name"], f"{g['vendor']} · {g['year']}", body).exec()

    def use_core_in_sandbox(self, cid: str):
        c = CORES.get(cid)
        if not c or c["license"] not in ("arm", "riscv"):
            return
        self.start_scenario("sandbox")
        self.design.cores.append(CoreGroup(cid, 2, c["l2_default"], False, 0.0))
        self.design.placements.clear()
        self.result = simulate(self.design)
        self.header.update_state(self.result, self.scenario)
        self.go("architecture")
        self.persist()

    def start_tutorial(self, tid: str):
        lesson = TUTORIAL_BY_ID.get(tid)
        if not lesson:
            return
        self.design = lesson["make"]()
        self.design.name = f"教学 · {lesson['title'].split('：')[-1]}"
        self.scenario = SEGMENTS.get(self.design.scenario_id, SEGMENTS["sandbox"])
        self.tutorial_id = tid
        self.result = simulate(self.design)
        self.header.update_state(self.result, self.scenario)
        self.go("tutorial")
        self.persist()

    def load_blueprint_as_design(self, bp):
        """从图鉴“复刻”到沙盒（近似配置，不是精确复刻）。"""
        spec = bp.get("build")
        if not spec:
            return
        self.tutorial_id = None
        d = empty_design("sandbox")
        d.name = f"{bp['name']} 复刻"
        d.node_id = spec["node"]
        d.cores = [CoreGroup(cid, n, l2, False, clk) for cid, n, l2, clk in spec["cores"]]
        d.l3_mb = spec["l3"]
        d.slc_mb = float(spec.get("slc", 0))
        d.dram = str(spec.get("dram", d.dram))
        d.gpu_id, d.gpu_units = spec["gpu"]
        d.npu_id = spec["npu"]
        d.modem_id = spec["modem"]
        d.price = spec["price"]
        d.chiplet = bool(spec.get("chiplet", False))
        d.package_id = "imc25d" if (d.chiplet or bp["id"] in ("m1", "m4", "m5", "d9500", "xringO3", "kirin9030", "kirin9050", "kirin9050pro")) else "fowlp"
        d.cooling_id = "laptop" if bp["id"] in ("m1", "m4") else "vcPro"
        d.ambient_c = 25
        d.placements.clear()
        self.design = d
        self.scenario = SEGMENTS["sandbox"]
        self.result = simulate(d)
        self.header.update_state(self.result, self.scenario)
        self.go("architecture")
        self.hint.setText(f"已载入近似复刻：{bp['name']}（沙盒）")

    # ---------- navigation ----------
    def go(self, key: str):
        if self._timer.isActive():
            self.recompute_now(self._force_layout)
        if key not in self.screens:
            return
        if key not in ("start", "codex", "sources", "tutorial", "labs", "studio",'rescue','updates') and not self.design:
            key = "start"
        self.stack.setCurrentWidget(self.screens[key])
        self.nav_group.setExclusive(False)
        for k, b in self.nav_buttons.items():
            b.setChecked(k == key)
            b.setEnabled(self.design is not None)
        self.nav_group.setExclusive(True)
        if key in ("report", "showcase") and not self.result:
            self.go("signoff")
            return
        screen = self.screens[key]
        if hasattr(screen, "refresh"):
            screen.refresh()

    # ---------- simulation ----------
    def request_recompute(self, force_layout: bool = False):
        self._force_layout = self._force_layout or force_layout
        self._timer.start(90)

    def _do_recompute(self):
        if not self.design:
            return
        self.result = simulate(self.design, force_layout=self._force_layout)
        self._force_layout = False
        self.header.update_state(self.result, self.scenario)
        screen = self.stack.currentWidget()
        if hasattr(screen, "on_result"):
            screen.on_result()
        self.persist()

    def recompute_now(self, force_layout: bool = False):
        self._timer.stop()
        self._force_layout = force_layout
        self._do_recompute()

    def tape_out(self):
        self.recompute_now(force_layout=False)
        if not self.result:
            return
        if not self.result["signoff"]["ready"]:
            return
        m = self.result["market"]
        self.published_design = self.design.to_dict()
        sid = self.design.scenario_id
        if sid=='sandbox':self.persist();self.go('showcase');return
        best = self.progress.get(sid)
        if not best or m["profit"] > best.get("profit", -1e9):
            self.progress[sid] = dict(grade=m["grade"], profit=m["profit"], review=m["review"],
                challenge_completed=bool(self.result.get('challenge') and self.result['challenge']['ready']))
        self.persist()
        self.go("showcase")

    def next_scenario(self):
        ids = [s["id"] for s in SEGMENT_LIST]
        if self.design and self.design.scenario_id in ids:
            i = ids.index(self.design.scenario_id)
            self.start_scenario(ids[(i + 1) % len(ids)])

    def closeEvent(self,event):
        updates=self.screens.get('updates')
        if updates and updates.busy():
            updates.status.setText('更新任务仍在运行，请等待本次网络操作结束后关闭。')
            self.go('updates');event.ignore();return
        self.persist();super().closeEvent(event)
