"""端到端仿真：热 → 频率 → 性能 → 良率 → 成本 → 市场。"""
from __future__ import annotations

import math

from ..data.blocks import (COOLING, DRAMS, FIXED_BLOCKS, GPUS, METAL_STACKS, NOCS, NPUS, PACKAGES, STORAGE)
from ..data.blocks import get_gpu, get_npu, get_isp
from ..data.cores import CORES, get_ip
from ..data.nodes import NODES
from ..data.tracks import TRACKS
from ..data.segments import SEGMENTS
from . import economics, ppa
from .build import build_plan
from .memory import memory_spec
from .engineering import engineering_report, signoff_report
from .rng import clamp, log2, mulberry32

EFF_TYPE = {"big": 0.90, "mid": 0.85, "little": 0.70}
TUNING_OFFICIAL = 0.30


def _total_power(plan, scale: float, design, tuning: float = 0.0, temp: float = 85.0) -> float:
    node = NODES[design.node_id]
    p = 0.0
    for g in plan.groups:
        dyn, leak = ppa.core_power(g.ip, max(0.2, g.clock * scale), g.fmax,
                                   g.area_each, node, g.impl, temp)
        p += (dyn + leak) * g.count
    gpu_power = plan.metrics.get("gpu_power", 0.0)
    p += gpu_power * (scale ** 1.4)
    activity = {"modem": 0.15, "isp": 0.25, "media": 0.10, "display": 0.10,
                "dramphy": 0.50, "io": 0.10, "npu": 0.30, "l2": 0.30,
                "l3": 0.30, "slc": 0.30}
    for b in plan.blocks:
        if b.kind in ("big", "mid", "little", "gpu"):
            continue
        p += b.power * activity.get(b.kind, 0.5)
    p += plan.metrics.get("wire_power", 0.0) * (1.0 + 0.5 * tuning)
    dram = DRAMS.get(design.dram, DRAMS["lpddr4x"])
    p += memory_spec(design)["channels"] * dram["power_per_channel"] * 0.5
    if getattr(design, "chiplet", False):
        p += 0.40  # 跨 die / 中介层链路
    p *= (1.0 + 0.06 * tuning + 0.02 * getattr(design, "bench_isa", 0.0))
    return p


def _solve_scale(plan, design, budget: float, tuning: float, resistance=None) -> tuple[float, float]:
    def power_at(scale):
        if resistance is None:
            return _total_power(plan, scale, design, tuning)
        # 简化稳态热/漏电耦合；阻尼迭代，避免热正反馈直接发散。
        temp = design.ambient_c
        for _ in range(12):
            power = _total_power(plan, scale, design, tuning, temp)
            target = min(160.0, design.ambient_c + power * resistance)
            temp = (temp + target) / 2
        return _total_power(plan, scale, design, tuning, temp)

    if power_at(1.0) <= budget:
        return 1.0, power_at(1.0)
    lo, hi = 0.12, 1.0
    for _ in range(22):
        mid = (lo + hi) / 2
        if power_at(mid) <= budget:
            lo = mid
        else:
            hi = mid
    return lo, power_at(lo)


def _thermal(plan, design, scenario, tuning):
    pkg = PACKAGES.get(design.package_id, PACKAGES["pop"])
    cool = COOLING.get(design.cooling_id, COOLING["graphite"])
    ambient = design.ambient_c
    skin_limit = scenario["limits"]["skin_temp"]
    r_total = pkg["rjc"] + cool["rca"]
    p_skin = max(0.3, (skin_limit - ambient) / max(0.2, cool["rca"]))
    p_tj = max(0.5, (105.0 - ambient) / max(0.2, r_total))
    p_sustain = min(p_skin, p_tj)
    p_burst = min((118.0 - ambient) / max(0.2, r_total), max(p_sustain * 3.2, p_sustain + 2.0))
    s_burst, p_burst_actual = _solve_scale(plan, design, p_burst, tuning)
    s_sustain, p_sus_actual = _solve_scale(plan, design, p_sustain, tuning, r_total)
    tj = ambient + p_sus_actual * r_total
    tskin = ambient + p_sus_actual * cool["rca"]
    hot = tj + plan.metrics.get("hotspot_rise", 0.0) * s_sustain
    throttle = 1.0 - s_sustain
    heat_penalty = 0.0
    if hot > 100.0:
        heat_penalty = min(0.18, (hot - 100.0) * 0.0015)
    return dict(
        r_total=r_total, r_ca=cool["rca"], r_jc=pkg["rjc"],
        p_skin=p_skin, p_tj=p_tj, p_sustain=p_sustain, p_burst=p_burst,
        p_burst_actual=p_burst_actual, p_sustain_actual=p_sus_actual,
        scale_burst=s_burst, scale_sustain=s_sustain,
        throttle=throttle, tj=tj, tskin=tskin, hotspot=hot,
        hotspot_rise=plan.metrics.get("hotspot_rise", 0.0),
        heat_penalty=heat_penalty, ambient=ambient, skin_limit=skin_limit,
    )


def _tuning_multipliers(t: float) -> tuple[float, float]:
    """返回 (官方跑分倍率, 真实体验倍率)。t<=0.3 属于合理调优。"""
    t = clamp(t, 0.0, 1.0)
    if t <= TUNING_OFFICIAL:
        k = t / TUNING_OFFICIAL
        return 1.0 + 0.10 * k, 1.0 + 0.03 * k
    k = (t - TUNING_OFFICIAL) / (1.0 - TUNING_OFFICIAL)
    return 1.10 + 0.25 * k, 1.03 - 0.15 * k


def _group_ipc(plan, g, design, scenario) -> float:
    node = NODES[design.node_id]
    l3_per_cluster = design.l3_mb
    l3_factor = 1.0 + 0.06 * log2(max(0.5, l3_per_cluster) / 8.0)
    slc_factor = 1.0 + 0.025 * log2(1.0 + design.slc_mb / 8.0)
    noc = NOCS.get(design.noc, NOCS["ring"])
    noc_factor = max(0.90, 1.0 - 0.02 * (noc["base_hops"] - 1.0))
    wire_factor = max(0.90, 1.0 - 0.004 * plan.metrics.get("avg_wire_mm", 0.0))
    l2f = ppa.l2_ipc_factor(g.ip, g.group.l2_mb, g.group.l2_shared, g.count)
    return max(0.2, g.ipc_base * l2f * l3_factor * slc_factor * noc_factor * wire_factor)


def _bw_factor(plan, design, scale: float, ipcs: list[float]) -> float:
    dram = DRAMS.get(design.dram, DRAMS["lpddr4x"])
    avail = memory_spec(design)["effective_gbs"]
    demand = 0.0
    for g, ipc in zip(plan.groups, ipcs):
        demand += ipc * g.clock * scale * 4.0 * g.count
    if demand <= 1e-6:
        return 1.0
    return clamp((avail / demand) ** 0.25, 0.55, 1.0)


def _perf(plan, design, thermal, scenario):
    node = NODES[design.node_id]
    noc = NOCS.get(design.noc, NOCS["ring"])
    metal = METAL_STACKS.get(design.metal_stack, METAL_STACKS["balanced"])
    cong_penalty = 1.0 - plan.metrics.get("congestion", 0.0) * 0.6
    total_cores = sum(g.count for g in plan.groups)
    dsu_penalty = 1.0
    if design.l3_shared and total_cores > 10:
        # DSU 簇规模：单簇共享 L3 超过 10 核，仲裁与跨核延迟上升
        dsu_penalty = max(0.90, 1.0 - 0.025 * (total_cores - 10))
    ipcs = [_group_ipc(plan, g, design, scenario) for g in plan.groups]
    big_count = sum(g.count for g in plan.groups if g.ip["tier"] == "big")
    big_contention = 1.0 / (1.0 + 0.06 * max(0, big_count - 1))

    def clocks(scale):
        return [g.clock * scale * cong_penalty * dsu_penalty * (1.0 - thermal["heat_penalty"]) for g in plan.groups]

    f_burst = clocks(thermal["scale_burst"])
    f_sus = clocks(thermal["scale_sustain"])
    bw_b = _bw_factor(plan, design, thermal["scale_burst"], ipcs)
    bw_s = _bw_factor(plan, design, thermal["scale_sustain"], ipcs)

    # ST：只开一颗最好的核，用单核功耗预算，不受全核热预算拖累
    best_i = max(range(len(plan.groups)), key=lambda i: ipcs[i] * plan.groups[i].clock)
    best = plan.groups[best_i]
    p_single = ppa.core_power(best.ip, best.clock, best.fmax, best.area_each,
                              NODES[design.node_id], best.impl, 85.0)
    p_single = p_single[0] + p_single[1] + 0.5
    st_scale = 1.0
    if p_single > thermal["p_burst"]:
        st_scale = (thermal["p_burst"] / p_single) ** (1.0 / 1.8)
    st_sus_scale = 1.0
    if p_single > thermal["p_sustain"]:
        st_sus_scale = (thermal["p_sustain"] / p_single) ** (1.0 / 1.8)
    st_burst = (ipcs[best_i] * best.clock * 660.0 * st_scale
                * cong_penalty * dsu_penalty * (1.0 - thermal["heat_penalty"]))
    st_sus = (ipcs[best_i] * best.clock * 660.0 * st_sus_scale
              * cong_penalty * dsu_penalty * (1.0 - thermal["heat_penalty"]))

    def mt(freqs, bw):
        s = 0.0
        for g, ipc, f in zip(plan.groups, ipcs, freqs):
            s += ipc * f * 660.0 * EFF_TYPE.get(g.ip["tier"], 0.8) * g.count
        return 0.68 * s * big_contention * bw

    mt_burst = mt(f_burst, bw_b)
    mt_sus = mt(f_sus, bw_s)

    gpu = get_gpu(design)
    gpu_base = (plan.metrics.get("gpu_units", gpu["default_units"]) * gpu["perf_per_unit"]
                * plan.metrics.get("gpu_freq_ratio", 1.0))
    slc_gpu = 1.0 + 0.035 * log2(1.0 + design.slc_mb / 8.0)
    gpu_burst = gpu_base * (thermal["scale_burst"] ** 0.85) * slc_gpu
    gpu_sus = gpu_base * (thermal["scale_sustain"] ** 0.85) * slc_gpu
    gpu_compat = float(gpu.get("compat", 1.0))

    npu = get_npu(design)
    ai = npu["tops"] * 0.80 * (1.0 + 0.02 * design.slc_mb / 8.0) + gpu_burst * 0.010

    off_mult, real_mult = _tuning_multipliers(design.bench_tuning)
    isa = clamp(design.bench_isa, 0.0, 1.0)
    official_st = st_burst * off_mult * (1.0 + 0.15 * isa)
    official_mt = mt_burst * off_mult * (1.0 + 0.18 * isa)
    real_st = (0.55 * st_burst + 0.45 * st_sus) * real_mult
    real_mt = (0.60 * mt_burst + 0.40 * mt_sus) * real_mult
    official_gpu = gpu_burst * (1.0 + 0.12 * design.bench_tuning)
    gpu_real = (0.60 * gpu_burst + 0.40 * gpu_sus) * gpu_compat

    dram = DRAMS.get(design.dram, DRAMS["lpddr4x"])
    n_cores = sum(g.count for g in plan.groups)
    board = scenario.get("board", "phone")
    base_light = {"laptop": 2.2, "fold": 0.70}.get(board, 0.55)
    display = {"laptop": 3.0, "fold": 0.90}.get(board, 0.35)
    modem_light = 0.0 if design.modem_id=='modem_none' else 0.10 if design.modem_id == "modem5g" else 0.04
    light = (base_light + 0.012 * n_cores + 0.012 * design.l3_mb
             + 0.03 * memory_spec(design)["channels"] + modem_light
             + plan.metrics.get("wire_power", 0.0) * 0.25)
    battery_h = scenario["battery_wh"] / max(0.4, light + display)
    sustain_ratio = mt_sus / max(1.0, mt_burst)

    if getattr(design, "chiplet", False):
        real_st *= 0.98
        real_mt *= 0.98
        official_st *= 0.98
        official_mt *= 0.98
        st_burst *= 0.98
        mt_burst *= 0.98
        st_sus *= 0.98
        mt_sus *= 0.98
        official_gpu *= 0.98
        gpu_real *= 0.98
    return dict(
        st=real_st, mt=real_mt, gpu=official_gpu, gpu_real=gpu_real, ai=ai,
        st_burst=st_burst, mt_burst=mt_burst, st_sustain=st_sus, mt_sustain=mt_sus,
        official_st=official_st, official_mt=official_mt, official_gpu=official_gpu,
        real_st=real_st, real_mt=real_mt,
        battery_h=battery_h, light_power=light, sustain_ratio=sustain_ratio,
        gpu_sustain=gpu_sus, gpu_compat=gpu_compat, ipcs=ipcs,
        bw_burst=bw_b, bw_sustain=bw_s, tuning_official=off_mult, tuning_real=real_mult,
        dsu_penalty=dsu_penalty,
    )


def _eff_curve(plan, design, perf):
    """能效曲线：横轴 package power，纵轴 MT。"""
    ipcs = perf.get("ipcs", [])
    if not ipcs:
        return []
    noc = NOCS.get(design.noc, NOCS["ring"])
    big_count = sum(g.count for g in plan.groups if g.ip["tier"] == "big")
    big_contention = 1.0 / (1.0 + 0.06 * max(0, big_count - 1))
    out = []
    for i in range(11):
        scale = 0.20 + 0.08 * i
        s = scale
        p = _total_power(plan, s, design, design.bench_tuning)
        vals = []
        for g, ipc in zip(plan.groups, ipcs):
            f = g.clock * s
            vals.append(ipc * f * 660.0 * EFF_TYPE.get(g.ip["tier"], 0.8) * g.count)
        mt = 0.68 * sum(vals) * big_contention * noc["latency_factor"]
        st = max((ipc * g.clock * s * 660.0 for g, ipc in zip(plan.groups, ipcs)), default=0)
        out.append(dict(scale=round(s, 3), power=round(p, 3), st=round(st, 1), mt=round(mt, 1)))
    return out


def _eco_score(design) -> tuple[float, list[str]]:
    notes = []
    eco = 1.0
    isas = set()
    for g in design.cores:
        ip = get_ip(design, g.core_id)
        if g.count > 0 and ip:
            isas.add(ip["isa"])
    if "riscv" in isas:
        eco = TRACKS["riscv"]["eco_base"] + TRACKS["riscv"]["eco_gain"] * clamp(design.eco_invest, 0, 1)
        notes.append(TRACKS["riscv"]["eco_note"])
    if "riscv" in isas and any(i.startswith("arm") for i in isas):
        eco -= 0.10
        notes.append(TRACKS["riscv"]["mix_note"])
    return clamp(eco, 0.5, 1.0), notes


def _market(result, design, scenario, yld, cost, nre, perf, thermal):
    targets = scenario["targets"]
    limits = scenario["limits"]
    weights = scenario["weights"]
    eco, eco_notes = _eco_score(design)
    q_st = clamp(perf["real_st"] / targets["st"], 0, 1.35)
    q_mt = clamp(perf["real_mt"] / targets["mt"], 0, 1.35)
    q_gpu = clamp(perf.get("gpu_real", perf["gpu"]) / targets["gpu"], 0, 1.35)
    q_ai = clamp(perf["ai"] / targets["ai"], 0, 1.35)
    q_bat = clamp(perf["battery_h"] / targets["battery_h"], 0, 1.35)
    q_sus = clamp(perf["sustain_ratio"] / 0.80, 0, 1.35)
    q_eff = 0.6 * q_bat + 0.4 * q_sus
    quality = (weights["st"] * q_st + weights["mt"] * q_mt + weights["gpu"] * q_gpu
               + weights["eff"] * q_eff + weights["ai"] * q_ai)

    value = clamp(scenario["ref_price"] / max(1.0, design.price), 0.50, 1.30)
    thermal_ok = clamp(1.0 - max(0.0, thermal["tskin"] - limits["skin_temp"]) / 10.0, 0, 1)
    review = 20.0 + 24.0 * min(quality, 1.25) + 28.0 * min(value, 1.20) + 10.0 * thermal_ok + 10.0 * eco + 8.0 * min(perf["sustain_ratio"] / 0.8, 1.0)
    review = clamp(review, 0, 100)
    storage = STORAGE.get(getattr(design, "storage_id", "ufs31"), STORAGE["ufs31"])
    modem = FIXED_BLOCKS.get(design.modem_id, FIXED_BLOCKS["modem5g"])
    fluency_bonus = (storage.get("fluency", 0.97) - 0.97) * 40.0
    signal_bonus = (modem.get("signal", 1.0) - 0.97) * 100.0
    review = clamp(review + fluency_bonus + signal_bonus, 0, 100)

    rng = mulberry32(design.seed + 17)
    caught = False
    p_caught = max(0.0, (design.bench_tuning - 0.50) / 0.50) * 0.85
    p_caught = max(p_caught, getattr(design, "bench_isa", 0.0) * 0.35)
    if rng() < p_caught:
        caught = True
        review = max(0.0, review - 22.0)

    # 首发稳定性：新节点 + 激进频率 + 强调优 = 黑屏/死机翻车风险
    node = NODES[design.node_id]
    immaturity = 1.0 - node["maturity"]
    aggr = 0.0
    n_cores = 0
    for g in result["plan"].groups:
        a = clamp((g.clock - g.fmax * 0.95) / max(0.05, 0.15 * g.fmax), 0, 1)
        aggr += a * g.count
        n_cores += g.count
    aggr = aggr / max(1, n_cores)
    tuning_push = clamp(design.bench_tuning, 0, 1) * 0.3 + clamp(getattr(design, "bench_isa", 0.0), 0, 1) * 0.3
    plan = result["plan"]
    pike = _total_power(plan, 1.0, design, design.bench_tuning)
    supply_weak = 1.0 if design.package_id == "pop" else 0.4
    ir_push = clamp((pike - 8.0) / 12.0, 0, 1) * 0.30 * supply_weak
    pdn_push = clamp((result["engineering"]["ir_drop_v"] - 0.06) / 0.12, 0, 1) * 0.15
    p_crash = clamp(0.02 + immaturity * 1.2 + aggr * 0.25 + tuning_push * 0.20 + ir_push + pdn_push - 0.05, 0, 0.60)
    p_crash *= 1.0 - 0.4 * (clamp(design.verification_effort, 0, 1) - 0.60)
    rng2 = mulberry32(design.seed + 31)
    crashed = bool(p_crash > 0.08 and rng2() < p_crash)
    rng3 = mulberry32(design.seed + 77)
    retail_gap = 0.03 * rng3() + clamp(design.bench_tuning, 0, 1) * 0.06 \
        + clamp(getattr(design, "bench_isa", 0.0), 0, 1) * 0.04
    retail_factor = clamp(1.0 - retail_gap, 0.85, 1.0)
    retail_st = perf["official_st"] * retail_factor
    retail_mt = perf["official_mt"] * retail_factor
    review = clamp(review - (1.0 - retail_factor) * 100.0 * 0.3, 0, 100)
    if crashed:
        review = max(0.0, review - 15.0)

    # 代际提升有限：官方分相对上代主流提升不足
    stagnant = False
    prev = scenario.get("prev")
    if prev:
        imp = max(perf["official_st"] / max(1.0, prev["st"]) - 1.0,
                  perf["official_mt"] / max(1.0, prev["mt"]) - 1.0)
        if imp < 0.08:
            stagnant = True
            review = max(0.0, review - 8.0)

    # 应力折损：高温高负载，一年后持续性能衰减
    heat_stress = clamp((thermal["hotspot"] - 70.0) / 60.0, 0, 1) * 0.6 \
        + clamp(thermal["throttle"], 0, 1) * 0.4
    aged_ratio = 1.0 - 0.25 * heat_stress
    aged_mt = perf["mt_sustain"] * aged_ratio
    aging_risk = (1.0 - aged_ratio) > 0.10
    if aging_risk:
        review = max(0.0, review - 5.0)

    brand = 0.85 + 0.30 * clamp(design.reputation, 0.0, 1.0)
    demand_mult = (scenario["ref_price"] / max(1.0, design.price)) ** 1.8
    demand_mult *= (max(review, 1.0) / 75.0) ** 1.6
    demand_mult *= brand
    # 可服务市场有限，低价不能产生无限销量。
    units = scenario["base_units_m"] * min(3.0, demand_mult)
    revenue = units * design.price
    gross = units * (design.price - cost["total"])
    profit = gross - nre["total"]

    met = 0
    checks = [
        perf["st_burst"] >= targets["st"],
        perf["mt_burst"] >= targets["mt"],
        perf["gpu"] >= targets["gpu"],
        perf["ai"] >= targets["ai"],
        perf["battery_h"] >= targets["battery_h"],
        thermal["tskin"] <= limits["skin_temp"],
        cost["total"] <= limits["max_cost"],
    ]
    met = sum(1 for c in checks if c)
    budget = scenario["budget_m"]
    if profit >= 3.0 * budget and review >= 90 and met >= 6:
        grade = "S"
    elif profit >= 1.5 * budget and review >= 82 and met >= 4:
        grade = "A"
    elif profit > 0 and met >= 2:
        grade = "B"
    else:
        grade = "C"

    return dict(
        quality=quality, review=review, value=value, eco=eco, eco_notes=eco_notes,
        q_st=q_st, q_mt=q_mt, q_gpu=q_gpu, q_ai=q_ai, q_eff=q_eff,
        q_bat=q_bat, q_sus=q_sus, thermal_ok=thermal_ok,
        units=units, revenue=revenue, gross=gross, profit=profit, brand=brand,
        margin=(design.price - cost["total"]) / max(1.0, design.price),
        targets_met=met, targets_total=len(checks), grade=grade,
        caught=caught, p_caught=p_caught,
        crashed=crashed, p_crash=p_crash, ir_push=ir_push,
        retail_st=retail_st, retail_mt=retail_mt, retail_factor=retail_factor,
        stagnant=stagnant, prev=prev,
        aging_risk=aging_risk, aged_mt=aged_mt, aged_ratio=aged_ratio,
    )


def simulate(design, force_layout: bool = False) -> dict:
    scenario = SEGMENTS.get(design.scenario_id, SEGMENTS["mid2019"])
    plan = build_plan(design, force_layout=force_layout)
    errors = list(plan.errors)
    warnings = list(plan.warnings)

    # 授权 / 指令集检查
    allowed = set(scenario.get("allowed_licenses", ["arm", "riscv"]))
    if design.node_id not in scenario.get("allowed_nodes", []):
        errors.append(f"{NODES[design.node_id]['name']} 不在本关可用制程范围。")
    isas = set()
    for g in design.cores:
        if g.count <= 0:
            continue
        ip = get_ip(design, g.core_id)
        if not ip:
            errors.append(f'核心 {g.core_id} 无有效IP定义。')
            continue
        if ip["license"] == "research" and "research" not in allowed:
            errors.append(f"{ip['name']} 是研究档案，现实中不可授权。沙盒“研究沙盒”可用。")
        if ip["license"] == "riscv" and "riscv" not in allowed:
            errors.append(f"{ip['name']} 的 RISC-V 授权不在本关可用范围。")
        if ip["license"] == "custom" and "custom" not in allowed:
            errors.append("自研核只在研究沙盒可用。")
        if scenario["id"] != "sandbox" and ip["year"] > scenario["year"]:
            errors.append(f"{ip['name']}（{ip['year']}）晚于本关年份 {scenario['year']}，不可用。")
        isas.add(ip["isa"])
    if "riscv" in isas and any(i.startswith("arm") for i in isas):
        errors.append("本作不支持 ARM 与 RISC-V 混用为同一操作系统的应用核心；真实 SoC 可另设异构控制核。")
    families={'arm' if i.startswith('arm') else i for i in isas}
    if len(families)>1 and any(i.startswith('x86') for i in families):
        errors.append('应用CPU集群不能混用x86与其他ISA；异构控制器尚未建模。')
    if not plan.groups:
        errors.append("至少需要一个 CPU 核心组。")
    gpu = get_gpu(design)
    if gpu.get("license_cost_m") is None and "research" not in allowed:
        errors.append(f"{gpu['name']} 是研究 GPU，不能作为通用授权 IP 采购；可在研究沙盒使用。")
    if scenario["id"] != "sandbox" and gpu["year"] > scenario["year"]:
        errors.append(f"{gpu['name']} 晚于本关设定年份，不在当期可用 IP 范围。")
    if scenario["id"] != "sandbox" and scenario.get("board") in ("phone", "fold") and design.cooling_id in ("laptop", "server"):
        errors.append("所选笔记本或服务器散热方案不符合手机机身约束。")
    if getattr(design, "chiplet", False) and design.package_id != "imc25d":
        errors.append("本作的 Chiplet 方案需要 2.5D 封装；现实也有有机基板与 3D 互连方案。")
    if plan.die_area > scenario["limits"]["max_die_area"]:
        errors.append(f"die 面积 {plan.die_area:.0f}mm² 超过本关上限 {scenario['limits']['max_die_area']}mm²。")
    lim = scenario["limits"]
    if plan.die_w > lim.get("max_die_w", 99) or plan.die_h > lim.get("max_die_h", 99):
        errors.append(f"die 尺寸 {plan.die_w:.1f}×{plan.die_h:.1f}mm 超过设备可接受上限 "
                      f"{lim.get('max_die_w',99)}×{lim.get('max_die_h',99)}mm。")
    pkg = PACKAGES.get(design.package_id, PACKAGES["pop"])
    if plan.die_area > pkg["max_area"]:
        errors.append(f"{pkg['name']} 最大支持 {pkg['max_area']}mm²。")
    if plan.die_w > pkg.get("max_w", 99) or plan.die_h > pkg.get("max_h", 99):
        errors.append(f"{pkg['name']} 最大支持 {pkg.get('max_w')}×{pkg.get('max_h')}mm 的 die。")

    if not plan.groups:
        thermal = dict(scale_burst=1, scale_sustain=1, throttle=0, tj=25, tskin=25,
                       hotspot=25, p_sustain=0, p_burst=0, p_burst_actual=0,
                       p_sustain_actual=0, heat_penalty=0, r_total=0, r_ca=0, r_jc=0,
                       hotspot_rise=0, ambient=design.ambient_c,
                       skin_limit=scenario["limits"]["skin_temp"])
        perf = dict(st=0, mt=0, gpu=0, gpu_real=0, ai=0, st_burst=0, mt_burst=0, st_sustain=0,
                    mt_sustain=0, official_st=0, official_mt=0, official_gpu=0,
                    real_st=0, real_mt=0, battery_h=0, light_power=1, sustain_ratio=0,
                    gpu_sustain=0, ipcs=[], bw_burst=0, bw_sustain=0,
                    tuning_official=1, tuning_real=1)
    else:
        thermal = _thermal(plan, design, scenario, design.bench_tuning)
        perf = _perf(plan, design, thermal, scenario)
        perf["curve"] = _eff_curve(plan, design, perf)

    nre = economics.nre_breakdown(design, plan, scenario)
    budget = economics.check_budget(nre, scenario)
    binfrac, bin_details = economics.bin_fraction(design, plan)
    yld = economics.die_yield(design, plan, binfrac)
    cost = economics.unit_cost(design, plan, yld, scenario)
    engineering = engineering_report(design, plan, perf, thermal)
    market = _market(dict(plan=plan, engineering=engineering), design, scenario, yld, cost, nre, perf, thermal)
    m_crash_warn = {"p": market["p_crash"]}
    m_stag = {"stagnant": market["stagnant"],
              "prev_name": (market["prev"] or {}).get("name", "上代")}
    m_age = {"aging": market["aging_risk"], "ratio": market["aged_ratio"]}

    # 建议
    if budget["over"]:
        warnings.append(f"NRE {nre['total']:.0f}M 超出预算 {scenario['budget_m']}M；流片会被拒绝。")
    if cost["total"] > scenario["limits"]["max_cost"]:
        warnings.append(f"单颗成本 ${cost['total']:.0f} 高于本关上限 ${scenario['limits']['max_cost']}。")
    if thermal["tskin"] > scenario["limits"]["skin_temp"]:
        warnings.append(f"机身温度 {thermal['tskin']:.1f}°C 超过舒适上限 {scenario['limits']['skin_temp']}°C。")
    if thermal["p_burst_actual"] > scenario["limits"]["max_tdp"]:
        warnings.append(f"峰值功耗 {thermal['p_burst_actual']:.1f}W 超过本关上限 {scenario['limits']['max_tdp']}W。")
    if thermal["hotspot"] > 100:
        warnings.append(f"局部热点 {thermal['hotspot']:.0f}°C，建议把大核与 GPU 分开。")
    if plan.metrics.get("congestion", 0) > 0.09:
        warnings.append("布线拥塞偏高：尝试更均衡的布局或 mesh NoC。")
    if perf.get("dsu_penalty", 1.0) < 0.999:
        nc = sum(g.count for g in plan.groups)
        warnings.append(f"共享 L3 连接 {nc} 核，超过本作十核阈值；可拆簇。真实支持规模需查具体互连 IP。")
    if getattr(design, "storage_id", "ufs31") == "ufs22" and scenario.get("year", 2019) >= 2022:
        warnings.append("UFS 2.2 配旗舰 SoC：存储会拖累应用体验与口碑（存储带宽限制）。")
    if design.modem_id == "modem4g" and scenario.get("year", 2019) >= 2020:
        warnings.append("4G 基带出现在 5G 时代：评测与销量都会受影响。")
    if NODES[design.node_id]["maturity"] < 0.85:
        warnings.append(f"{NODES[design.node_id]['name']} 成熟度低：良率爬坡慢，首发稳定性风险高（教学成熟度假设）。")
    if market.get("ir_push", 0) > 0.12:
        warnings.append("峰值负载提高了供电压力：到工程验证页检查压降，或降低频率。")
    if scenario.get("board") == "fold" and thermal["p_burst_actual"] > 10.0:
        warnings.append("峰值超过 10W：本关折叠设备的持续热预算较低，应同时查看持续功耗与结温。")
    if perf.get("sustain_ratio", 1.0) < 0.60:
        warnings.append(f"持续多核性能为峰值的 {perf['sustain_ratio']*100:.0f}%；检查散热与功耗预算，再用具体负载评估体验。")
    if market.get("retail_factor", 1.0) < 0.93:
        warnings.append("零售机复测明显低于工程机：特挑、散热与调度差异，工程机成绩别全信。")
    if plan.metrics.get("utilization", 0) < 0.62:
        warnings.append("die 利用率偏低：空白面积也是成本。")
    if design.bench_tuning > 0.5:
        warnings.append("调度/提频优化过强：媒体实测可能识破，真实体验会下降。")
    if getattr(design, "bench_isa", 0.0) > 0.3:
        warnings.append("跑分 ISA 扩展偏多：常规应用无收益，且更容易被媒体质疑。")
    if m_crash_warn["p"] > 0.25:
        warnings.append(f"首发稳定性风险高（{m_crash_warn['p']*100:.0f}%）：新节点 + 激进频率是功能异常的经典配方。")
    if m_stag["stagnant"]:
        warnings.append(f"相对上代（{m_stag['prev_name']}）提升不足 8%，媒体可能评价为“代际提升有限”。")
    if m_age["aging"]:
        warnings.append(f"教学热应力情景下性能系数为 {m_age['ratio']*100:.0f}%；这不是实际寿命或一年后性能预测。")
    if design.slc_mb == 0 and any(g.count >= 4 and g.ip["tier"] == "big" for g in plan.groups):
        warnings.append("多性能核配置需要检查共享缓存与带宽。SLC 可供多个客户端使用，但不是所有架构的必需模块。")
    big_count = sum(g.count for g in plan.groups if g.ip["tier"] == "big")
    if big_count >= 4:
        warnings.append("4 颗以上大核会显著拉高功率密度，持续性能未必线性增长。")
    for g in plan.groups:
        if g.clock > g.fmax * 1.02:
            warnings.append(f"{g.ip['name']} 目标 {g.clock:.2f}GHz 高于均值 {g.fmax:.2f}GHz，良率按 bin 折损。")

    # 尖峰频率与良率
    valid = not errors
    result = dict(
        valid=valid, errors=errors, warnings=warnings,
        scenario=scenario, node=NODES[design.node_id], plan=plan,
        groups=[dict(ip=g.ip, clock=g.clock, fmax=g.fmax, count=g.count,
                     power=g.power_each, area=g.area_each, ipc=ipc,
                     l2=g.group.l2_mb, l2_shared=g.group.l2_shared)
                for g, ipc in zip(plan.groups, perf.get("ipcs", [1.0] * len(plan.groups)))],
        metrics=plan.metrics, thermal=thermal, power=dict(
            peak=thermal["p_burst_actual"], sustain=thermal["p_sustain_actual"],
            budget_sustain=thermal["p_sustain"]),
        perf=perf, nre=nre, budget=budget, yield_=yld,
        bin=dict(fraction=binfrac, details=bin_details), cost=cost,
        market=market, die_area=plan.die_area, engineering=engineering,
    )
    result["warnings"].extend(engineering["notes"])
    result["signoff"] = signoff_report(result)
    from .challenges import challenge_report
    challenge=challenge_report(design,result)
    result['challenge']=challenge
    if challenge:
        check=dict(id='challenge',ok=challenge['ready'],title='项目委托验收',remedy='返回项目简报查看未满足的关卡目标。')
        result['signoff']['checks'].append(check)
        if not check['ok']:result['signoff']['blockers'].append(check);result['signoff']['ready']=False
    return result


# 便于 UI 快速取用
def quick_scores(design) -> dict:
    r = simulate(design)
    return dict(st=r["perf"]["st_burst"], mt=r["perf"]["mt_burst"],
                gpu=r["perf"]["gpu"], area=r["die_area"],
                cost=r["cost"]["total"], power=r["power"]["peak"],
                valid=r["valid"], warnings=len(r["warnings"]))
