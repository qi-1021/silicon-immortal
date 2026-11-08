"""从原始下载记录和正式证据声明构建逐项审计。不会联网或自动认证结论。"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    directory = ROOT / "docs/research"
    raw = directory / "raw"
    if not raw.exists(): raw = ROOT / ".research-cache/raw"
    evidence_path = ROOT / "silicon_professor/data/evidence.json"
    sources = json.loads(evidence_path.read_text())
    for source in sources.values():
        documents = []
        for filename in source.pop("files", []):
            file = raw / filename
            documents.append(dict(file=filename, sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
        if documents:
            source["audit"]["documents"] = documents
    evidence_path.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n")
    legacy = json.loads((directory / "legacy_sources.json").read_text())
    entries = {}
    replacements = {"apple_m4_news": "apple_m4", "apple_m4": "apple_m4", "sifive_p670": "sifive_p670"}
    for sid, old in legacy.items():
        url = old.get("url", "")
        entry = dict(original_title=old["title"], original_url=url,
                     original_year=old.get("year"), disposition="withdrawn")
        if sid in sources:
            entry.update(disposition="corrected", replacement=sid,
                         reason=sources[sid].get("correction") or
                                f"改为明确书目、版本、正文定位和支持范围。状态为 {sources[sid]['verification']}；旧数值校准说法撤回。")
        elif sid in replacements:
            entry.update(disposition="replaced", replacement=replacements[sid],
                         reason="旧条目只有机构主页/模糊标题，替换为已读的具体原始文档；不沿用旧数值推断。")
        elif "bilibili.com/video/" in url:
            file = raw / f"legacy_{sid}.raw"
            if file.exists():
                info = json.loads(file.read_text())
                data = info.get("data") or {}
                entry["retrieval"] = dict(api_code=info.get("code"), sha256=hashlib.sha256(file.read_bytes()).hexdigest())
                if info.get("code") == 0:
                    entry["identity"] = dict(title=data["title"], uploader=data["owner"]["name"],
                        published_at=datetime.datetime.fromtimestamp(data["pubdate"], datetime.timezone.utc).isoformat(),
                        duration_seconds=data["duration"], bvid=data["bvid"])
            entry["reason"] = "视频接口已核对题名、UP 主、发布日期和时长；没有获取/逐段核对视频正文、测试条件及时间戳。元数据不能证明性能排名、黑屏概率、面积或寿命。本条退出正式结论链，保留身份记录；并非判定视频不存在。"
        elif "kurnal-insights.com/uploads/" in url:
            file = raw / f"legacy_{sid}.raw"
            data = file.read_bytes() if file.exists() else b""
            entry["retrieval"] = dict(sha256=hashlib.sha256(data).hexdigest(), observed="HTML 页面，非所请求的 WebP" if b"html" in data[:1000].lower() else "未取得可确认原图")
            entry["reason"] = "直接图片链接返回 HTML/访问检查页面，未取得可核验的原图、作者标注或尺寸测量方法。文件名中的 mm 值不能当实际测量；没有用此图校准模块面积。"
        elif sid == "tensor_g6_leak":
            entry["reason"] = "来源为前瞻媒体链接，未完成正文、原始爆料与实测证据核对；不作已发布规格或 GPU 兼容性结论。"
        elif sid == "dally_towles":
            entry["reason"] = "遗留书目没有页码或具体章节；出版社页访问受限，未取得可核验正文。互连 lab 改为公开算法规则，不引用本书证明数值。"
        elif sid == "irds2023":
            entry["reason"] = "只有 IRDS 主页，没有指定 2023 版报告章节、表格与节点定义；未读取所需原表。不能支撑晶圆价、成熟度、D0 或厂商 SRAM 密度。"
        elif not url:
            entry["reason"] = f"条目“{old['title']}”缺少具体原始文章/文档 URL、出版版本或时间戳，无法从“{old.get('venue','')}”定位支持的事实；撤回全部关联数值与故障归因，不用同主题替代原文。"
        else:
            path = url.split("/", 3)[-1] if url.count("/") >= 3 else ""
            entry["reason"] = f"遗留链接为机构/媒体主页或未定位资料（{url}），未提供文章版本、具体章节或参数表；同名核心/厂商并不能验证 PPA、ROB 或授权价。" if not path or path in ("", "en/", "english/") else "没有获得与条目题名及声称参数相匹配的具体正文；退出正式证据链。"
            if sid in ("arm_a55", "arm_a76"):
                filename = f"{sid}_trm.raw"
                entry["reason"] += " 补查的具体 TRM 页只返回 Arm Developer 页面壳，未取得正文，不能判定技术内容。"
            if sid == "tsmc_n5":
                entry["reason"] += " 补查 5nm 专页返回 HTTP 403，未据此补充未读内容。"
        entries[sid] = entry
    report = dict(checked_on="2026-11-08", policy="正式来源只保留明确身份和范围；书目核验不等于正文核验，参数估算无来源背书。",
                  legacy=entries, active={sid:s["verification"] for sid,s in sources.items()})
    (directory / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    rows = ["# 遗留引用逐项审计\n", "原有 99 条引用全部作出处置；并未声称全部取得全文。以下给出每一条的原题名、链接、处置与具体原因。\n"]
    for sid, entry in entries.items():
        rows += [f"\n## {sid} — {entry['original_title']}\n", f"- 原链接：{entry['original_url'] or '原条目未提供'}\n",
                 f"- 处置：{entry['disposition']}" + (f" → {entry['replacement']}" if entry.get("replacement") else "") + "\n",
                 f"- 原因：{entry['reason']}\n"]
        if entry.get("identity"):
            i = entry["identity"]
            rows.append(f"- 已确认元数据：{i['title']}；{i['uploader']}；{i['published_at']}；{i['duration_seconds']} 秒。未核验正文结论。\n")
    (directory / "LEGACY_AUDIT.md").write_text("".join(rows))
    print(f"Audited {len(entries)} legacy sources, {len(sources)} explicit active sources.")


if __name__ == "__main__": main()
