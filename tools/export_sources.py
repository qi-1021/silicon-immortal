"""导出参考文献为 Markdown。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from silicon_professor.data.sources import SOURCES, TIER_LABELS

out = Path(__file__).resolve().parents[1] / "docs" / "REFERENCES.md"
lines = ["# 参考文献与证据等级\n",
         f"正式来源 {len(SOURCES)} 条：正文核验与仅书目核验分别标注。模型数字为游戏假设，除明确字段级证明外不声称来自论文。\n",
         "[原有 99 条引用的逐项处置](research/LEGACY_AUDIT.md)；[机器可读核验记录](research/audit.json)。\n"]
for tier in (1, 2, 3, 4):
    lines.append(f"\n## T{tier} · {TIER_LABELS[tier]}\n")
    for sid, s in SOURCES.items():
        if s["tier"] != tier:
            continue
        lines.append(f"### {s['title']}\n")
        lines.append(f"- id: `{sid}`\n")
        lines.append(f"- 作者/机构: {s.get('authors','')}\n")
        lines.append(f"- 出处: {s.get('venue','')} ({s.get('year','')})\n")
        lines.append(f"- 核验状态: {s.get('verification', 'not_audited')}\n")
        if s.get("url"):
            lines.append(f"- 链接: {s['url']}\n")
        for key,title in (("locator","原文定位"),("supports","支持"),("does_not_support","不支持"),("model_use","本作使用")):
            lines.append(f"- {title}: {s[key]}\n")
        if s.get('fulltext_url'):
            lines.append(f"- 可读作者稿/全文: {s['fulltext_url']}\n")
        for document in s['audit'].get('documents',[]):
            lines.append(f"- 核验文件: `{document['file']}` · SHA-256 `{document['sha256']}`\n")
out.write_text("".join(lines), "utf-8")
print(f"wrote {out} ({len(SOURCES)} sources)")
