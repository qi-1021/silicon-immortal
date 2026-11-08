"""实验室的离散互连与解析时序/功耗实验。参数单位与边界均显式。"""
from __future__ import annotations

import math


def route(src, dst, count, topology):
    if not 0 <= src < count or not 0 <= dst < count:
        raise ValueError("端点越界。")
    if topology not in ("ring", "mesh"):
        raise ValueError("拓扑应为 ring 或 mesh。")
    if src == dst:
        return [src]
    if topology == "ring":
        clockwise = (dst - src) % count
        direction = 1 if clockwise <= count - clockwise else -1
        return [(src + direction * i) % count for i in range(min(clockwise, count - clockwise) + 1)]
    width = math.isqrt(count)
    if width * width != count:
        raise ValueError("Mesh 端点数必须为平方数。")
    current, result = src, [src]
    # 确定性 XY：先横向，再纵向。
    while current % width != dst % width:
        current += 1 if current % width < dst % width else -1
        result.append(current)
    while current // width != dst // width:
        current += width if current // width < dst // width else -width
        result.append(current)
    return result


def simulate_network(packets, count=16, topology="mesh", link_latency=1, max_cycles=10000):
    """store-and-forward 单 flit 包；每条有向链路每周期接受一包。

    无 VC、有限 buffer、credit、路由器仲裁或多 flit 包，不模拟真实协议死锁。
    按全局包 ID 仲裁链路；输出实际排队与到达周期，不拟合能耗。
    """
    if not 2 <= count <= 64 or not 1 <= link_latency <= 100:
        raise ValueError("端点为 2..64，链路延迟为 1..100 周期。")
    if len(packets) > 2000:
        raise ValueError("最多 2000 个包。")
    entries = []
    for pid, (src, dst, injection) in enumerate(packets):
        if injection < 0:
            raise ValueError("注入周期不能为负。")
        entries.append(dict(id=pid, src=src, dst=dst, injection=injection,
                            route=route(src, dst, count, topology), step=0,
                            ready=injection, arrival=None, waits=0))
    timeline, cycle = [], 0
    while any(e["arrival"] is None for e in entries):
        used = set()
        for e in entries:
            if e["arrival"] is not None or e["ready"] > cycle:
                continue
            if e["step"] == len(e["route"]) - 1:
                e["arrival"] = cycle
                continue
            link = (e["route"][e["step"]], e["route"][e["step"] + 1])
            if link in used:
                e["waits"] += 1
                continue
            used.add(link)
            timeline.append(dict(cycle=cycle, packet=e["id"], src=link[0], dst=link[1]))
            e["step"] += 1
            e["ready"] = cycle + link_latency
        cycle += 1
        if cycle > max_cycles:
            raise ValueError("超过网络模拟周期上限。")
    latency = [e["arrival"] - e["injection"] for e in entries]
    return dict(packets=entries, timeline=timeline, cycles=cycle,
                avg_latency=sum(latency) / max(1, len(latency)),
                max_latency=max(latency, default=0), hops=sum(len(e["route"]) - 1 for e in entries),
                queue_wait=sum(e["waits"] for e in entries))


def timing_lab(stage_delays_ps, clock_ghz=2.0, setup_ps=40.0, skew_ps=20.0):
    """寄存器之间的组合级延迟列表；skew 参数表示最坏的时钟不确定度。"""
    if not stage_delays_ps or any(not math.isfinite(v) or v < 0 for v in stage_delays_ps):
        raise ValueError("级延迟必须为有限非负数。")
    if not all(math.isfinite(v) for v in (clock_ghz, setup_ps, skew_ps)) or clock_ghz <= 0 or setup_ps < 0 or skew_ps < 0:
        raise ValueError("时钟为正数，setup/不确定度为非负数。")
    period = 1000 / clock_ghz
    rows = [dict(stage=i + 1, delay=d, required=d + setup_ps + skew_ps,
                 slack=period - d - setup_ps - skew_ps) for i, d in enumerate(stage_delays_ps)]
    longest = max(stage_delays_ps) + setup_ps + skew_ps
    return dict(period_ps=period, rows=rows, wns=min(r["slack"] for r in rows),
                fmax_ghz=1000 / longest if longest else math.inf,
                setup_met=all(r["slack"] >= 0 for r in rows))


def power_lab(*, capacitance_pf=1000, activity=0.2, voltage=0.9,
              frequency_ghz=2, leakage_w=.2, thermal_r=5, thermal_c=2,
              ambient=25, duration=60):
    """单节点热 RC 的阶跃功耗解析解。这里的 C 是等效热容 J/K。"""
    values = [capacitance_pf, activity, voltage, frequency_ghz, leakage_w,
              thermal_r, thermal_c, ambient, duration]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("参数必须为有限数。")
    if min(capacitance_pf, voltage, frequency_ghz, leakage_w, duration) < 0 or not 0 <= activity <= 1 or thermal_r <= 0 or thermal_c <= 0:
        raise ValueError("检查物理参数范围。")
    dynamic = activity * capacitance_pf * 1e-12 * voltage ** 2 * frequency_ghz * 1e9
    total = dynamic + leakage_w
    tau = thermal_r * thermal_c
    points = [(duration * i / 60, ambient + total * thermal_r * (1 - math.exp(-duration * i / 60 / tau))) for i in range(61)]
    return dict(dynamic_w=dynamic, total_w=total, tau_s=tau,
                steady_c=ambient + total * thermal_r, points=points, final_c=points[-1][1])


def logic_lab(op, a, b, bits=8):
    """有限位宽 ALU 真值实验；加法给出溢出与进位的不同含义。"""
    if not 1 <= bits <= 32 or not isinstance(a, int) or not isinstance(b, int):
        raise ValueError("位宽 1..32，输入为整数。")
    mask = (1 << bits) - 1
    a, b = a & mask, b & mask
    if op == "add":
        full = a + b
        result, carry = full & mask, full > mask
        sign = 1 << (bits - 1)
        overflow = bool(not ((a ^ b) & sign) and ((a ^ result) & sign))
    elif op == "and": result, carry, overflow = a & b, False, False
    elif op == "xor": result, carry, overflow = a ^ b, False, False
    elif op == "or": result, carry, overflow = a | b, False, False
    else: raise ValueError("只支持 add / and / xor / or。")
    return dict(a=a, b=b, result=result, carry=carry, overflow=overflow,
                binary=f"{result:0{bits}b}", signed=result if result < 1 << (bits - 1) else result - (1 << bits))
