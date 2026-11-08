"""视觉系统：颜色、字体、QSS。"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont

BG = "#141617"
BG2 = "#191c1e"
PANEL = "#202426"
PANEL2 = "#262b2d"
PANEL3 = "#303638"
BORDER = "#353b3d"
BORDER_HI = "#555e61"
TEXT = "#eeece7"
TEXT2 = "#c0c5c5"
DIM = "#969fa1"
CYAN = "#dbb788"  # 保留控件 API 名称；主色为铜金
CYAN_DIM = "#a48a66"
AMBER = "#e0b776"
RED = "#ed958b"
GREEN = "#a3c7aa"
PURPLE = "#b6a9cd"
BLUE = "#a1bfd0"
PINK = "#cba4b5"

import sys
FONT_UI = "Microsoft YaHei" if sys.platform=='win32' else "PingFang SC" if sys.platform=='darwin' else "Noto Sans CJK SC"
FONT_MONO = "Consolas" if sys.platform=='win32' else "Menlo" if sys.platform=='darwin' else "DejaVu Sans Mono"

TIER_COLORS = {
    1: CYAN, 2: BLUE, 3: AMBER, 4: DIM,
}


def font(size: int = 13, weight: int = 400, mono: bool = False) -> QFont:
    f = QFont(FONT_MONO if mono else FONT_UI)
    f.setPixelSize(size)
    f.setWeight(QFont.Weight(weight))
    return f


def rgba(hex_: str, alpha: float) -> str:
    c = QColor(hex_)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha:.3f})"


def color(hex_: str, alpha: int = 255) -> QColor:
    c = QColor(hex_)
    c.setAlpha(alpha)
    return c


QSS = f"""
* {{
    font-family: "{FONT_UI}";
    font-size: 13px;
    color: {TEXT};
}}
QWidget {{
    background: transparent;
}}
QMainWindow, QWidget#Root {{
    background: {BG};
}}
QFrame#Panel, QWidget#Panel {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#Panel2 {{
    background: {PANEL2};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#Hero {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 16px;
}}
QLabel#H1 {{ font-size: 30px; font-weight: 700; }}
QLabel#H2 {{ font-size: 20px; font-weight: 700; }}
QLabel#H3 {{ font-size: 15px; font-weight: 600; }}
QLabel#Dim {{ color: {TEXT2}; }}
QLabel#Muted {{ color: {DIM}; font-size: 12px; }}
QLabel#Mono {{ font-family: "{FONT_MONO}"; color: {TEXT}; }}
QLabel#Cyan {{ color: {CYAN}; }}
QLabel#Amber {{ color: {AMBER}; }}
QLabel#Red {{ color: {RED}; }}
QLabel#Pill {{
    background: {PANEL3}; border: 1px solid {BORDER_HI};
    border-radius: 9px; padding: 2px 9px; color: {TEXT2}; font-size: 11px;
}}
QPushButton {{
    background: {PANEL2}; border: 1px solid {BORDER};
    border-radius: 7px; padding: 7px 14px; color: {TEXT};
    font-size: 13px;
}}
QPushButton:hover {{ background: {PANEL3}; border-color: {BORDER_HI}; }}
QPushButton:pressed {{ background: {BG}; border-color: {CYAN_DIM}; }}
QPushButton:disabled {{ color: {DIM}; background: {BG2}; }}
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {CYAN_DIM};
}}
QPushButton:checked {{
    background: {rgba(CYAN, 0.12)};
    border: 1px solid {CYAN_DIM}; color: {CYAN};
}}
QPushButton#Primary {{
    background: {CYAN}; color: #241d14; border: 1px solid {CYAN}; font-weight: 600;
}}
QPushButton#Primary:hover {{ background: #e7cba7; border-color: #e7cba7; }}
QPushButton#Primary:pressed {{ background: #bc9a70; border-color: #bc9a70; }}
QPushButton#Primary:disabled {{ background: {PANEL3}; color: {DIM}; border-color: {BORDER}; }}
QPushButton#Nav {{ text-align:left; padding:10px 12px; background:transparent; border:1px solid transparent; }}
QPushButton#Nav:hover {{ background:{PANEL}; }}
QPushButton#Nav:checked {{ background:{PANEL2}; color:{CYAN}; border-color:{BORDER}; }}
QPushButton#Nav:focus {{ border-color:{CYAN_DIM}; }}
QFrame#Sidebar {{ background:{BG2}; border-right:1px solid {BORDER}; }}
QPushButton#Danger {{ border-color: #5b2630; color: {RED}; }}
QPushButton#Ghost {{ background: transparent; border: 1px solid {BORDER}; }}
QLineEdit {{
    background: {BG2}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 5px 8px; color: {TEXT}; min-height: 20px;
}}
QLineEdit:hover {{ border-color: {BORDER_HI}; }}
QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {BG2}; border: 1px solid {BORDER};
    border-radius: 6px; padding: 5px 8px; min-height: 20px;
}}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {BORDER_HI}; }}
QComboBox QAbstractItemView {{
    background: {PANEL2}; border: 1px solid {BORDER_HI};
    selection-background-color: {PANEL3}; color: {TEXT};
}}
QMenu {{ background-color:{PANEL}; color:{TEXT}; border:1px solid {BORDER_HI}; padding:6px; }}
QMenu::item {{ background-color:{PANEL}; padding:8px 16px; border-radius:4px; }}
QMenu::item:selected {{ background-color:{PANEL3}; color:{CYAN}; }}
QMenu::item:disabled {{ color:{DIM}; }}
QMenu::separator {{ height:1px; background-color:{BORDER}; margin:5px 8px; }}
QPlainTextEdit, QTextEdit {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER}; border-radius:6px; padding:8px; }}
QPlainTextEdit:focus {{ border-color:{CYAN_DIM}; }}
QTabWidget::pane {{ border:1px solid {BORDER}; background:{BG}; }}
QTabBar::tab {{ background:{BG2}; color:{TEXT2}; padding:8px 12px; border:1px solid {BORDER}; }}
QTabBar::tab:selected {{ background:{PANEL2}; color:{CYAN}; }}
QTableWidget {{ background:{BG2}; alternate-background-color:{PANEL}; gridline-color:{BORDER}; border:none; selection-background-color:{PANEL3}; }}
QHeaderView::section {{ background:{PANEL2}; color:{TEXT2}; border:none; padding:6px; }}
QSlider::groove:horizontal {{
    height: 5px; background: {BORDER}; border: none; border-radius: 2px;
}}
QSlider::add-page:horizontal {{
    background: {BORDER}; border-radius: 3px;
}}
QSlider::sub-page:horizontal {{ background: {CYAN}; border-radius: 4px; }}
QSlider::handle:horizontal {{
    width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;
    background: {TEXT}; border: 1px solid {BG};
}}
QSlider::handle:horizontal:hover {{ background: {CYAN}; }}
QCheckBox {{ spacing: 7px; color: {TEXT2}; }}
QCheckBox::indicator {{
    width: 15px; height: 15px; border-radius: 4px;
    border: 1px solid {BORDER_HI}; background: {BG2};
}}
QCheckBox::indicator:checked {{ background: {CYAN}; border-color: {CYAN}; }}
QCheckBox:focus {{ color: {CYAN}; }}
QCheckBox::indicator:hover {{ border-color: {CYAN}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: {BORDER_HI}; border-radius: 5px; min-height: 42px; }}
QScrollBar::handle:vertical:hover {{ background: {CYAN_DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; }}
QScrollBar::handle:horizontal {{ background: {BORDER_HI}; border-radius: 4px; }}
QToolTip {{
    background: {PANEL3}; color: {TEXT}; border: 1px solid {BORDER_HI};
    padding: 6px; border-radius: 5px;
}}
QListWidget {{
    background: transparent; border: none;
}}
QListWidget::item {{
    padding: 10px; border-radius: 7px; color: {TEXT2};
}}
QListWidget::item:selected {{
    background: {PANEL3}; color: {TEXT}; border: 1px solid {BORDER_HI};
}}
"""
