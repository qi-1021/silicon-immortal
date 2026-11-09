"""经过明确范围核验的正式资料库。遗留引用的处置见 docs/research/audit.json。"""
import json
from pathlib import Path

SOURCES = json.loads(Path(__file__).with_name("evidence.json").read_text("utf-8"))
from .rescue_sources import RESCUE_SOURCES
SOURCES.update(RESCUE_SOURCES)
TIER_LABELS = {1: "论文 / 规范 / 方法", 2: "官方资料 / 案例", 3: "独立评测", 4: "报道"}


def verification_text(source):
    return {'fulltext_checked':'正文与范围已核验','bibliography_checked':'仅书目已核验',
            'unverified_locator':'仅定位 · 书目/正文待核验'}.get(source['verification'],'未核验')


def source_text(sid):
    s = SOURCES[sid]
    status = verification_text(s)
    return (f"{s['title']}\n{s['authors']}\n{s['venue']}\n{status}\n\n"
            f"原文定位：{s['locator']}\n\n支持：{s['supports']}\n\n"
            f"不支持：{s['does_not_support']}\n\n本作使用：{s['model_use']}\n\n"
            f"链接：{s['url']}")
