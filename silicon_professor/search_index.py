"""全局搜索索引：芯片、核心、文献、教学、制程、GPU。"""
from __future__ import annotations

from .data.blueprints import BLUEPRINTS
from .data.cores import CORES
from .data.nodes import NODES
from .data.blocks import GPUS
from .data.sources import SOURCES, TIER_LABELS
from .data.tutorials import TUTORIALS
from .data.lab_courses import COURSES


def build_index() -> list[dict]:
    out: list[dict] = []
    for b in BLUEPRINTS:
        out.append(dict(kind="chip", id=b["id"], title=b["name"],
                        subtitle=f"{b['vendor']} · {b['year']} · {b['node'].upper()}",
                        text=f"{b['name']} {b['vendor']} {b['year']} {b['cpu']} {b['gpu']} {b['cache']}"))
    for c in CORES.values():
        out.append(dict(kind="core", id=c["id"], title=c["name"],
                        subtitle=f"{c['vendor']} · {c['year']} · {c['isa']} · {c['tier']}",
                        text=f"{c['name']} {c['vendor']} {c['arch']} {c['year']} {c['isa']} {c['tier']} "
                             + ("RISC-V RV64" if c['isa'] == "riscv" else "")))
    for sid, s in SOURCES.items():
        out.append(dict(kind="source", id=sid, title=s["title"],
                        subtitle=f"T{s['tier']} {TIER_LABELS[s['tier']]} · {s.get('year','')}",
                        text=f"{s['title']} {s.get('authors','')} {s.get('venue','')} {s.get('note','')}"))
    for t in TUTORIALS:
        out.append(dict(kind="tutorial", id=t["id"], title=t["title"],
                        subtitle=t["tag"], text=f"{t['title']} {t['tag']} {t['concept']}"))
    for c in COURSES:
        out.append(dict(kind="lab_course",id=c["id"],title=c["title"],subtitle="LAB · "+c["kind"],
                        text=c["title"]+" "+c["lecture"]))
    for n in NODES.values():
        out.append(dict(kind="node", id=n["id"], title=n["name"],
                        subtitle=f"{n['vendor']} · {n['year']}",
                        text=f"{n['name']} {n['vendor']} {n['year']} {n['note']}"))
    for g in GPUS.values():
        out.append(dict(kind="gpu", id=g["id"], title=g["name"],
                        subtitle=f"{g['vendor']} · {g['year']}",
                        text=f"{g['name']} {g['vendor']} {g['year']} {g['note']}"))
    return out


INDEX = build_index()


def search(query: str, limit: int = 40) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    terms = [t for t in q.split() if t]
    hits = []
    for item in INDEX:
        hay = (item["title"] + " " + item["subtitle"] + " " + item["text"]).lower()
        if all(t in hay for t in terms):
            title = item["title"].lower()
            score = 0
            if title.startswith(q):
                score += 3
            elif q in title:
                score += 2
            score += 1
            hits.append((score, item))
    hits.sort(key=lambda x: (-x[0], x[1]["title"]))
    return [h[1] for h in hits[:limit]]
