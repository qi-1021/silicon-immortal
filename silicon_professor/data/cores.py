"""CPU 核心 IP 目录。

ipc 以 Cortex-X4 = 1.00 归一；fmax/面积为参考节点上的公开资料估算中值。
license: arm / riscv 可授权；research 仅用于图鉴和沙盒“研究沙盒”。
"""
from __future__ import annotations

import math


def _core(**kw):
    kw.setdefault("eco", 1.0)
    kw.setdefault("l2_max", max(kw["l2_default"] * 2, kw["l2_default"]))
    return kw


CORES = {
    # ---------------- Arm 公版：能效小核 ----------------
    "a55": _core(
        id="a55", name="Cortex-A55", vendor="Arm", arch="ARMv8.2-A", isa="armv8",
        year=2017, tier="little", license="arm", ref_node="n7", ipc=0.40,
        fmax_ref=2.0, logic_area=0.27, l2_default=0.256, l2_max=0.512,
        power_ref=0.12, leak_frac=0.22, license_cost_m=1.0, eng_weeks=2,
        decode=2, rob=128,
        note="小核常青树。能效极高，适合背景负载与待机。",
        evidence=[], confidence="high",
    ),
    "a510": _core(
        id="a510", name="Cortex-A510", vendor="Arm", arch="ARMv9-A", isa="armv9",
        year=2021, tier="little", license="arm", ref_node="n5", ipc=0.42,
        fmax_ref=2.2, logic_area=0.22, l2_default=0.256, l2_max=0.512,
        power_ref=0.13, leak_frac=0.23, license_cost_m=1.0, eng_weeks=2,
        decode=2, rob=128,
        note="ARMv9 小核，能效好；性能提升有限。",
        evidence=[], confidence="high",
    ),
    "a520": _core(
        id="a520", name="Cortex-A520", vendor="Arm", arch="ARMv9.2-A", isa="armv9",
        year=2023, tier="little", license="arm", ref_node="n4p", ipc=0.45,
        fmax_ref=2.3, logic_area=0.25, l2_default=0.256, l2_max=0.512,
        power_ref=0.16, leak_frac=0.24, license_cost_m=0.9, eng_weeks=2,
        decode=2, rob=96,
        note="纯 64 位小核。省电，但单核性能很弱。",
        evidence=[], confidence="high",
    ),
    # ---------------- Arm 公版：中核 ----------------
    "a76": _core(
        id="a76", name="Cortex-A76", vendor="Arm", arch="ARMv8.2-A", isa="armv8",
        year=2018, tier="mid", license="arm", ref_node="n7", ipc=0.62,
        fmax_ref=2.8, logic_area=0.89, l2_default=0.512, l2_max=1.0,
        power_ref=0.75, leak_frac=0.20, license_cost_m=2.5, eng_weeks=3,
        decode=4, rob=128,
        note="2019 年的大核答案：性能、面积、成本都均衡。",
        evidence=[], confidence="high",
    ),
    "a77": _core(
        id="a77", name="Cortex-A77", vendor="Arm", arch="ARMv8.2-A", isa="armv8",
        year=2019, tier="mid", license="arm", ref_node="n7", ipc=0.67,
        fmax_ref=2.84, logic_area=1.09, l2_default=0.512, l2_max=1.0,
        power_ref=0.90, leak_frac=0.20, license_cost_m=3.0, eng_weeks=3,
        decode=4, rob=160,
        note="A76 的加宽版，IPC 小涨，面积也涨。",
        evidence=[], confidence="high",
    ),
    "a78": _core(
        id="a78", name="Cortex-A78", vendor="Arm", arch="ARMv8.2-A", isa="armv8",
        year=2020, tier="mid", license="arm", ref_node="n5", ipc=0.72,
        fmax_ref=3.0, logic_area=1.31, l2_default=0.512, l2_max=1.0,
        power_ref=0.85, leak_frac=0.20, license_cost_m=3.0, eng_weeks=3,
        decode=4, rob=160,
        note="N5 时代的中核，能效比漂亮。",
        evidence=[], confidence="high",
    ),
    "a710": _core(
        id="a710", name="Cortex-A710", vendor="Arm", arch="ARMv9-A", isa="armv9",
        year=2021, tier="mid", license="arm", ref_node="n5", ipc=0.80,
        fmax_ref=2.9, logic_area=1.11, l2_default=0.512, l2_max=1.0,
        power_ref=0.72, leak_frac=0.19, license_cost_m=3.5, eng_weeks=4,
        decode=5, rob=192,
        note="ARMv9 首代中核；能效被 A78 反超的争议一代。",
        evidence=[], confidence="medium",
    ),
    "a715": _core(
        id="a715", name="Cortex-A715", vendor="Arm", arch="ARMv9-A", isa="armv9",
        year=2022, tier="mid", license="arm", ref_node="n4p", ipc=0.84,
        fmax_ref=2.9, logic_area=1.04, l2_default=0.512, l2_max=1.0,
        power_ref=0.70, leak_frac=0.18, license_cost_m=3.5, eng_weeks=4,
        decode=5, rob=192,
        note="去掉 AArch32 后面积缩小，2022 旗舰的性价比中核。",
        evidence=[], confidence="high",
    ),
    "a720": _core(
        id="a720", name="Cortex-A720", vendor="Arm", arch="ARMv9.2-A", isa="armv9",
        year=2023, tier="mid", license="arm", ref_node="n4p", ipc=0.88,
        fmax_ref=3.0, logic_area=1.24, l2_default=0.512, l2_max=1.0,
        power_ref=0.78, leak_frac=0.18, license_cost_m=4.0, eng_weeks=4,
        decode=5, rob=224,
        note="2023–2024 旗舰的“大中核”，常被拿来堆 4–5 颗。",
        evidence=[], confidence="high",
    ),
    "a725": _core(
        id="a725", name="Cortex-A725", vendor="Arm", arch="ARMv9.2-A", isa="armv9",
        year=2024, tier="mid", license="arm", ref_node="n3e", ipc=0.94,
        fmax_ref=3.4, logic_area=1.54, l2_default=0.512, l2_max=1.0,
        power_ref=0.82, leak_frac=0.18, license_cost_m=4.5, eng_weeks=5,
        decode=5, rob=256,
        note="玄戒 O1 / 天玑 9400 的中核，IPC 已接近上一代 X 核。",
        evidence=[], confidence="medium",
    ),
    # ---------------- Arm 公版：超大核 ----------------
    "x1": _core(
        id="x1", name="Cortex-X1", vendor="Arm", arch="ARMv8.2-A", isa="armv8",
        year=2020, tier="big", license="arm", ref_node="n5", ipc=0.80,
        fmax_ref=3.0, logic_area=3.55, l2_default=1.0, l2_max=2.0,
        power_ref=1.7, leak_frac=0.18, license_cost_m=4.5, eng_weeks=6,
        decode=5, rob=224,
        note="Arm 第一次卖“超大核”，单核冲高，能效一般。",
        evidence=[], confidence="high",
    ),
    "x2": _core(
        id="x2", name="Cortex-X2", vendor="Arm", arch="ARMv9-A", isa="armv9",
        year=2021, tier="big", license="arm", ref_node="n4p", ipc=0.87,
        fmax_ref=3.1, logic_area=5.5, l2_default=1.0, l2_max=2.0,
        power_ref=2.0, leak_frac=0.18, license_cost_m=5.5, eng_weeks=7,
        decode=6, rob=288,
        note="ARMv9 超大核，面积已接近一个小 GPU。",
        evidence=[], confidence="high",
    ),
    "x3": _core(
        id="x3", name="Cortex-X3", vendor="Arm", arch="ARMv9-A", isa="armv9",
        year=2022, tier="big", license="arm", ref_node="n4p", ipc=0.94,
        fmax_ref=3.3, logic_area=7.8, l2_default=1.0, l2_max=2.0,
        power_ref=2.3, leak_frac=0.18, license_cost_m=6.0, eng_weeks=8,
        decode=6, rob=320,
        note="2022–2023 旗舰标配，面积换单核。",
        evidence=[], confidence="high",
    ),
    "x4": _core(
        id="x4", name="Cortex-X4", vendor="Arm", arch="ARMv9.2-A", isa="armv9",
        year=2023, tier="big", license="arm", ref_node="n4p", ipc=1.00,
        fmax_ref=3.4, logic_area=8.6, l2_default=2.0, l2_max=2.0,
        power_ref=2.6, leak_frac=0.17, license_cost_m=7.0, eng_weeks=9,
        decode=8, rob=384,
        note="基准核。8 宽解码 + 2MB L2，单核强，但很吃面积和电。",
        evidence=[], confidence="high",
    ),
    "x925": _core(
        id="x925", name="Cortex-X925", vendor="Arm", arch="ARMv9.2-A", isa="armv9",
        year=2024, tier="big", license="arm", ref_node="n3e", ipc=1.17,
        fmax_ref=3.8, logic_area=11.3, l2_default=2.0, l2_max=3.0,
        power_ref=2.8, leak_frac=0.17, license_cost_m=9.0, eng_weeks=11,
        decode=8, rob=448,
        note="玄戒 O1 的同款大核。N3E + 定制后端能把它推到 3.9GHz。",
        evidence=[], confidence="medium",
    ),
    # ---------------- 服务器 / RISC-V ----------------
    "n2": _core(
        id="n2", name="Neoverse N2", vendor="Arm", arch="ARMv9-A", isa="armv9",
        year=2021, tier="big", license="arm", ref_node="n5", ipc=0.86,
        fmax_ref=3.0, logic_area=3.75, l2_default=1.0, l2_max=2.0,
        power_ref=1.6, leak_frac=0.18, license_cost_m=8.0, eng_weeks=10,
        decode=5, rob=256,
        note="面向服务器/基础设施，追求可扩展与持续性能，不追极限频率。",
        evidence=[], confidence="medium",
    ),
    "v2": _core(
        id="v2", name="Neoverse V2", vendor="Arm", arch="ARMv9-A", isa="armv9",
        year=2022, tier="big", license="arm", ref_node="n5", ipc=1.02,
        fmax_ref=3.0, logic_area=8.5, l2_default=1.0, l2_max=2.0,
        power_ref=3.2, leak_frac=0.17, license_cost_m=12.0, eng_weeks=12,
        decode=8, rob=448,
        note="服务器大核，单核强、面积大，适合笔记本/服务器而不是手机。",
        evidence=[], confidence="medium",
    ),
    "p670": _core(
        id="p670", name="SiFive P670", vendor="SiFive", arch="RV64GCV", isa="riscv",
        year=2023, tier="mid", license="riscv", ref_node="n5", ipc=0.64,
        fmax_ref=2.4, logic_area=2.76, l2_default=0.512, l2_max=1.0,
        power_ref=1.2, leak_frac=0.20, license_cost_m=2.0, eng_weeks=6,
        decode=4, rob=192, eco=0.72,
        note="RISC-V 高性能核。授权自由，但 Android 生态仍是短板。",
        evidence=[], confidence="low",
    ),
    "p870": _core(
        id="p870", name="SiFive P870", vendor="SiFive", arch="RV64GCV", isa="riscv",
        year=2024, tier="big", license="riscv", ref_node="n5", ipc=0.78,
        fmax_ref=2.8, logic_area=4.0, l2_default=1.0, l2_max=2.0,
        power_ref=1.5, leak_frac=0.19, license_cost_m=3.0, eng_weeks=8,
        decode=6, rob=256, eco=0.74,
        note="RISC-V 目前的旗舰级核心；生态投入决定它能不能卖。",
        evidence=[], confidence="low",
    ),
    "c910": _core(
        id="c910", name="XuanTie C910", vendor="T-Head", arch="RV64GC", isa="riscv",
        year=2019, tier="mid", license="riscv", ref_node="n7", ipc=0.45,
        fmax_ref=2.5, logic_area=2.2, l2_default=0.512, l2_max=1.0,
        power_ref=1.0, leak_frac=0.21, license_cost_m=0.5, eng_weeks=4,
        decode=3, rob=128, eco=0.66,
        note="低成本 RISC-V 核。适合 IoT/工业，不适合旗舰手机。",
        evidence=[], confidence="low",
    ),
    # ---------------- 研究档案：自研核，不对外授权 ----------------
    "icestorm": _core(
        id="icestorm", name="Apple Icestorm", vendor="Apple", arch="ARMv8.5-A (自定义)",
        isa="armv8", year=2020, tier="little", license="research", ref_node="n5",
        ipc=0.62, fmax_ref=2.06, logic_area=1.2, l2_default=1.0, l2_max=1.0,
        power_ref=0.35, leak_frac=0.16, license_cost_m=None, eng_weeks=0,
        decode=4, rob=192, eco=1.0,
        note="苹果小核：单核性能接近同期 Arm 中核，能效极高。",
        evidence=[], confidence="medium",
    ),
    "sawtooth": _core(
        id="sawtooth", name="Apple Sawtooth", vendor="Apple", arch="ARMv8.6-A (自定义)",
        isa="armv9", year=2022, tier="little", license="research", ref_node="n3e",
        ipc=0.72, fmax_ref=2.9, logic_area=1.6, l2_default=1.0, l2_max=1.0,
        power_ref=0.45, leak_frac=0.16, license_cost_m=None, eng_weeks=0,
        decode=4, rob=224, eco=1.0,
        note="A16/M 系列的小核，能效核里的性能怪。",
        evidence=[], confidence="low",
    ),
    "firestorm": _core(
        id="firestorm", name="Apple Firestorm", vendor="Apple", arch="ARMv8.5-A (自定义)",
        isa="armv8", year=2020, tier="big", license="research", ref_node="n5",
        ipc=1.12, fmax_ref=3.2, logic_area=3.95, l2_default=3.0, l2_max=3.0,
        power_ref=4.2, leak_frac=0.15, license_cost_m=None, eng_weeks=0,
        decode=8, rob=630, eco=1.0,
        note="8 宽解码、超大 ROB、巨大共享 L2。苹果单核神话的物理基础。",
        evidence=[], confidence="medium",
    ),
    "everest": _core(
        id="everest", name="Apple Everest", vendor="Apple", arch="ARMv8.6-A (自定义)",
        isa="armv9", year=2022, tier="big", license="research", ref_node="n4p",
        ipc=1.18, fmax_ref=3.5, logic_area=4.0, l2_default=4.0, l2_max=4.0,
        power_ref=5.0, leak_frac=0.15, license_cost_m=None, eng_weeks=0,
        decode=8, rob=700, eco=1.0,
        note="A16/M2 的大核，宽后端 + 低延迟大缓存，能效比极高。",
        evidence=[], confidence="low",
    ),
    "m4p": _core(
        id="m4p", name="Apple M4 P-core", vendor="Apple", arch="ARMv9 (自定义)",
        isa="armv9", year=2024, tier="big", license="research", ref_node="n3e",
        ipc=1.30, fmax_ref=4.4, logic_area=4.6, l2_default=4.0, l2_max=4.0,
        power_ref=5.4, leak_frac=0.15, license_cost_m=None, eng_weeks=0,
        decode=10, rob=800, eco=1.0,
        note="4.4GHz 风冷笔记本核。超宽后端 + N3E + 大缓存，不是靠暴力电压。",
        evidence=[], confidence="low",
    ),
    "oryon": _core(
        id="oryon", name="Qualcomm Oryon", vendor="Qualcomm", arch="ARMv8.7-A (自定义)",
        isa="armv9", year=2023, tier="big", license="research", ref_node="n4p",
        ipc=1.16, fmax_ref=3.8, logic_area=4.6, l2_default=3.0, l2_max=3.0,
        power_ref=4.6, leak_frac=0.16, license_cost_m=None, eng_weeks=0,
        decode=8, rob=640, eco=1.0,
        note="Nuvia 团队作品。高频率 + 大缓存，PC 向设计思路。",
        evidence=[], confidence="medium",
    ),
    "oryon2": _core(
        id="oryon2", name="Qualcomm Oryon 2nd Gen", vendor="Qualcomm", arch="ARMv9 (自定义)",
        isa="armv9", year=2024, tier="big", license="research", ref_node="n3e",
        ipc=1.22, fmax_ref=4.3, logic_area=5.2, l2_default=3.0, l2_max=3.0,
        power_ref=5.0, leak_frac=0.16, license_cost_m=None, eng_weeks=0,
        decode=8, rob=704, eco=1.0,
        note="第二代 Oryon，频率和 IPC 同时提升，面积代价明显。",
        evidence=[], confidence="low",
    ),
    "taishan": _core(
        id="taishan", name="Huawei Taishan", vendor="Huawei", arch="ARMv8.2-A (自定义)",
        isa="armv8", year=2023, tier="mid", license="research", ref_node="smicN2",
        ipc=0.55, fmax_ref=2.62, logic_area=1.8, l2_default=0.512, l2_max=1.0,
        power_ref=1.2, leak_frac=0.22, license_cost_m=None, eng_weeks=0,
        decode=4, rob=192, eco=1.0,
        note="受限节点上的自研核；架构不差，制程拖了后腿。",
        evidence=[], confidence="low",
    ),
    "mongoose": _core(
        id="mongoose", name="Samsung Mongoose M5", vendor="Samsung", arch="ARMv8.2-A (自定义)",
        isa="armv8", year=2020, tier="big", license="research", ref_node="sf4",
        ipc=0.72, fmax_ref=2.7, logic_area=3.2, l2_default=2.0, l2_max=2.0,
        power_ref=2.2, leak_frac=0.24, license_cost_m=None, eng_weeks=0,
        decode=6, rob=384, eco=1.0,
        note="三星自研大核的最后一舞：频率上不去、功耗压不住，最终回归 Arm 公版。",
        evidence=[], confidence="low",
    ),
    "xringX925": _core(
        id="xringX925", name="XRING O1 · X925 定制版", vendor="Xiaomi", arch="ARMv9.2-A",
        isa="armv9", year=2025, tier="big", license="research", ref_node="n3e",
        ipc=1.17, fmax_ref=3.9, logic_area=10.6, l2_default=2.0, l2_max=2.0,
        power_ref=2.8, leak_frac=0.17, license_cost_m=None, eng_weeks=0,
        decode=8, rob=448, eco=1.0,
        note="同一份 Arm RTL，自研后端 + 更激进的库与时钟树，频率高于公版参考实现。",
        evidence=[], confidence="low",
    ),
}

def custom_ip(core) -> dict:
    """把自研核参数变成一颗可参与仿真的 IP。"""
    decode = max(1, min(12, core.decode))
    rob = max(1, min(1024, core.rob))
    l1 = max(1, min(256, core.l1_kb))
    pipe = max(2, min(24, core.pipeline))
    backend = max(1, min(12, core.backend))
    from ..engine.lab_cpu import profile_ipc
    measured_ipc = profile_ipc(decode, rob, backend, pipe, l1)
    baseline_ipc = profile_ipc(6, 320, 6, 12, 64)
    # 游戏分数的归一标尺；实际可复现的 IPC 单独返回，不称作 Cortex 等效 IPC。
    ipc = max(0.2, min(2.5, 0.9 * measured_ipc / baseline_ipc))
    area = (1.60 + 0.28 * decode + 0.0025 * rob + 0.006 * l1
            + 0.18 * backend + 0.04 * max(0, pipe - 10))
    # 理想均分逻辑延迟 + 寄存器开销，单位 ps；这些数值是显式游戏假设。
    logic_delay_ps = 2600 + 60 * (decode - 6) + 50 * (backend - 6) + 0.25 * (rob - 320)
    fmax = 1000 / (logic_delay_ps / pipe + 70)
    extensions = getattr(core, "extensions", ["M"])
    area += (0.25 if "M" in extensions else 0) + (0.10 if "Zbb" in extensions else 0)
    power = 0.8 + 0.12 * decode + 0.001 * rob + 0.005 * l1 + 0.10 * backend
    isa = core.isa if core.isa in ("armv8", "armv9", "riscv") else "armv9"
    return dict(
        id="custom", name=core.name, vendor="In-house", arch=("RV32I lab · M/RV32 Zbb按配置" if isa == "riscv" else "Arm 概念核 · RV32 代理工作负载"),
        isa=isa, year=2026, tier="big", license="custom", ref_node="n3e",
        ipc=ipc, fmax_ref=fmax, logic_area=area, l2_default=1.0, l2_max=4.0,
        power_ref=power, leak_frac=0.16, license_cost_m=0.0, eng_weeks=24,
        decode=decode, rob=rob, eco=(0.72 if isa == "riscv" else 1.0),
        measured_ipc=measured_ipc, benchmark_basis="rv32-three-program-profile-v1",
        extensions=list(extensions),
        parameter_basis="game_assumption",
        note="动态轨迹工作负载推导游戏性能指标；Fmax/面积/功耗仍为显式假设，未综合 RTL。",
        evidence=[],
        confidence="low",
    )


def get_ip(design, cid: str):
    if cid.startswith('ip:'):
        from ..engine.ip_library import asset_model
        record=design.embedded_ips.get(cid[3:])
        return asset_model(record) if record and record['kind']=='cpu' else None
    if cid == "custom":
        return custom_ip(getattr(design, "custom", None) or type("C", (), dict(
            decode=6, rob=320, l1_kb=64, pipeline=12, backend=6, isa="armv9", name="自研大核"))())
    from ..engine.core_bundle import template_model
    return template_model(design,'cpu',cid) or CORES.get(cid)



# ---------------- 2025 新一代 Arm / RISC-V / 自研 ----------------
CORES.update({
    "c1_ultra": _core(
        id="c1_ultra", name="Arm C1-Ultra", vendor="Arm", arch="ARMv9.3-A", isa="armv9",
        year=2025, tier="big", license="arm", ref_node="n3p", ipc=1.30,
        fmax_ref=4.4, logic_area=7.5, l2_default=3.0, l2_max=4.0,
        power_ref=3.0, leak_frac=0.16, license_cost_m=11.0, eng_weeks=13,
        decode=10, rob=640,
        note="Arm 2025 CSS 旗舰核：更宽的后端与更大的 L2，目标 4GHz 级。",
        evidence=[], confidence="low",
    ),
    "c1_premium": _core(
        id="c1_premium", name="Arm C1-Premium", vendor="Arm", arch="ARMv9.3-A", isa="armv9",
        year=2025, tier="big", license="arm", ref_node="n3p", ipc=1.18,
        fmax_ref=3.9, logic_area=5.0, l2_default=2.0, l2_max=3.0,
        power_ref=2.4, leak_frac=0.17, license_cost_m=8.0, eng_weeks=10,
        decode=8, rob=512,
        note="次旗舰大核，面积/频率平衡点。",
        evidence=[], confidence="low",
    ),
    "c1_pro": _core(
        id="c1_pro", name="Arm C1-Pro", vendor="Arm", arch="ARMv9.3-A", isa="armv9",
        year=2025, tier="mid", license="arm", ref_node="n3p", ipc=1.06,
        fmax_ref=3.6, logic_area=3.0, l2_default=1.0, l2_max=2.0,
        power_ref=1.3, leak_frac=0.18, license_cost_m=5.0, eng_weeks=6,
        decode=6, rob=384,
        note="2025 中核，接替 A725 的位置。",
        evidence=[], confidence="low",
    ),
    "c1_nano": _core(
        id="c1_nano", name="Arm C1-Nano", vendor="Arm", arch="ARMv9.3-A", isa="armv9",
        year=2025, tier="little", license="arm", ref_node="n3p", ipc=0.80,
        fmax_ref=3.0, logic_area=0.5, l2_default=0.256, l2_max=0.512,
        power_ref=0.28, leak_frac=0.22, license_cost_m=1.5, eng_weeks=2,
        decode=3, rob=128,
        note="新一代小核，性能接近旧中核，待机功耗低。",
        evidence=[], confidence="low",
    ),
    "c930": _core(
        id="c930", name="XuanTie C930", vendor="T-Head", arch="RV64GCV", isa="riscv",
        year=2025, tier="mid", license="riscv", ref_node="n5", ipc=0.72,
        fmax_ref=2.8, logic_area=3.2, l2_default=1.0, l2_max=2.0,
        power_ref=1.3, leak_frac=0.20, license_cost_m=1.0, eng_weeks=6,
        decode=4, rob=256, eco=0.70,
        note="RISC-V 高性能核；Android 生态需要大量适配。",
        evidence=[], confidence="low",
    ),
    "x280": _core(
        id="x280", name="SiFive X280", vendor="SiFive", arch="RV64GCV", isa="riscv",
        year=2022, tier="big", license="riscv", ref_node="n5", ipc=0.80,
        fmax_ref=2.6, logic_area=4.0, l2_default=1.0, l2_max=2.0,
        power_ref=1.8, leak_frac=0.19, license_cost_m=2.5, eng_weeks=8,
        decode=6, rob=320, eco=0.74,
        note="带向量扩展的 RISC-V 核；AI/媒体场景有潜力，通用生态仍弱。",
        evidence=[], confidence="low",
    ),
    "oryon3": _core(
        id="oryon3", name="Qualcomm Oryon 3rd Gen", vendor="Qualcomm", arch="ARMv9 (自定义)",
        isa="armv9", year=2025, tier="big", license="research", ref_node="n3p",
        ipc=1.32, fmax_ref=4.6, logic_area=5.4, l2_default=3.0, l2_max=3.0,
        power_ref=5.4, leak_frac=0.16, license_cost_m=None, eng_weeks=0,
        decode=9, rob=768, eco=1.0,
        note="第二代 Oryon 之后的 PC/手机向自研核，频率继续上探。",
        evidence=[], confidence="low",
    ),
    "a19p": _core(
        id="a19p", name="Apple A19 Pro P-core", vendor="Apple", arch="ARMv9 (自定义)",
        isa="armv9", year=2025, tier="big", license="research", ref_node="n3p",
        ipc=1.38, fmax_ref=4.3, logic_area=4.8, l2_default=4.0, l2_max=4.0,
        power_ref=5.2, leak_frac=0.15, license_cost_m=None, eng_weeks=0,
        decode=10, rob=800, eco=1.0,
        note="A19 Pro 的大核，继续走超宽 + 大缓存路线。",
        evidence=[], confidence="low",
    ),
    "m5p": _core(
        id="m5p", name="Apple M5 P-core", vendor="Apple", arch="ARMv9 (自定义)",
        isa="armv9", year=2025, tier="big", license="research", ref_node="n3p",
        ipc=1.42, fmax_ref=4.6, logic_area=5.2, l2_default=4.0, l2_max=4.0,
        power_ref=5.6, leak_frac=0.15, license_cost_m=None, eng_weeks=0,
        decode=10, rob=840, eco=1.0,
        note="M5 的 P-core，面向笔记本/平板的持续性能。",
        evidence=[], confidence="low",
    ),
    "taishan2": _core(
        id="taishan2", name="Huawei Taishan 2.0 (3nm)", vendor="Huawei", arch="ARMv9 (自定义)",
        isa="armv9", year=2025, tier="big", license="research", ref_node="n3e",
        ipc=0.82, fmax_ref=3.2, logic_area=3.0, l2_default=1.0, l2_max=2.0,
        power_ref=2.2, leak_frac=0.20, license_cost_m=None, eng_weeks=0,
        decode=6, rob=320, eco=1.0,
        note="泰山 2.0：架构落后一代，但靠 3nm/系统优化仍能打。",
        evidence=[], confidence="low",
    ),
    "taishan2_5nm": _core(
        id="taishan2_5nm", name="Huawei Taishan 2.0 (5nm)", vendor="Huawei", arch="ARMv9 (自定义)",
        isa="armv9", year=2025, tier="big", license="research", ref_node="n5",
        ipc=1.02, fmax_ref=3.4, logic_area=3.2, l2_default=1.0, l2_max=2.0,
        power_ref=2.4, leak_frac=0.22, license_cost_m=None, eng_weeks=0,
        decode=6, rob=320, eco=1.0,
        note="同一代泰山架构的 5nm 版本：面积更大、频率更低，靠设计补。",
        evidence=[], confidence="low",
    ),
})

CORE_LIST = [c for c in CORES.values() if c["license"] != "research"]
CORE_BY_ID = {c["id"]: c for c in CORES.values()}
LICENSABLE = {c["id"] for c in CORE_LIST}
RESEARCH = [c for c in CORES.values() if c["license"] == "research"]

# ---------------- Arm C2（2026，D9600 Pro 实测） ----------------
CORES.update({
    "c2_ultra": _core(
        id="c2_ultra", name="Arm C2-Ultra", vendor="Arm", arch="ARMv9.4-A", isa="armv9",
        year=2026, tier="big", license="arm", ref_node="n2", ipc=1.42,
        fmax_ref=4.55, logic_area=8.0, l2_default=4.0, l2_max=4.0,
        power_ref=3.2, leak_frac=0.16, license_cost_m=13.0, eng_weeks=14,
        decode=10, rob=704,
        note="Kurnal D9600 die shot 实测：C2 Ultra@4.55GHz，2 颗，配 4MB 私有 L2。2nm 首发架构。",
        evidence=[], confidence="low",
    ),
    "c2_pro": _core(
        id="c2_pro", name="Arm C2-Pro", vendor="Arm", arch="ARMv9.4-A", isa="armv9",
        year=2026, tier="mid", license="arm", ref_node="n2", ipc=1.18,
        fmax_ref=4.35, logic_area=4.5, l2_default=2.0, l2_max=4.0,
        power_ref=1.6, leak_frac=0.17, license_cost_m=6.0, eng_weeks=7,
        decode=6, rob=448,
        note="Kurnal D9600 die shot 实测：C2 Pro@4.35GHz，中核位置，面积效率高于 C2-Ultra。",
        evidence=[], confidence="low",
    ),
})

for _item in CORES.values():
    _item["parameter_basis"] = "game_assumption"

for _cid in ("a55", "a510", "a520"):
    CORES[_cid]["rob"] = 0
    CORES[_cid]["execution_model"] = "in_order"
CORES["p670"]["evidence"] = ["sifive_p670"]
for _c in CORES.values():
    _c["note"] = "游戏参数集：IPC、Fmax、面积、功耗、ROB 与许可费用未逐项由厂商规格校准。具体产品的 ISA 与微架构需查其原始手册。"

CORES['x86_lab']=_core(id='x86_lab',name='LAB IA-32 示例核',vendor='LAB',arch='IA-32 integer subset',isa='x86_32',year=2026,
    tier='big',license='research',ref_node='n3e',ipc=.9,fmax_ref=3.0,logic_area=5.0,l2_default=1.0,l2_max=8.0,power_ref=2.0,
    leak_frac=.16,license_cost_m=None,eng_weeks=0,decode=4,rob=128,note='x86教学PPA假设；保存实验核后使用独立资产，不是厂商CPU。',
    evidence=[],confidence='assumption',parameter_basis='game_assumption')
