"""关卡 = 市场细分 + 预算 + 目标。"""
from __future__ import annotations

SEGMENTS = {
    "mid2019": dict(
        id="mid2019", name="中端 5G · 2020", year=2020, budget_m=55,
        tagline="把 5G 手机做到 300 美元以内。",
        brief=("运营商正在推 5G，但市场要的是“买得起”。你没有旗舰预算，也没有最新节点。"
               "从两颗 A76 与四颗 A55 起步，在面积、功耗和单颗成本之间取舍。"),
        allowed_nodes=["n7", "n5"],
        allowed_licenses=["arm", "riscv"],
        weights=dict(st=0.28, mt=0.24, gpu=0.18, eff=0.18, ai=0.12),
        targets=dict(st=750, mt=1500, gpu=450, ai=8, battery_h=10),
        limits=dict(max_die_area=90, max_cost=30, max_tdp=6, skin_temp=43, max_die_w=11, max_die_h=11),
        base_units_m=12, ref_price=38, battery_wh=17.3, board="phone",
        competitor=dict(name="竞品 A", st=650, mt=2600, gpu=360, price=42),
        prev=dict(name="2018 主流", st=550, mt=2200, gpu=300),
        tutorial="先选 N7，再放 2×A76 + 4×A55。L2 不用贪大，同时检查缓存面积与成本。",
        evidence=[], confidence="medium",
    ),
    "flagship2022": dict(
        id="flagship2022", name="旗舰 · 2022", year=2022, budget_m=95,
        tagline="单核要赢，持续性能也不能塌。",
        brief=("旗舰机的媒体评测只看两件事：跑分和发热。X3 的单核很强，"
               "但增加 X3 数量会提高电源与散热要求。你需要决定：几颗大核、多少缓存、什么总线。"),
        allowed_nodes=["n4p", "n5", "sf4"],
        allowed_licenses=["arm", "riscv"],
        weights=dict(st=0.35, mt=0.25, gpu=0.20, eff=0.10, ai=0.10),
        targets=dict(st=1750, mt=4000, gpu=700, ai=18, battery_h=8),
        limits=dict(max_die_area=130, max_cost=65, max_tdp=12, skin_temp=45, max_die_w=13, max_die_h=13),
        base_units_m=6, ref_price=88, battery_wh=17.3, board="phone",
        competitor=dict(name="竞品 B", st=1450, mt=5000, gpu=720, price=92),
        prev=dict(name="骁龙888 级", st=1150, mt=3400, gpu=720),
        tutorial="一颗 X3 冲单核，三颗 A715 撑多核。L3 给到 8MB，NoC 用 mesh。",
        evidence=[], confidence="medium",
    ),
    "xring2025": dict(
        id="xring2025", name="玄戒时刻 · 2025", year=2025, budget_m=150,
        tagline="同样的 Arm 核，做出不一样的芯片。",
        brief=("你拿到了 Cortex-X925 和 N3E。公版参考实现只是起点：物理实现中的库档位、时序约束、"
               "长宽比，会让同一颗核在面积、频率和发热上完全不同。问题是，N3E 的 mask 和良率都很贵。"),
        allowed_nodes=["n3e", "n3p", "n3b", "n4p"],
        allowed_licenses=["arm", "riscv"],
        weights=dict(st=0.34, mt=0.24, gpu=0.20, eff=0.12, ai=0.10),
        targets=dict(st=2550, mt=6400, gpu=950, ai=30, battery_h=8),
        limits=dict(max_die_area=135, max_cost=100, max_tdp=17, skin_temp=47, max_die_w=13.5, max_die_h=13.5),
        base_units_m=5, ref_price=115, battery_wh=17.3, board="phone",
        competitor=dict(name="竞品 C", st=2500, mt=7000, gpu=980, price=120),
        prev=dict(name="上代主流", st=2400, mt=6800, gpu=900),
        tutorial="试着把 X925 做成 2:1 长条、HP 库 + LVT，再把 A725 压密度。注意良率和热点。",
        evidence=[], confidence="medium",
    ),
    "laptop2025": dict(
        id="laptop2025", name="轻薄本 · 2025", year=2025, budget_m=220,
        tagline="15W 持续性能，续航一整天。",
        brief=("手机那套堆大核的办法在笔记本上不成立：用户会连续编译、开会、跑模型。"
               "你需要更多核心、更低漏电、更好的封装，还要控制待机功耗。"),
        allowed_nodes=["n3p", "n3e", "n4p"],
        allowed_licenses=["arm", "riscv"],
        weights=dict(st=0.20, mt=0.30, gpu=0.20, eff=0.20, ai=0.10),
        targets=dict(st=2350, mt=7500, gpu=850, ai=42, battery_h=12),
        limits=dict(max_die_area=190, max_cost=130, max_tdp=30, skin_temp=60, max_die_w=18, max_die_h=18),
        base_units_m=2.5, ref_price=190, battery_wh=70.0, board="laptop",
        competitor=dict(name="竞品 D", st=2350, mt=9000, gpu=1150, price=200),
        prev=dict(name="M1 级", st=2200, mt=8000, gpu=1800),
        tutorial="2.5D 封装 + 风扇，允许更高持续功耗。用 HVT 混搭压漏电，换更长续航。",
        evidence=[], confidence="medium",
    ),
    "sandbox": dict(
        id="sandbox", name="沙盒实验室", year=2026, budget_m=999,
        tagline="自由组合 IP，比较架构方案。",
        brief=("所有节点、所有 IP 全部解锁，包括仅供研究的自研核（研究沙盒）。"
               "自由验证你的架构直觉，或者构建公开芯片的近似研究方案。"),
        allowed_nodes=["n7", "n5", "n4", "n4p", "n3e", "n3p", "n2", "n2p", "sf4", "sf3", "intel18a", "smicN2"],
        allowed_licenses=["arm", "riscv", "research", "custom"],
        weights=dict(st=0.30, mt=0.25, gpu=0.20, eff=0.15, ai=0.10),
        targets=dict(st=2500, mt=6200, gpu=950, ai=30, battery_h=10),
        limits=dict(max_die_area=220, max_cost=140, max_tdp=35, skin_temp=60, max_die_w=18, max_die_h=18),
        base_units_m=3, ref_price=120, battery_wh=17.3, board="phone",
        competitor=dict(name="参照组", st=2400, mt=7500, gpu=950, price=120),
        tutorial="先按图鉴复刻一颗 8 Gen 3，再试着超过它。",
        evidence=[], confidence="medium",
    ),
}

SEGMENTS["fold2026"] = dict(
    id="fold2026", name="折叠屏 · 2026", year=2026, budget_m=170,
    tagline="把旗舰塞进对折的机身。",
    brief=("大折叠的内部空间被铰链和两块电池切碎：die 不能大，散热靠不住，"
           "但内屏又大又费电。这是一项假设性的产品设计任务，"
           "条件是你真的把功耗和尺寸管住。"),
    allowed_nodes=["n3p", "n3e", "n2"],
    allowed_licenses=["arm", "riscv"],
    weights=dict(st=0.30, mt=0.22, gpu=0.18, eff=0.20, ai=0.10),
    targets=dict(st=2600, mt=6500, gpu=950, ai=35, battery_h=8),
    limits=dict(max_die_area=110, max_cost=110, max_tdp=12, skin_temp=43,
                max_die_w=12, max_die_h=12),
    base_units_m=3, ref_price=150, battery_wh=12.0, board="fold",
    competitor=dict(name="竞品 F", st=2500, mt=6200, gpu=900, price=155),
    prev=dict(name="上代折叠旗舰", st=2300, mt=5800, gpu=850),
    tutorial="die ≤ 110mm²、机身 43°C 是硬墙；SLC 和 HVT 是你的朋友。",
    evidence=[], confidence="low",
)

from .challenges import challenge_segments
SEGMENTS.update(challenge_segments(SEGMENTS))
from copy import deepcopy
SEGMENTS['x86_workstation']=deepcopy(SEGMENTS['laptop2025'])
SEGMENTS['x86_workstation'].update(id='x86_workstation',name='x86 工作站 · 32位核心设计',year=2026,budget_m=300,
    tagline='从Intel/AMD熟悉的指令家族开始，设计自己的32位x86核心。',
    brief='选择顺序或乱序x86教学核，检查程序依赖、缓存与吞吐，再用于工作站SoC。三种模板都含可执行硬件定义，可载入LAB编辑；不冒称Intel/AMD厂商产品，尚无x86-64长模式、SSE/AVX或OS。',
    allowed_licenses=['arm','riscv','research','custom'],
    tutorial='先用x86双发射顺序核；架构页“在LAB编辑教学核心”打开硬件，比较独立运算、依赖链和缓存任务。发布后替换同ISA集群。',
    evidence=['intel_ia32'],confidence='game_assumption')
SEGMENT_LIST = list(SEGMENTS.values())

for _item in SEGMENTS.values():
    _item["parameter_basis"] = "game_assumption"
