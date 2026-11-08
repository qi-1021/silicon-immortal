"""设计文件导出：其他客户端可读取的稳定 JSON 格式。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from .version import MODEL_VERSION,producer,compatibility_notes,diagnostic

FORMAT = "silicon-professor/design"
VERSION = 1


def payload(design, result) -> dict:
    from .engine.core_bundle import SCHEMA,materialize
    p = result.get("perf", {}) if result else {}
    m = result.get("market", {}) if result else {}
    return {
        "format": FORMAT,
        "version": VERSION,
        "producer": producer(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "name": design.name,
        "scenario": design.scenario_id,
        "design": materialize(design),
        "core_bundle": {"schema": SCHEMA},
        "summary": {
            "die_area_mm2": round(result.get("die_area", 0), 3) if result else None,
            "st": round(p.get("st_burst", 0), 1) if p else None,
            "mt": round(p.get("mt_burst", 0), 1) if p else None,
            "gpu": round(p.get("gpu", 0), 1) if p else None,
            "ai_tops": round(p.get("ai", 0), 1) if p else None,
            "ai_score": round(p.get("ai", 0), 1) if p else None,
            "peak_power_w": round(result.get("power", {}).get("peak", 0), 2) if result else None,
            "unit_cost_usd": round(result.get("cost", {}).get("total", 0), 2) if result else None,
            "review": round(m.get("review", 0), 1) if m else None,
            "grade": m.get("grade") if m else None,
            "valid": bool(result.get("valid")) if result else None,
        },
        "engine": {"name": "Silicon Professor", "model": MODEL_VERSION},
        "provenance": {"simulation": True, "visuals": "procedural-floorplan-illustration",
                       "legacy_ai_tops_is_score": True,
                       "signoff_ready": bool(result and result.get("signoff", {}).get("ready"))},
    }


def export_to(path: str | Path, design, result) -> Path:
    p = Path(path)
    if not p.suffix:p=p.with_suffix('.sil')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload(design, result), ensure_ascii=False, indent=2, allow_nan=False), "utf-8")
    return p


def read_design(path):
    """读取.sil及旧JSON文件；未知顶层字段不阻塞，版本信息只供诊断。"""
    from .engine.types import Design
    p=Path(path)
    if p.stat().st_size>12_000_000:raise ValueError('SoC文件超过12MB。')
    record=None
    try:
        record=json.loads(p.read_text('utf-8'))
        if not isinstance(record,dict) or record.get('format')!=FORMAT:raise ValueError('文件内容不是Silicon SoC格式。')
        if not isinstance(record.get('design'),dict):raise ValueError('缺少design对象。')
        from .engine.design_input import validate_design_record
        notes=validate_design_record(record['design'])
        from .engine.core_bundle import SCHEMA,check_complete
        if 'core_bundle' in record:
            bundle=record['core_bundle']
            if not isinstance(bundle,dict) or bundle.get('schema')!=SCHEMA:raise ValueError('本版无法解释此core_bundle结构。')
            check_complete(record['design'])
        else:notes.append('旧文件没有完整核心包声明；未内嵌的模板使用本机目录参数。')
        design=Design.from_dict(record['design'])
        from .engine.simulate import simulate
        simulate(design) # 检查已理解的ID和数值模型能否重放，不信任summary。
        return design,compatibility_notes(record,VERSION)+notes
    except (UnicodeError,json.JSONDecodeError,ValueError,TypeError,KeyError,OverflowError,RecursionError) as ex:
        raise ValueError(f'{ex}\n{diagnostic(record)}') from ex


def export_dieshot_png(path: str | Path, design, result, width: int = 1600, mode: str = "silicon") -> Path:
    """把当前 floorplan 渲染成带标题/图例的高清 Die Shot PNG。"""
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QImage, QPainter

    from .ui.die_render import render_die
    from .ui.silicon_render import render_silicon
    from .ui.wafer_render import render_wafer
    from .ui import theme as T
    from PySide6.QtCore import QRectF, Qt

    if mode not in ("silicon", "wafer", "layout"):
        raise ValueError("只导出当前设计的硅片、晶圆或布局模拟图。")
    if width < 320 or width > 8192:
        raise ValueError("图片宽度应介于 320 与 8192 像素。")

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    plan = (result or {}).get("plan")
    node = (result or {}).get("node", {})
    perf = (result or {}).get("perf", {})
    mkt = (result or {}).get("market", {})
    title = design.name or "未命名芯片"
    subtitle = (f"{node.get('name', '')} · {plan.die_w:.1f}×{plan.die_h:.1f}mm · "
                f"{plan.die_area:.1f}mm²" if plan is not None else "")
    height = int(width * 0.72)
    if mode == "silicon":
        img = render_silicon(QSize(width, height), plan, seed=design.seed, title=title, subtitle=subtitle, legend=True)
    elif mode == "wafer":
        img = render_wafer(QSize(width, height), plan, seed=design.seed, title=title)
    else:
        img = QImage(width, height, QImage.Format_ARGB32)
    pt = QPainter(img)
    pt.setRenderHint(QPainter.RenderHint.Antialiasing)
    pt.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    if mode == "layout":
        render_die(pt, QSize(width, height), plan, title=title, subtitle=subtitle, legend=True)
    pt.setFont(T.font(11))
    pt.setPen(T.color(T.TEXT2))
    caption = "模拟生成 / SIMULATED · 模块布局来自设计，纹理为示意"
    if mode == "wafer" and design.chiplet:
        caption += " · Chiplet 为逻辑总图示意"
    pt.drawText(QRectF(14, height - 24, width - 28, 18), Qt.AlignmentFlag.AlignCenter, caption)
    pt.end()
    if not img.save(str(p), "PNG"):
        raise OSError(f"无法写入 PNG：{p}")
    return p
