"""教学用工程检查与 Amdahl / Roofline 分析，无网表和 SPICE 输入。"""
from __future__ import annotations

from .memory import memory_spec
from .ppa import vdd_for
from .rng import clamp

PVT_CORNERS = {
    "tt": dict(name="TT · 标称", freq=1.0, temp=25, voltage=1.0),
    "ss": dict(name="SS · 低压 / 高温", freq=0.88, temp=105, voltage=0.92),
    "ff": dict(name="FF · 高压 / 低温", freq=1.06, temp=0, voltage=1.05),
}


def engineering_report(design, plan, perf, thermal):
    mem = memory_spec(design)
    effort = clamp(design.verification_effort, 0, 1)
    # 规划完成度代理值，不是代码覆盖率或 silicon 可靠性概率。
    completion = 0.55 + 0.40 * effort
    corners = []
    for key, c in PVT_CORNERS.items():
        ratios = [(g.group.clock or g.clock) / max(0.01, g.fmax * c["freq"])
                  for g in plan.groups]
        ratio = max(ratios, default=0.0)
        corners.append(dict(id=key, **c, timing_margin=1.0 - ratio,
                            bin_supported=ratio <= 1.10))
    selected = next((c for c in corners if c["id"] == design.pvt_corner), corners[0])
    vdd = max((vdd_for(g.clock / g.fmax) for g in plan.groups), default=0.9)
    current = thermal["p_burst_actual"] / max(0.4, vdd)
    resistance = (0.014 - 0.010 * clamp(design.pdn_quality, 0, 1))
    resistance *= {"pop": 1.2, "fowlp": 1.0, "imc25d": 0.75}.get(design.package_id, 1.0)
    droop = current * resistance

    # 异构核以最快核归一；得到有效并行算力，而不是直接数核。
    rates = [ipc * g.clock for g, ipc in zip(plan.groups, perf.get("ipcs", []))]
    best = max(rates, default=1.0)
    effective_cores = max(1.0, sum(rate * g.count for rate, g in zip(rates, plan.groups)) / best)
    parallel = clamp(design.workload_parallel, 0, 0.999)
    speedup = 1.0 / ((1.0 - parallel) + parallel / effective_cores)
    compute = best * thermal["scale_sustain"] * speedup
    # 抽象运算单位与 GB/s 对应；只用于比较同一工作负载的方案。
    intensity = max(0.1, design.workload_intensity)
    roof = mem["effective_gbs"] * intensity
    achievable = min(compute, roof)
    cache_mb = max(0.0, design.l3_mb) + max(0.0, design.slc_mb)
    cache_fit = min(1.0, cache_mb / max(0.1, design.workload_set_mb))
    # 不假设命中率由容量唯一决定；显示容量比与访存瓶颈，留出模型边界。
    notes = []
    if completion < 0.75:
        notes.append("验证规划不足：增加验证投入，补齐复位、跨时钟域、缓存一致性和 DFT 测试计划。")
    if droop > 0.08:
        notes.append("供电压降超过 80mV 教学门槛：提高电源网络投入，降低峰值频率或改用更低电阻封装。")
    if not selected["bin_supported"]:
        notes.append("所选 PVT 角落无法支撑目标档位：降低目标频率或调整标准单元库与时序投入。")
    return dict(memory=mem, verification_completion=completion, corners=corners,
                selected_corner=selected, current_a=current, pdn_resistance_ohm=resistance,
                ir_drop_v=droop, notes=notes, workload=dict(
                    effective_cores=effective_cores, amdahl_speedup=speedup,
                    compute_ceiling=compute, memory_ceiling=roof, achievable=achievable,
                    bottleneck="内存带宽" if roof < compute else "计算 / 串行部分",
                    shared_cache_mb=cache_mb, working_set_mb=design.workload_set_mb,
                    cache_capacity_ratio=cache_fit))


def signoff_report(result):
    lim = result["scenario"]["limits"]
    eng = result["engineering"]
    checks = [
        ("structure", not result["errors"], "布局、面积与 IP 使用范围", "修复布局或返回架构调整配置。"),
        ("budget", not result["budget"]["over"], "研发预算", "减少定制 IP 或实现投入。"),
        ("cost", result["cost"]["total"] <= lim["max_cost"], "芯片方案成本", "减小面积、降低频率档位或简化封装。"),
        ("skin", result["thermal"]["tskin"] <= lim["skin_temp"] + 0.01, "机身温度", "降低功耗或提高散热能力。"),
        ("power", result["power"]["peak"] <= lim["max_tdp"], "峰值功耗", "降低 CPU 频率或 GPU 规模。"),
        ("verification", eng["verification_completion"] >= 0.75, "验证规划 ≥ 75%", "在工程验证页增加投入。"),
        ("pdn", eng["ir_drop_v"] <= 0.08, "供电压降 ≤ 80mV", "提高电源网络投入或降低峰值功耗。"),
        ("corner", eng["selected_corner"]["bin_supported"], "所选 PVT 档位", "降低目标频率，或调整库和时序投入。"),
        ("bin", result["bin"]["fraction"] >= 0.10, "频率档位可用率 ≥ 10%", "降低目标频率以提高可出售比例。"),
    ]
    rows = [dict(id=key, ok=ok, title=title, remedy=remedy) for key, ok, title, remedy in checks]
    return dict(ready=all(c["ok"] for c in rows), checks=rows,
                blockers=[c for c in rows if not c["ok"]])
