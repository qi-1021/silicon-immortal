"""PPA：面积、频率、电压、功耗。所有公式集中在这里，便于校验。"""
from __future__ import annotations

import math

from ..data.nodes import NODES

LIBS = {
    "hd": dict(name="高密度 HD", area=0.92, freq=0.94, power=0.95, leak=0.95),
    "sd": dict(name="标准 SD", area=1.00, freq=1.00, power=1.00, leak=1.00),
    "hp": dict(name="高性能 HP", area=1.12, freq=1.08, power=1.06, leak=1.25),
}
VTS = {
    "ulvt": dict(name="ULVT", freq=1.06, power=1.10, leak=1.40),
    "lvt": dict(name="LVT", freq=1.03, power=1.05, leak=1.15),
    "svt": dict(name="SVT", freq=1.00, power=1.00, leak=1.00),
    "hvt": dict(name="HVT", freq=0.95, power=0.96, leak=0.70),
}


def node_of(design):
    return NODES[design.node_id]


def ref_node(ip):
    return ip['_reference_node'] if '_reference_node' in ip else NODES[ip["ref_node"]]


def scale_ratio(node, ip) -> float:
    return node["area_scale"] / ref_node(ip)["area_scale"]


def impl_area_factor(impl) -> float:
    lib = LIBS.get(impl.lib, LIBS["sd"])
    base = lib["area"] * (1.0 - 0.18 * impl.density + 0.10 * impl.timing)
    aspect_penalty = 1.0 + 0.02 * (max(impl.aspect, 1.0) - 1.0)
    return max(0.62, base * aspect_penalty)


def impl_freq_factor(impl) -> float:
    lib = LIBS.get(impl.lib, LIBS["sd"])
    vt = VTS.get(impl.vt, VTS["svt"])
    base = lib["freq"] * vt["freq"] * (1.0 - 0.10 * impl.density + 0.12 * impl.timing)
    aspect_penalty = 1.0 - 0.01 * (max(impl.aspect, 1.0) - 1.0)
    return max(0.55, base * aspect_penalty)


def impl_power_factor(impl) -> float:
    lib = LIBS.get(impl.lib, LIBS["sd"])
    vt = VTS.get(impl.vt, VTS["svt"])
    return max(0.5, lib["power"] * vt["power"] * (1.0 + 0.08 * impl.timing - 0.05 * impl.density))


def impl_leak_factor(impl) -> float:
    lib = LIBS.get(impl.lib, LIBS["sd"])
    vt = VTS.get(impl.vt, VTS["svt"])
    return lib["leak"] * vt["leak"] * (1.0 + 0.20 * impl.density)


def core_fmax(ip, impl, node) -> float:
    base = ip["fmax_ref"] * (node["freq_scale"] / ref_node(ip)["freq_scale"])
    l2_penalty = (ip["l2_default"] / max(ip["l2_default"], 0.25)) ** 0.0
    return base * impl_freq_factor(impl) * l2_penalty


def core_area(ip, impl, node, l2_mb: float, shared: bool, count: int) -> float:
    ratio = scale_ratio(node, ip)
    logic = ip["logic_area"] * ratio * impl_area_factor(impl)
    # sram_mb 已经是目标节点的 mm²/MB，不能再次乘逻辑缩放比。
    l2_area = l2_mb * node["sram_mb"]
    if shared:
        l2_area *= 0.80 + 0.04 * count
    return max(0.15, logic + l2_area)


def vdd_for(f_norm: float) -> float:
    f_norm = max(0.35, min(1.10, f_norm))
    return 0.55 + 0.37 * (f_norm ** 1.6)


def core_power(ip, f_ghz, fmax, area, node, impl, temp_c=85.0, dynamic_only=False):
    """返回 (dynamic, leakage)。功耗随频率、电压、温度和节点缩放。"""
    fmax = max(0.4, fmax)
    f_norm = max(0.25, min(1.12, f_ghz / fmax))
    vdd = vdd_for(f_norm)
    pwr = ip["power_ref"]
    leak_frac = ip["leak_frac"]
    node_power = (node["area_scale"] / ref_node(ip)["area_scale"]) ** 0.85

    dyn = pwr * (1.0 - leak_frac) * f_norm * (vdd / 0.90) ** 2 * node_power
    dyn *= impl_power_factor(impl)

    ref_area = max(0.2, ip["logic_area"] + ip["l2_default"] * ref_node(ip)["sram_mb"])
    area_ratio = area / ref_area
    leak = (pwr * leak_frac * 0.55 * area_ratio * (vdd / 0.90)
            * node["leak_scale"] * impl_leak_factor(impl)
            * (2.0 ** ((temp_c - 25.0) / 75.0)))
    if dynamic_only:
        leak = 0.0
    return dyn, leak


def l2_ipc_factor(ip, l2_mb: float, shared: bool, count: int) -> float:
    per_core = l2_mb if not shared else l2_mb / max(1, count)
    ref = max(0.128, ip["l2_default"])
    gain = 0.10 if not shared else 0.08
    f = 1.0 + gain * math.log2(max(per_core, 0.0625) / ref)
    if shared:
        f += 0.035 * math.log2(max(1, count)) - 0.02  # 共享收益 vs 交叉开关延迟
    return max(0.80, f)
