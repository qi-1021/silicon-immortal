"""CPU 指令集赛道：Arm / RISC-V / x86 独立成段。

赛道是一等公民：核心目录、生态模型、校验文案都按赛道组织。
新增赛道只需要在 TRACKS 里加一条，再配上对应 isa 的核心数据，
UI（架构页分区）、生态评分、校验会自动跟上。
"""
from __future__ import annotations


TRACKS = {
    "arm": dict(
        id="arm", name="ARM 阵营", short="ARM", available=True,
        match=("armv8", "armv9"),
        eco_base=1.0, eco_gain=0.0,
        tagline="成熟软件栈 · Android 兼容 · 编译器优化齐全",
        note="ARM 阵营：软件栈、Android 兼容性、编译器优化都成熟，开箱即用。",
        evidence=[], confidence="high",
    ),
    "riscv": dict(
        id="riscv", name="RISC-V 阵营", short="RISC-V", available=True,
        match=("riscv",),
        eco_base=0.72, eco_gain=0.20,
        tagline="授权自由、可定制 · 生态短板靠投入补",
        note="RISC-V 阵营：授权更自由、可定制，但驱动、运行时、应用兼容层都要自己补；"
             "生态投入是工程费用，直接决定真实体验和口碑（签核页可调）。",
        eco_note="RISC-V 生态兼容性依赖软件投入。",
        mix_note="ARM 与 RISC-V 混用会带来双软件栈成本。",
        evidence=[], confidence="medium",
    ),
    "x86": dict(
        id="x86", name="x86 · Intel / AMD 指令家族", short="x86", available=True,
        match=("x86_64","x86_32"),
        eco_base=0.60, eco_gain=0.20,
        tagline="32/64位整数核心 · 精简/均衡/性能/吞吐设计 · 无OS/SIMD",
        note="x86提供参数化教学核心、硬件设计与工作站项目。ISA属于Intel/AMD广为使用的家族，模板不是其商业CPU复刻或授权IP。",
        evidence=[], confidence="low",
    ),
}

TRACK_ORDER = ["arm", "riscv", "x86"]


def track_of_isa(isa: str | None) -> str:
    isa = (isa or "").lower()
    for tid, t in TRACKS.items():
        if isa in t["match"]:
            return tid
    if isa.startswith("arm"):
        return "arm"
    return "unknown"


def design_track(design) -> str | None:
    """按现有核心组判定赛道；没有核心组返回 None；混用返回 'mixed'。"""
    found = set()
    for g in getattr(design, "cores", []):
        if getattr(g, "count", 0) <= 0:
            continue
        from .cores import get_ip
        ip = get_ip(design, getattr(g, "core_id", ""))
        if ip:
            found.add(track_of_isa(ip.get("isa")))
    if not found:
        return None
    if len(found) > 1:
        return "mixed"
    return next(iter(found))

for _item in TRACKS.values():
    _item["parameter_basis"] = "game_assumption"
