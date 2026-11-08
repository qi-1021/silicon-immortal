"""设计状态的数据结构（可直接 JSON 序列化）。"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Impl:
    """物理实现选项：库、阈值电压、密度/时序偏向、长宽比。"""
    lib: str = "sd"          # hd | sd | hp
    vt: str = "svt"          # ulvt | lvt | svt | hvt
    density: float = 0.35    # 0 面积优先 .. 1 密度优先
    timing: float = 0.35     # 0 省电优先 .. 1 时序优先
    aspect: float = 1.0      # 1 | 2 | 4，核的长宽比

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict | None) -> "Impl":
        d = d or {}
        return cls(
            lib=str(d.get("lib", "sd")),
            vt=str(d.get("vt", "svt")),
            density=float(d.get("density", 0.35)),
            timing=float(d.get("timing", 0.35)),
            aspect=float(d.get("aspect", 1.0)),
        )


@dataclass
class CoreGroup:
    core_id: str
    count: int = 2
    l2_mb: float = 0.0
    l2_shared: bool = False
    clock: float = 0.0       # 目标频率 GHz；0 = 自动
    impl: Impl = field(default_factory=Impl)

    def to_dict(self) -> dict:
        return {
            "core_id": self.core_id,
            "count": self.count,
            "l2_mb": self.l2_mb,
            "l2_shared": self.l2_shared,
            "clock": self.clock,
            "impl": self.impl.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CoreGroup":
        return cls(
            core_id=str(d["core_id"]),
            count=int(d.get("count", 2)),
            l2_mb=float(d.get("l2_mb", 0.0)),
            l2_shared=bool(d.get("l2_shared", False)),
            clock=float(d.get("clock", 0.0)),
            impl=Impl.from_dict(d.get("impl")),
        )


@dataclass
class Placement:
    x: float
    y: float
    rot: int = 0
    w: float = 0.0
    h: float = 0.0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "rot": self.rot, "w": self.w, "h": self.h}

    @classmethod
    def from_dict(cls, d: dict) -> "Placement":
        return cls(float(d.get("x", 0)), float(d.get("y", 0)), int(d.get("rot", 0)),
                   float(d.get("w", 0)), float(d.get("h", 0)))


@dataclass
class CustomCore:
    """沙盒里的自研核：宽度/ROB/缓存/流水线深度决定 IPC、面积、频率、功耗。"""
    name: str = "自研大核"
    isa: str = "armv9"
    decode: int = 6
    rob: int = 320
    l1_kb: int = 64
    pipeline: int = 12
    backend: int = 6
    extensions: list[str] = field(default_factory=lambda: ["M"])

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict | None) -> "CustomCore":
        d = d or {}
        return cls(
            name=str(d.get("name", "自研大核")),
            isa=str(d.get("isa", "armv9")),
            decode=int(d.get("decode", 6)),
            rob=int(d.get("rob", 320)),
            l1_kb=int(d.get("l1_kb", 64)),
            pipeline=int(d.get("pipeline", 12)),
            backend=int(d.get("backend", 6)),
            extensions=[str(e) for e in d.get("extensions", ["M"])],
        )


@dataclass
class Design:
    scenario_id: str = "mid2019"
    name: str = ""
    node_id: str = "n7"
    cores: list[CoreGroup] = field(default_factory=list)
    l3_mb: float = 2.0
    l3_shared: bool = True
    slc_mb: float = 0.0
    noc: str = "ring"
    dram: str = "lpddr4x"
    gpu_id: str = "maliG76"
    gpu_units: int = 12
    npu_id: str = "npu8"
    modem_id: str = "modem5g"
    storage_id: str = "ufs31"
    isp: bool = True
    media: bool = True
    display: bool = True
    metal_stack: str = "balanced"
    package_id: str = "pop"
    chiplet: bool = False
    cooling_id: str = "graphite"
    ambient_c: float = 25.0
    floorplan_aspect: float = 1.1
    routing_overhead: float = 0.12
    placements: dict[str, Placement] = field(default_factory=dict)
    bench_tuning: float = 0.0
    bench_isa: float = 0.0
    rotated_once: bool = False
    eco_invest: float = 0.0       # 0..1，生态适配投入
    price: float = 38.0
    reputation: float = 0.50
    verification_effort: float = 0.60  # 验证工程投入，不代表实际测得的覆盖率
    pvt_corner: str = "tt"            # tt | ss | ff，教学用相对角落
    pdn_quality: float = 0.60         # 电源网络投入：降低估算电阻，增加 NRE
    memory_channels: int = 0         # 0 沿用代际默认；其余为 x16 通道数
    memory_gb: int = 8
    workload_parallel: float = 0.90
    workload_set_mb: float = 32.0
    workload_intensity: float = 4.0  # 每个 DRAM 字节对应的抽象运算数
    seed: int = 2025
    custom: CustomCore = field(default_factory=CustomCore)
    embedded_ips: dict[str,dict] = field(default_factory=dict)
    ip_blocks: dict[str,str] = field(default_factory=dict)
    core_templates: dict[str,dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["placements"] = {k: v.to_dict() for k, v in self.placements.items()}
        d["cores"] = [c.to_dict() for c in self.cores]
        d["custom"] = self.custom.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Design":
        d = d or {}
        cores = [CoreGroup.from_dict(c) for c in d.get("cores", [])]
        placements = {
            k: Placement.from_dict(v) for k, v in (d.get("placements") or {}).items()
        }
        from .ip_library import validate_asset
        from .core_bundle import validate_templates
        templates=validate_templates(d.get('core_templates',{}))
        originals=d.get('embedded_ips',{})
        if not isinstance(originals,dict) or len(originals)>64:raise ValueError('内嵌IP库无效或超过64项。')
        assets={}
        for key,record in originals.items():
            asset=validate_asset(record)
            if key!=asset['id']:raise ValueError('IP键与稳定ID不一致。')
            assets[key]=asset
        bindings=d.get('ip_blocks',{})
        if not isinstance(bindings,dict) or any(kind not in ('gpu','npu','isp') or ident not in assets or assets[ident]['kind']!=kind for kind,ident in bindings.items()):raise ValueError('IP绑定不匹配。')
        return cls(
            scenario_id=str(d.get("scenario_id", "mid2019")),
            name=str(d.get("name", "")),
            node_id=str(d.get("node_id", "n7")),
            cores=cores,
            l3_mb=float(d.get("l3_mb", 2.0)),
            l3_shared=bool(d.get("l3_shared", True)),
            slc_mb=float(d.get("slc_mb", 0.0)),
            noc=str(d.get("noc", "ring")),
            dram=str(d.get("dram", "lpddr4x")),
            gpu_id=str(d.get("gpu_id", "maliG76")),
            gpu_units=int(d.get("gpu_units", 12)),
            npu_id=str(d.get("npu_id", "npu8")),
            modem_id=str(d.get("modem_id", "modem5g")),
            storage_id=str(d.get("storage_id", "ufs31")),
            isp=bool(d.get("isp", True)),
            media=bool(d.get("media", True)),
            display=bool(d.get("display", True)),
            metal_stack=str(d.get("metal_stack", "balanced")),
            package_id=str(d.get("package_id", "pop")),
            chiplet=bool(d.get("chiplet", False)),
            cooling_id=str(d.get("cooling_id", "graphite")),
            ambient_c=float(d.get("ambient_c", 25.0)),
            floorplan_aspect=float(d.get("floorplan_aspect", 1.1)),
            routing_overhead=float(d.get("routing_overhead", 0.12)),
            placements=placements,
            bench_tuning=float(d.get("bench_tuning", 0.0)),
            bench_isa=float(d.get("bench_isa", 0.0)),
            rotated_once=bool(d.get("rotated_once", False)),
            eco_invest=float(d.get("eco_invest", 0.0)),
            price=float(d.get("price", 38.0)),
            reputation=float(d.get("reputation", 0.50)),
            verification_effort=float(d.get("verification_effort", 0.60)),
            pvt_corner=str(d.get("pvt_corner", "tt")),
            pdn_quality=float(d.get("pdn_quality", 0.60)),
            memory_channels=int(d.get("memory_channels", 0)),
            memory_gb=int(d.get("memory_gb", 8)),
            workload_parallel=float(d.get("workload_parallel", 0.90)),
            workload_set_mb=float(d.get("workload_set_mb", 32.0)),
            workload_intensity=float(d.get("workload_intensity", 4.0)),
            seed=int(d.get("seed", 2025)),
            custom=CustomCore.from_dict(d.get("custom")),
            embedded_ips=assets,ip_blocks=dict(bindings),core_templates=templates,
        )


def empty_design(scenario_id: str = "mid2019") -> Design:
    """每个关卡一个合理的初始设计，玩家可以在此基础上修改。"""
    from ..data.challenges import CHALLENGES
    if scenario_id in CHALLENGES:
        from .challenges import challenge_design
        return challenge_design(scenario_id)
    if scenario_id == "flagship2022":
        d = Design(scenario_id=scenario_id, node_id="n4p", l3_mb=8, noc="mesh",
                   dram="lpddr5", gpu_id="g715", gpu_units=11, npu_id="npu16",
                   package_id="fowlp", cooling_id="vc", price=88, seed=2022)
        d.cores = [
            CoreGroup("x3", 1, 1.0, False, 3.3),
            CoreGroup("a715", 3, 0.512, False, 2.9),
            CoreGroup("a510", 4, 0.256, False, 1.8),
        ]
        return d
    if scenario_id == "xring2025":
        d = Design(scenario_id=scenario_id, node_id="n3e", l3_mb=12, noc="mesh",
                   dram="lpddr5x", gpu_id="g925", gpu_units=16, npu_id="npu30",
                   package_id="fowlp", cooling_id="vcPro", price=115, seed=2025)
        d.cores = [
            CoreGroup("x925", 2, 2.0, False, 3.8),
            CoreGroup("a725", 6, 0.512, False, 3.0),
            CoreGroup("a520", 2, 0.256, False, 1.8),
        ]
        return d
    if scenario_id == "laptop2025":
        d = Design(scenario_id=scenario_id, node_id="n3p", l3_mb=16, noc="mesh",
                   dram="lpddr5x", gpu_id="g925", gpu_units=12, npu_id="npu45",
                   package_id="imc25d", cooling_id="laptop", price=190, seed=2025,
                   ambient_c=25)
        d.cores = [
            CoreGroup("x925", 4, 2.0, False, 3.4),
            CoreGroup("a725", 4, 1.0, False, 2.8),
            CoreGroup("a520", 4, 0.256, False, 1.8),
        ]
        return d
    if scenario_id == "fold2026":
        d = Design(scenario_id=scenario_id, node_id="n3p", l3_mb=12, noc="mesh",
                   dram="lpddr5x", gpu_id="g2Ultra", gpu_units=12, npu_id="npu45",
                   modem_id="modem5g", storage_id="ufs40",
                   package_id="fowlp", cooling_id="vcPro", price=145, seed=2026)
        d.cores = [
            CoreGroup("c1_ultra", 2, 3.0, False, 4.0),
            CoreGroup("c1_pro", 4, 1.0, False, 3.2),
            CoreGroup("c1_nano", 2, 0.256, False, 2.0),
        ]
        return d
    if scenario_id == "sandbox":
        d = Design(scenario_id=scenario_id, node_id="n3e", l3_mb=12, noc="mesh",
                   dram="lpddr5x", gpu_id="g925", gpu_units=16, npu_id="npu30",
                   package_id="fowlp", cooling_id="vc", price=120, seed=7)
        d.cores = [
            CoreGroup("x925", 1, 2.0, False, 3.7),
            CoreGroup("a725", 5, 0.512, False, 3.0),
            CoreGroup("a520", 2, 0.256, False, 1.8),
        ]
        return d
    d = Design(scenario_id=scenario_id, node_id="n7", l3_mb=2, noc="ring",
               dram="lpddr4x", gpu_id="maliG76", gpu_units=12, npu_id="npu8",
               modem_id="modem_ext", package_id="pop", cooling_id="graphite",
               price=38, seed=2019)
    d.cores = [
        CoreGroup("a76", 2, 0.512, False, 2.6),
        CoreGroup("a55", 4, 0.256, False, 1.8),
    ]
    return d
