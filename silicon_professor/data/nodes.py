"""制程节点数据。面积为相对 N5 的倍率；成本为教学用估算。"""
from __future__ import annotations

NODES = {
    "n7": dict(
        id="n7", name="TSMC N7", short="N7", vendor="TSMC", year=2018,
        area_scale=1.75, sram_mb=1.10, freq_scale=0.82, leak_scale=1.28,
        wafer_cost=9500, d0=0.12, mask_cost=6, maturity=0.94, vmin=0.60,
        note='成熟 FinFET 节点。表中面积、费用与缺陷参数为教学估算。',
        evidence=[], confidence="high",
    ),
    "n5": dict(
        id="n5", name="TSMC N5", short="N5", vendor="TSMC", year=2020,
        area_scale=1.00, sram_mb=0.85, freq_scale=1.00, leak_scale=1.00,
        wafer_cost=16000, d0=0.09, mask_cost=9, maturity=0.95, vmin=0.58,
        note="第一代大规模量产的 5nm，能效优秀，成本适中。",
        evidence=[], confidence="high",
    ),
    "n4": dict(
        id="n4", name="TSMC N4", short="N4", vendor="TSMC", year=2021,
        area_scale=0.97, sram_mb=0.82, freq_scale=1.03, leak_scale=1.06,
        wafer_cost=16500, d0=0.08, mask_cost=9, maturity=0.94, vmin=0.57,
        note="N5 的光学收缩版，成本略低于 N4P。",
        evidence=[], confidence="medium",
    ),
    "n4p": dict(
        id="n4p", name="TSMC N4P", short="N4P", vendor="TSMC", year=2022,
        area_scale=0.94, sram_mb=0.80, freq_scale=1.06, leak_scale=1.05,
        wafer_cost=17500, d0=0.07, mask_cost=10, maturity=0.93, vmin=0.57,
        note="N5 的性能增强版，2022–2023 旗舰主力。",
        evidence=[], confidence="high",
    ),
    "n3e": dict(
        id="n3e", name="TSMC N3E", short="N3E", vendor="TSMC", year=2023,
        area_scale=0.66, sram_mb=0.60, freq_scale=1.12, leak_scale=1.12,
        wafer_cost=20500, d0=0.10, mask_cost=14, maturity=0.88, vmin=0.55,
        note='N3 工艺家族的一个版本；逻辑、SRAM 与 I/O 的缩放不同。',
        evidence=[], confidence="medium",
    ),
    "n2": dict(
        id="n2", name="TSMC N2", short="N2", vendor="TSMC", year=2025,
        area_scale=0.55, sram_mb=0.50, freq_scale=1.18, leak_scale=0.95,
        wafer_cost=30000, d0=0.12, mask_cost=20, maturity=0.78, vmin=0.52,
        note="GAA 第一代，密度和能效再上一台阶；成本/良率是门槛。",
        evidence=[], confidence="low",
    ),
    "n2p": dict(
        id="n2p", name="TSMC N2P", short="N2P", vendor="TSMC", year=2026,
        area_scale=0.52, sram_mb=0.48, freq_scale=1.22, leak_scale=0.93,
        wafer_cost=33000, d0=0.11, mask_cost=22, maturity=0.75, vmin=0.51,
        note='前瞻工艺情景，具体密度、频率和生产良率待核验。',
        evidence=[], confidence="low",
    ),
    "n3b": dict(
        id="n3b", name="TSMC N3B", short="N3B", vendor="TSMC", year=2023,
        area_scale=0.68, sram_mb=0.62, freq_scale=1.10, leak_scale=1.15,
        wafer_cost=24000, d0=0.13, mask_cost=18, maturity=0.78, vmin=0.55,
        note='早期 N3 工艺情景。成本与成熟度为本作假设，不是已公布的代工厂良率。',
        evidence=[], confidence="low",
    ),
    "n3p": dict(
        id="n3p", name="TSMC N3P", short="N3P", vendor="TSMC", year=2024,
        area_scale=0.62, sram_mb=0.57, freq_scale=1.16, leak_scale=1.10,
        wafer_cost=22500, d0=0.09, mask_cost=15, maturity=0.90, vmin=0.54,
        note="N3E 的光学收缩 + 性能增强，2025 旗舰的稳妥选择。",
        evidence=[], confidence="medium",
    ),
    "sf4": dict(
        id="sf4", name="Samsung SF4", short="SF4", vendor="Samsung", year=2021,
        area_scale=0.98, sram_mb=0.88, freq_scale=0.98, leak_scale=1.18,
        wafer_cost=14500, d0=0.14, mask_cost=8, maturity=0.90, vmin=0.60,
        note="便宜，但漏电和良率波动大，适合价格敏感的产品。",
        evidence=[], confidence="medium",
    ),
    "sf3": dict(
        id="sf3", name="Samsung SF3", short="SF3", vendor="Samsung", year=2024,
        area_scale=0.68, sram_mb=0.64, freq_scale=1.08, leak_scale=1.22,
        wafer_cost=18000, d0=0.16, mask_cost=12, maturity=0.82, vmin=0.57,
        note='GAA 工艺情景；本作参数不提供已测得的跨代工厂性能排名。',
        evidence=[], confidence="low",
    ),
    "intel18a": dict(
        id="intel18a", name="Intel 18A", short="18A", vendor="Intel", year=2025,
        area_scale=0.60, sram_mb=0.58, freq_scale=1.14, leak_scale=0.95,
        wafer_cost=21000, d0=0.12, mask_cost=16, maturity=0.80, vmin=0.55,
        note="背面供电 + GAA，理论性能强；2025 年外部客户良率仍待验证。",
        evidence=[], confidence="low",
    ),
    "smicN2": dict(
        id="smicN2", name="SMIC N+2", short="N+2", vendor="SMIC", year=2023,
        area_scale=1.80, sram_mb=1.15, freq_scale=0.72, leak_scale=1.30,
        wafer_cost=8000, d0=0.20, mask_cost=5, maturity=0.85, vmin=0.65,
        note="受限节点。面积和频率吃亏，但供应链自主，成本低。",
        evidence=[], confidence="low",
    ),
}

NODE_LIST = list(NODES.values())

for _item in NODES.values():
    _item["parameter_basis"] = "game_assumption"

for _node in NODES.values():
    _node["note"] = "教学节点情景：面积、频率、SRAM密度、缺陷率、成熟度与费用均为未校准假设。节点名称不等于物理线宽。"
