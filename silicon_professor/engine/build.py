"""芯片构建：block 尺寸、die 尺寸、自动布局、布线/拥塞/热图指标。"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..data.blocks import (COOLING, DRAMS, FIXED_BLOCKS, GPUS, METAL_STACKS,
                           NOCS, NPUS, PACKAGES)
from ..data.blocks import get_gpu, get_npu, get_isp
from ..data.cores import CORES, get_ip
from ..data.nodes import NODES
from . import ppa
from .memory import memory_spec
from .types import Design, Placement

CORE_COLORS = {
    "big": "#ff7a6b",
    "mid": "#ffc46b",
    "little": "#7ee7c7",
    "l2": "#4fa3ff",
    "l3": "#3d7fe0",
    "slc": "#8f7bff",
    "gpu": "#ff6bd6",
    "npu": "#b98cff",
    "isp": "#57d6c7",
    "modem": "#ffb86b",
    "media": "#9d8cff",
    "display": "#c6a6ff",
    "dramphy": "#6db3ff",
    "io": "#8a93a6",
}


@dataclass
class Block:
    id: str
    kind: str
    label: str
    area: float
    power: float
    aspect: float = 1.0
    edge: bool = False
    group: int = -1
    core_index: int = -1
    w: float = 1.0
    h: float = 1.0
    color: str = "#8899aa"

    def __post_init__(self):
        self.recompute()

    def recompute(self):
        a = max(0.12, self.area)
        asp = max(0.2, self.aspect)
        self.w = max(0.55, math.sqrt(a * asp))
        self.h = max(0.55, a / self.w)
        if self.color == "#8899aa":
            self.color = CORE_COLORS.get(self.kind, "#8899aa")

    def dims(self, rot: int = 0) -> tuple[float, float]:
        return (self.h, self.w) if rot % 180 == 90 else (self.w, self.h)


@dataclass
class CoreCalc:
    group_index: int
    group: object
    ip: dict
    impl: object
    count: int
    fmax: float
    clock: float
    area_each: float
    power_each: float
    ipc_base: float
    block_ids: list[str] = field(default_factory=list)
    l2_block_id: str | None = None


@dataclass
class Plan:
    design: Design
    node: dict
    blocks: list[Block]
    groups: list[CoreCalc]
    die_w: float = 10.0
    die_h: float = 10.0
    used_area: float = 0.0
    die_area: float = 0.0
    placements: dict[str, Placement] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    fit: bool = True

    def block_map(self):
        return {b.id: b for b in self.blocks}


def _dims_for(area: float, aspect: float) -> tuple[float, float]:
    w = max(0.55, math.sqrt(max(0.12, area) * max(0.2, aspect)))
    h = max(0.55, max(0.12, area) / w)
    return w, h


def _new_block(id_, kind, label, area, power, aspect=1.0, edge=False, group=-1, core_index=-1):
    return Block(id=id_, kind=kind, label=label, area=max(0.12, area), power=max(0.0, power),
                 aspect=aspect, edge=edge, group=group, core_index=core_index,
                 color=CORE_COLORS.get(kind, "#8899aa"))


def build_blocks(design: Design) -> tuple[list[Block], list[CoreCalc], dict]:
    node = NODES[design.node_id]
    metal = METAL_STACKS.get(design.metal_stack, METAL_STACKS["balanced"])
    blocks: list[Block] = []
    groups: list[CoreCalc] = []

    for gi, g in enumerate(design.cores):
        if g.count <= 0:
            continue
        ip = get_ip(design, g.core_id)
        if not ip:
            continue
        fmax = ppa.core_fmax(ip, g.impl, node) * metal["freq_factor"]
        clock = g.clock if g.clock and g.clock > 0 else fmax * 0.90
        clock = min(clock, fmax * 1.10) * 1.0

        shared = bool(g.l2_shared)
        core_area = ppa.core_area(ip, g.impl, node, 0.0 if shared else g.l2_mb, shared, g.count)
        core_area *= 1.0 + 0.015 * getattr(design, "bench_isa", 0.0)
        if shared:
            l2_area = g.l2_mb * node["sram_mb"] * (0.80 + 0.04 * g.count)
            l2_area = max(0.15, l2_area)
            l2_block = _new_block(f"l2:{gi}", "l2", f"L2 {g.l2_mb:g}MB", l2_area,
                                  0.035 * g.l2_mb, aspect=3.0, group=gi)
            blocks.append(l2_block)
            l2_id = l2_block.id
        else:
            l2_id = None

        dyn, leak = ppa.core_power(ip, clock, fmax, core_area, node, g.impl, 85.0)
        power_each = dyn + leak
        calc = CoreCalc(gi, g, ip, g.impl, g.count, fmax, clock, core_area,
                        power_each, ip["ipc"], l2_block_id=l2_id)
        for i in range(g.count):
            bid = f"core:{gi}:{i}"
            b = _new_block(bid, ip["tier"], f"{ip['name']} #{i + 1}", core_area,
                           power_each, aspect=g.impl.aspect, group=gi, core_index=i)
            blocks.append(b)
            calc.block_ids.append(bid)
        groups.append(calc)

    # L3：共享一份，或每个簇一份
    l3_area_each = max(0.25, design.l3_mb * node["sram_mb"] * 0.90 + 0.5)
    if design.l3_shared:
        blocks.append(_new_block("l3", "l3", f"L3 {design.l3_mb:g}MB", l3_area_each,
                                 0.06 * design.l3_mb, aspect=4.0))
    else:
        for g in groups:
            blocks.append(_new_block(f"l3:{g.group_index}", "l3", f"L3 {design.l3_mb:g}MB (簇)",
                                     l3_area_each, 0.06 * design.l3_mb / max(1, len(groups)),
                                     aspect=4.0, group=g.group_index))

    if design.slc_mb > 0.01:
        slc_area = max(0.25, design.slc_mb * node["sram_mb"] * 0.85 + 0.3)
        blocks.append(_new_block("slc", "slc", f"SLC {design.slc_mb:g}MB", slc_area,
                                 0.05 * design.slc_mb, aspect=3.5))

    # GPU
    gpu = get_gpu(design)
    gpu_ratio = node["area_scale"] / ppa.ref_node(gpu)["area_scale"]
    gpu_freq_ratio = node["freq_scale"] / ppa.ref_node(gpu)["freq_scale"]
    gpu_units = max(gpu["min_units"], min(gpu["max_units"], design.gpu_units))
    gpu_area = max(0.4, gpu_units * gpu["area_per_unit"] * gpu_ratio)
    gpu_power = gpu_units * gpu["power_per_unit"] * (gpu_freq_ratio ** 1.4)
    blocks.append(_new_block("gpu", "gpu", f"{gpu['name']} ({gpu_units}{gpu['unit_name']})",
                             gpu_area, gpu_power, aspect=1.5))

    # NPU / 固定块
    npu = get_npu(design)
    if npu["tops"] > 0:
        blocks.append(_new_block("npu", "npu", f"{npu['name']} {npu['tops']}T",
                                 npu["area"] * (node["area_scale"] ** 0.7), npu["power"], aspect=1.3))

    def add_fixed(fid, panel_id=None):
        f = get_isp(design) if fid == "isp" else FIXED_BLOCKS[panel_id or fid]
        b = _new_block(fid, fid if fid in CORE_COLORS else "io", f["name"],
                       f["area"] * (node["area_scale"] ** 0.6), f["power"],
                       aspect=6.0 if f["edge"] else 1.6, edge=f.get("edge", False))
        b.color = f["color"]
        blocks.append(b)

    if design.isp:
        add_fixed("isp")
    modem = FIXED_BLOCKS.get(design.modem_id, FIXED_BLOCKS["modem5g"])
    if not modem.get("external"):
        blocks.append(_new_block("modem", "modem", modem["name"],
                                 modem["area"] * (node["area_scale"] ** 0.6), modem["power"],
                                 aspect=1.3))
    if design.media:
        add_fixed("media")
    if design.display:
        add_fixed("display")

    dram = DRAMS.get(design.dram, DRAMS["lpddr4x"])
    channels = memory_spec(design)["channels"]
    phy_area = FIXED_BLOCKS["dramphy"]["area"] * (node["area_scale"] ** 0.6) * channels
    phy = _new_block("dramphy", "dramphy", f"DRAM PHY ×{channels}",
                     phy_area, FIXED_BLOCKS["dramphy"]["power"] * channels,
                     aspect=max(0.9, 8.0 / channels), edge=True)
    blocks.append(phy)
    add_fixed("io")

    return blocks, groups, dict(gpu=gpu, gpu_units=gpu_units, gpu_area=gpu_area,
                                gpu_power=gpu_power, gpu_freq_ratio=gpu_freq_ratio,
                                npu=npu, dram=dram)


def _pack_at_width(normal: list[Block], width: float):
    """Guillotine 装箱：固定宽度，高度自适应。"""
    free = [(0.0, 0.0, width, 400.0)]
    placed: dict[str, tuple[float, float, float, float]] = {}
    for b in sorted(normal, key=lambda x: (max(x.w, x.h), x.area), reverse=True):
        best = None
        for i, (fx, fy, fw, fh) in enumerate(free):
            if b.w <= fw + 0.001 and b.h <= fh + 0.001:
                short = min(fw - b.w, fh - b.h)
                long_ = max(fw - b.w, fh - b.h)
                score = (short, long_)
                if best is None or score < best[0]:
                    best = (score, i)
        if best is None:
            return None
        i = best[1]
        fx, fy, fw, fh = free.pop(i)
        placed[b.id] = (fx, fy, b.w, b.h)
        if fw - b.w > 0.05:
            free.append((fx + b.w, fy, fw - b.w, b.h))
        if fh - b.h > 0.05:
            free.append((fx, fy + b.h, fw, fh - b.h))
        # 去掉被完全包含的空闲矩形
        pruned = []
        for r in free:
            contained = False
            for q in free:
                if r is q:
                    continue
                if (r[0] >= q[0] - 0.01 and r[1] >= q[1] - 0.01
                        and r[0] + r[2] <= q[0] + q[2] + 0.01
                        and r[1] + r[3] <= q[1] + q[3] + 0.01):
                    contained = True
                    break
            if not contained:
                pruned.append(r)
        free = pruned
    if not placed:
        return placed, 0.0, 0.0
    right = max(x + w for x, y, w, h in placed.values())
    bottom = max(y + h for x, y, w, h in placed.values())
    return placed, right, bottom


def _treemap_fill(items, x, y, w, h, out):
    if not items:
        return
    if len(items) == 1:
        out[items[0].id] = (x, y, w, h)
        return
    total = sum(b.area for b in items)
    acc = 0.0
    cut = 1
    for i, b in enumerate(items):
        acc += b.area
        if acc >= total / 2.0:
            cut = i + 1
            break
    left, right = items[:cut], items[cut:]
    if not right:
        out[items[-1].id] = (x, y, w, h)
        return
    ratio = sum(b.area for b in left) / total
    if w >= h:
        _treemap_fill(left, x, y, w * ratio, h, out)
        _treemap_fill(right, x + w * ratio, y, w * (1 - ratio), h, out)
    else:
        _treemap_fill(left, x, y, w, h * ratio, out)
        _treemap_fill(right, x, y + h * ratio, w, h * (1 - ratio), out)


def _pack_layout(blocks: list[Block], used: float, aspect: float):
    """按 82% 目标利用率生成 die，再用面积切分把 block 塞进去。"""
    margin = 0.15
    target_area = max(1.0, used) / 0.86
    aspect = max(0.65, min(1.9, aspect))
    die_w = math.sqrt(target_area * aspect)
    die_h = target_area / die_w

    edge = [b for b in blocks if b.edge]
    io = next((b for b in edge if b.kind == "io"), None)
    phy = next((b for b in edge if b.kind == "dramphy"), None)
    io_h = io.area / die_w if io else 0.0
    phy_w = phy.area / max(1.0, die_h - io_h) if phy else 0.0
    inner_w = max(2.0, die_w - phy_w)
    inner_h = max(2.0, die_h - io_h)

    normal = [b for b in blocks if not b.edge]
    raw: dict[str, tuple[float, float, float, float]] = {}
    _treemap_fill(sorted(normal, key=lambda b: b.area, reverse=True), 0.0, 0.0,
                  inner_w, inner_h, raw)
    placements: dict[str, Placement] = {}
    for b in normal:
        px, py, pw, ph = raw.get(b.id, (0, 0, inner_w, inner_h))
        a = max(0.12, b.area)
        asp = max(0.2, b.aspect)
        w = min(pw, math.sqrt(a * asp))
        h = a / max(0.1, w)
        if h > ph:
            h = ph
            w = a / max(0.1, h)
        x = max(0.0, px + (pw - w) / 2.0)
        y = max(0.0, py + (ph - h) / 2.0)
        placements[b.id] = Placement(x + margin, y + margin, 0, w, h)
    if io:
        placements[io.id] = Placement(margin, die_h - io_h + margin, 0, die_w, io_h)
    if phy:
        placements[phy.id] = Placement(die_w - phy_w + margin, margin, 0, phy_w,
                                       die_h - io_h)
    return placements, die_w + 2 * margin, die_h + 2 * margin


def build_plan(design: Design, force_layout: bool = False) -> Plan:
    node = NODES[design.node_id]
    metal = METAL_STACKS.get(design.metal_stack, METAL_STACKS["balanced"])
    noc = NOCS.get(design.noc, NOCS["ring"])
    blocks, groups, extra = build_blocks(design)
    used = sum(b.area for b in blocks)
    aspect = max(0.65, min(1.9, design.floorplan_aspect))
    plan = Plan(design=design, node=node, blocks=blocks, groups=groups,
                die_w=0.0, die_h=0.0, used_area=used, die_area=used)

    ids = {b.id for b in blocks}
    stale = force_layout or not design.placements or any(k not in ids for k in design.placements)
    if not stale:
        for b in blocks:
            p = design.placements.get(b.id)
            if p is None:
                stale = True
                break
            if p.w <= 0 or p.h <= 0:
                stale = True
                break
            area_p = max(0.0, p.w * p.h)
            if abs(area_p - b.area) / max(0.1, b.area) > 0.22:
                stale = True
                break
    if stale:
        placements, dw, dh = _pack_layout(blocks, used, aspect)
        design.placements = placements
        plan.die_w, plan.die_h = dw, dh

    plan.placements = dict(design.placements)
    rects = [_rect(plan, b) for b in blocks]
    max_x = max((r[0] + r[2] for r in rects), default=5.0)
    max_y = max((r[1] + r[3] for r in rects), default=5.0)
    plan.die_w = max_x + 0.42
    plan.die_h = max_y + 0.42
    plan.die_area = plan.die_w * plan.die_h

    plan.metrics = _metrics(plan)
    plan.metrics.update(extra)
    _validate(plan)
    return plan


def _rect(plan: Plan, b: Block):
    p = plan.placements.get(b.id)
    if not p:
        return (0.0, 0.0, 0.0, 0.0)
    if p.w > 0 and p.h > 0:
        w, h = (p.h, p.w) if p.rot % 180 == 90 else (p.w, p.h)
    else:
        w, h = b.dims(p.rot)
    return (p.x, p.y, w, h)


def _overlap(a, b, eps=0.04) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw - eps and bx < ax + aw - eps and ay < by + bh - eps and by < ay + ah - eps


def _links(plan: Plan, bm: dict[str, Block]) -> list[tuple[str, str, float]]:
    cluster_count = max(1, len(plan.groups))
    links: list[tuple[str, str, float]] = []
    l3_shared = plan.design.l3_shared
    for g in plan.groups:
        target_l3 = "l3" if l3_shared else f"l3:{g.group_index}"
        if g.l2_block_id:
            for cid in g.block_ids:
                links.append((cid, g.l2_block_id, 4.0))
            links.append((g.l2_block_id, target_l3, 4.0))
        else:
            for cid in g.block_ids:
                links.append((cid, target_l3, 3.0))
    if "gpu" in bm:
        links.append(("gpu", "l3" if l3_shared else f"l3:0", 6.0))
        if "slc" in bm:
            links.append(("gpu", "slc", 3.0))
    if "npu" in bm:
        links.append(("npu", "l3" if l3_shared else f"l3:0", 4.0))
        if "slc" in bm:
            links.append(("npu", "slc", 2.5))
    if "slc" in bm:
        links.append(("slc", "l3" if l3_shared else f"l3:0", 3.0))
    for src, w in (("dramphy", 5.0),):
        for g in plan.groups:
            tgt = "l3" if l3_shared else f"l3:{g.group_index}"
            links.append((tgt, src, w))
    for src, w in (("isp", 4.0), ("media", 3.0), ("display", 2.0), ("modem", 2.0)):
        if src in bm:
            links.append((src, "dramphy", w))
    if "io" in bm:
        links.append(("io", "dramphy", 2.0))
        if "modem" in bm:
            links.append(("modem", "io", 2.0))
        if "display" in bm:
            links.append(("display", "io", 2.0))
    return [(a, b, w) for a, b, w in links if a in bm and b in bm]


def _metrics(plan: Plan) -> dict:
    bm = plan.block_map()
    overlaps = []
    rects = {}
    for b in plan.blocks:
        r = _rect(plan, b)
        rects[b.id] = r
        if r[0] < -0.02 or r[1] < -0.02 or r[0] + r[2] > plan.die_w + 0.02 or r[1] + r[3] > plan.die_h + 0.02:
            plan.errors.append(f"{b.label} 超出 die 边界")
    for i, a in enumerate(plan.blocks):
        for b in plan.blocks[i + 1:]:
            if _overlap(rects[a.id], rects[b.id]):
                overlaps.append((a.label, b.label))
    if overlaps:
        plan.errors.append("模块重叠：" + "、".join(f"{a}/{b}" for a, b in overlaps[:3]))

    links = _links(plan, bm)
    segments = []
    total_w = 0.0
    total_len = 0.0
    wire_power = 0.0
    for a, bid, weight in links:
        ax, ay, aw, ah = rects[a]
        bx, by, bw, bh = rects[bid]
        acx, acy = ax + aw / 2, ay + ah / 2
        bcx, bcy = bx + bw / 2, by + bh / 2
        dist = abs(acx - bcx) + abs(acy - bcy)
        segments.append((acx, acy, bcx, bcy, weight))
        total_w += weight
        total_len += dist * weight
        wire_power += dist * weight
    avg_dist = total_len / max(1e-6, total_w)
    metal = METAL_STACKS.get(plan.design.metal_stack, METAL_STACKS["balanced"])
    wire_power *= 0.00075 * metal["wire_power"]

    # 拥塞：1mm 网格上的通道占用
    nx = max(2, int(math.ceil(plan.die_w)))
    ny = max(2, int(math.ceil(plan.die_h)))
    usage = [[0.0] * nx for _ in range(ny)]
    for x1, y1, x2, y2, w in segments:
        steps = max(8, int((abs(x2 - x1) + abs(y2 - y1)) * 2))
        for s in range(steps + 1):
            t = s / steps
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            ix = min(nx - 1, max(0, int(x)))
            iy = min(ny - 1, max(0, int(y)))
            usage[iy][ix] += w
    peak = max(max(row) for row in usage)
    congestion = max(0.0, min(0.08, (peak - 12.0) * 0.004))

    # 功率密度热图
    grid = [[0.0] * nx for _ in range(ny)]
    for b in plan.blocks:
        x, y, w, h = rects[b.id]
        dens = b.power / max(0.2, b.area)
        ix0, ix1 = int(x), min(nx, int(math.ceil(x + w)))
        iy0, iy1 = int(y), min(ny, int(math.ceil(y + h)))
        for iy in range(max(0, iy0), max(0, iy1)):
            for ix in range(max(0, ix0), max(0, ix1)):
                grid[iy][ix] += dens
    for _ in range(3):
        grid = _blur(grid)
    hot_rise = 0.0
    for row in grid:
        for v in row:
            hot_rise = max(hot_rise, v * 24.0)

    util = plan.used_area / max(1e-6, plan.die_area)
    return dict(
        wire_power=wire_power,
        avg_wire_mm=avg_dist,
        congestion=congestion,
        hotspot_rise=hot_rise,
        utilization=util,
        segments=segments,
        heat=grid,
        grid_w=nx,
        grid_h=ny,
        overlaps=len(overlaps),
        total_block_area=plan.used_area,
        die_area=plan.die_area,
    )


def _blur(grid):
    ny, nx = len(grid), len(grid[0])
    k = (1.0, 2.0, 1.0)
    tmp = [[0.0] * nx for _ in range(ny)]
    for y in range(ny):
        for x in range(nx):
            s = 0.0
            ws = 0.0
            for d, w in zip((-1, 0, 1), k):
                xx = x + d
                if 0 <= xx < nx:
                    s += grid[y][xx] * w
                    ws += w
            tmp[y][x] = s / ws
    out = [[0.0] * nx for _ in range(ny)]
    for y in range(ny):
        for x in range(nx):
            s = 0.0
            ws = 0.0
            for d, w in zip((-1, 0, 1), k):
                yy = y + d
                if 0 <= yy < ny:
                    s += tmp[yy][x] * w
                    ws += w
            out[y][x] = s / ws
    return out


def _validate(plan: Plan):
    for b in plan.blocks:
        if b.edge:
            x, y, w, h = _rect(plan, b)
            if not (x <= 0.7 or y <= 0.7 or x + w >= plan.die_w - 0.7 or y + h >= plan.die_h - 0.7):
                plan.errors.append(f"{b.label} 必须贴边放置（PHY/IO 约束）")
    if plan.metrics.get("utilization", 0) > 0.96:
        plan.warnings.append("die 利用率 > 96%，布线资源非常紧张。")
    plan.fit = not plan.errors
