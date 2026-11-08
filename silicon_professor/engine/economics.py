"""NRE、良率、binning、单颗成本。"""
from __future__ import annotations

import math

from ..data.blocks import (COOLING, DRAMS, FIXED_BLOCKS, GPUS, METAL_STACKS, NPUS, PACKAGES, STORAGE)
from ..data.blocks import get_gpu, get_npu, get_isp
from ..data.cores import CORES, get_ip
from ..data.nodes import NODES
from . import ppa
from .rng import normal_cdf
from .wafer import wafer_sites
from .memory import memory_spec


def nre_breakdown(design, plan, scenario) -> dict:
    node = NODES[design.node_id]
    metal = METAL_STACKS.get(design.metal_stack, METAL_STACKS["balanced"])
    gpu = get_gpu(design)
    npu = get_npu(design)

    core_ids = []
    custom_groups = 0
    eng_weeks = 4.0
    for g in design.cores:
        if g.count <= 0:
            continue
        ip = get_ip(design, g.core_id)
        if not ip:
            continue
        if g.core_id not in core_ids:
            core_ids.append(g.core_id)
            eng_weeks += ip["eng_weeks"]
        if (g.impl.lib != "sd" or g.impl.vt != "svt" or abs(g.impl.density - 0.35) > 0.02
                or abs(g.impl.timing - 0.35) > 0.02 or abs(g.impl.aspect - 1.0) > 0.01):
            custom_groups += 1
            eng_weeks += 4.0

    license_core = sum(((get_ip(design, cid) or {}).get("license_cost_m") or 0.0) for cid in core_ids)
    license_gpu = gpu.get("license_cost_m") or 0.0
    license_npu = npu.get("license_cost_m") or 0.0
    fixed_license = 0.0
    if design.isp:
        fixed_license += get_isp(design)["license_cost_m"]
    modem = FIXED_BLOCKS.get(design.modem_id, FIXED_BLOCKS["modem5g"])
    fixed_license += modem["license_cost_m"]
    if design.media:
        fixed_license += FIXED_BLOCKS["media"]["license_cost_m"]
    if design.display:
        fixed_license += FIXED_BLOCKS["display"]["license_cost_m"]
    fixed_license += FIXED_BLOCKS["dramphy"]["license_cost_m"]
    fixed_license += FIXED_BLOCKS["io"]["license_cost_m"]

    mask = float(node["mask_cost"])
    eda = 6.0 + 0.3 * mask
    eng = eng_weeks * 0.12
    custom = custom_groups * 2.2
    custom += 30.0 * sum((get_ip(design,cid) or {}).get('license')=='custom' for cid in core_ids)
    metal_cost = metal["cost_m"]
    eco = design.eco_invest * 12.0
    verification = 2.0 + 5.0 * design.verification_effort + 4.0 * getattr(design, "bench_isa", 0.0)
    eng += 2.0 * design.pdn_quality
    total = mask + license_core + license_gpu + license_npu + fixed_license + eda + eng + custom + metal_cost + eco + verification

    return dict(
        mask=mask, license_core=license_core, license_gpu=license_gpu,
        license_npu=license_npu, license_fixed=fixed_license, eda=eda,
        engineering=eng, custom=custom, metal=metal_cost, eco=eco,
        verification=verification, total=total, eng_weeks=eng_weeks,
        custom_groups=custom_groups, n_core_types=len(core_ids),
    )


def _one_die(node, area: float, bin_fraction: float, width=None, height=None) -> dict:
    area = max(1.0, area)
    a_cm2 = area / 100.0
    d0 = node["d0"]
    murphy = ((1.0 - math.exp(-a_cm2 * d0)) / (a_cm2 * d0)) ** 2 if a_cm2 * d0 > 1e-9 else 1.0
    y = max(0.01, min(0.995, murphy * node["maturity"]))
    dpw = len(wafer_sites(width or math.sqrt(area), height or math.sqrt(area)))
    good = max(1e-6, dpw * y * max(1e-4, bin_fraction))
    return dict(area=area, yield_pct=y, dies_per_wafer=dpw, good_dies=good,
                die_cost=node["wafer_cost"] / good, murphy=murphy, area_cm2=a_cm2)


def die_yield(design, plan, bin_fraction: float = 1.0) -> dict:
    node = NODES[design.node_id]
    if getattr(design, "chiplet", False):
        # 把 GPU/NPU/IO 侧切到第二颗 die；逻辑布局仍是一张图
        accel = sum(b.area for b in plan.blocks
                    if b.kind in ("gpu", "npu", "isp", "media", "display", "dramphy", "io"))
        share = max(0.18, min(0.62, accel / max(1.0, plan.used_area)))
        a1 = plan.die_area * (1.0 - share)
        a2 = plan.die_area * share
        d1 = _one_die(node, a1, bin_fraction)
        d2 = _one_die(node, a2, 1.0)  # CPU 分档只约束 CPU die
        total_good = 1.0 / (1.0 / d1["good_dies"] + 1.0 / d2["good_dies"])
        y = (d1["yield_pct"] * a1 + d2["yield_pct"] * a2) / max(1.0, plan.die_area)
        return dict(
            yield_pct=y, dies_per_wafer=d1["dies_per_wafer"], good_dies=total_good,
            die_cost=d1["die_cost"] + d2["die_cost"],
            murphy=(d1["murphy"] + d2["murphy"]) / 2, d0=node["d0"],
            area_cm2=plan.die_area / 100.0, chiplet=True,
            die_areas=[a1, a2], die_costs=[d1["die_cost"], d2["die_cost"]],
        )
    d = _one_die(node, plan.die_area, bin_fraction, plan.die_w, plan.die_h)
    d.update(chiplet=False)
    return d


def bin_fraction(design, plan) -> tuple[float, list[dict]]:
    details = []
    overall = 1.0
    for g in plan.groups:
        fmax = g.fmax
        target = g.group.clock or g.clock
        sigma = max(0.01, 0.045 * fmax)
        frac = normal_cdf((fmax - target) / sigma)
        frac = max(1e-4, min(1.0, frac))
        overall = min(overall, frac)
        details.append(dict(core=g.ip["name"], fmax=fmax, target=target, fraction=frac))
    return overall, details


def unit_cost(design, plan, yld: dict, scenario) -> dict:
    package = PACKAGES.get(design.package_id, PACKAGES["pop"])
    test = 0.30 + plan.die_area * 0.0035
    assembly = 0.25
    die = yld["die_cost"]
    modem = FIXED_BLOCKS.get(design.modem_id, FIXED_BLOCKS["modem5g"])
    external_bom = modem.get("bom_cost", 0.0)
    chiplet_asm = 8.0 if getattr(design, "chiplet", False) else 0.0
    storage = STORAGE.get(getattr(design, "storage_id", "ufs31"), STORAGE["ufs31"])
    storage_cost = storage.get("cost", 4.0)
    total = die + package["cost"] + test + assembly + external_bom + chiplet_asm
    dram = DRAMS[design.dram]
    dram_cost = memory_spec(design)["channels"] * dram["cost_per_channel"] * max(1, design.memory_gb) / 8.0
    cooling_cost = COOLING[design.cooling_id]["cost"]
    return dict(die=die, package=package["cost"], test=test,
                assembly=assembly, external_bom=external_bom,
                chiplet_assembly=chiplet_asm, storage=storage_cost, dram=dram_cost,
                cooling=cooling_cost, platform_total=total + storage_cost + dram_cost + cooling_cost,
                total=total)


def check_budget(nre: dict, scenario) -> dict:
    total = nre["total"]
    return dict(total=total, budget=scenario["budget_m"],
                remaining=scenario["budget_m"] - total,
                over=total > scenario["budget_m"])
