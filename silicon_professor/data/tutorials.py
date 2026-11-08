"""教学关卡：每关只教一个决策，目标可实时勾选。

check(design, result) 必须只读，返回 bool；教学页会按顺序显示进度。
"""
from __future__ import annotations

from ..engine.build import build_plan
from ..engine.types import CoreGroup, Design, empty_design
from .cores import get_ip


def _mid() -> Design:
    d = empty_design("mid2019")
    d.cores = [CoreGroup("a76", 2, 0.512, False, 2.6),
               CoreGroup("a55", 4, 0.256, False, 1.8)]
    return d


def _flagship() -> Design:
    return empty_design("flagship2022")


def _xring() -> Design:
    return empty_design("xring2025")


def _pricey() -> Design:
    d = _flagship()
    d.price = 110
    return d


def _sandbox() -> Design:
    return empty_design("sandbox")


def _d9300_like() -> Design:
    d = empty_design("sandbox")
    d.node_id = "n4p"
    d.cores = [CoreGroup("x4", 4, 1.0, False, 3.2),
               CoreGroup("a720", 4, 0.512, False, 2.85)]
    d.l3_mb = 8
    d.gpu_id, d.gpu_units = "g720", 12
    d.npu_id = "npu30"
    d.dram = "lpddr5x"
    d.package_id = "fowlp"
    d.cooling_id = "vc"
    d.price = 120
    # 故意做一个“GPU 被丢到角落”的坏布局，让学生把它挪回来
    plan = build_plan(d)
    g = d.placements["gpu"]
    g.x = plan.die_w - g.w - 0.35
    g.y = plan.die_h - g.h - 0.35
    return d


def _single_x925() -> Design:
    d = empty_design("sandbox")
    d.cores = [CoreGroup("x925", 1, 2.0, False, 3.8)]
    d.l3_mb = 8
    d.gpu_id, d.gpu_units = "g925", 8
    d.price = 100
    return d


def _cost(result) -> float:
    return result["cost"]["total"]


def _peak(result) -> float:
    return result["power"]["peak"]


def _mt(result) -> float:
    return result["perf"]["mt_burst"]


def _st(result) -> float:
    return result["perf"]["st_burst"]


TUTORIALS = [
    dict(
        id="t1", title='第一课：制程与成本', tag="制程 / 面积 / 成本",
        concept="N5 比 N7 更密、更快，但晶圆和 mask 更贵。",
        intro="你手上是一颗 2019 年的中端设计。把它从 N7 换到 N5，看看面积和成本会怎么变。",
        make=_mid,
        steps=[
            dict(title="把制程换到 N5", text="在架构页选择 TSMC N5。",
                 hint="同样的逻辑，N5 的密度约为 N7 的 1.75 倍。",
                 screen="architecture", check=lambda d, r: d.node_id == "n5"),
            dict(title="die 面积 ≤ 50mm²", text="中端芯片的封装和成本都不允许大 die。",
                 hint="N7 版本约 63mm²；N5 会把它压到 50mm² 以内。",
                 screen="architecture", check=lambda d, r: r["die_area"] <= 50),
            dict(title="单颗成本 ≤ $30", text="换制程后重新检查 BOM。",
                 hint="外挂基带会省 die 面积，但增加 $9 BOM。",
                 screen="signoff", check=lambda d, r: _cost(r) <= 30),
        ],
    ),
    dict(
        id="t2", title='第二课：核心规模与功耗', tag="大小核 / 热 / 持续性能",
        concept="多核跑分会被功率和散热吃掉；峰值和持续是两回事。",
        intro="这是一颗 1×X925 + 5×A725 + 2×A520 的沙盒设计。把它压到手机能承受的功耗，同时保住多核。",
        make=_sandbox,
        steps=[
            dict(title="峰值功耗 ≤ 10W", text="先看封装页的热结果。",
                 hint="降目标频率、换更省电的 VT、或减小 GPU 都能降峰值。",
                 screen="package", check=lambda d, r: _peak(r) <= 10.0),
            dict(title="多核 MT 仍 ≥ 5000", text="不能靠砍核心把功耗做低。",
                 hint="保留 1 颗大核 + 若干中核，比全小核更划算。",
                 screen="architecture", check=lambda d, r: _mt(r) >= 5000),
            dict(title="持续降频 ≤ 20%", text="跑分只看峰值，用户看的是持续。",
                 hint="换 VC、把大核目标频率降到 2.4GHz 左右，都能减少降频。",
                 screen="package", check=lambda d, r: r["thermal"]["throttle"] <= 0.20),
        ],
    ),
    dict(
        id="t3", title='第三课：缓存与带宽', tag="L2 / L3 / SLC / 面积",
        concept="缓存能抬 IPC，但 SRAM 面积随容量线性增长。",
        intro="一颗旗舰设计已经有 8MB L3。试着用缓存把单核拉起来，同时别让 die 爆掉。",
        make=_flagship,
        steps=[
            dict(title="L3 ≥ 12MB", text="更大的 L3 让多核共享数据更便宜。",
                 hint="在架构页的缓存卡片里调。",
                 screen="architecture", check=lambda d, r: d.l3_mb >= 12),
            dict(title="SLC ≥ 8MB", text="系统级缓存同时喂 CPU/GPU/NPU。",
                 hint="SLC 很贵，但它是 Apple 式能效的关键。",
                 screen="architecture", check=lambda d, r: d.slc_mb >= 8),
            dict(title="单核 ST ≥ 1800", text="缓存最终要变成性能。",
                 hint="如果 ST 不够，检查大核频率与 L2 是否被砍太小。",
                 screen="architecture", check=lambda d, r: _st(r) >= 1800),
            dict(title="die ≤ 130mm²", text="缓存不是白送的。",
                 hint="面积超了就砍 GPU 或把中核换成更小的核。",
                 screen="signoff", check=lambda d, r: r["die_area"] <= 130),
        ],
    ),
    dict(
        id="t4", title="第四课：同一份 RTL，做出不同频率", tag="物理实现 / 库 / VT / 长宽比",
        concept="公版参考实现只是起点；库、VT、时序和形状由你自己定。",
        intro="一颗 X925 参考实现跑 3.8GHz。把它推到 3.9GHz 以上，同时保住面积和良率——这就是玄戒 O1 做过的事。",
        make=_single_x925,
        steps=[
            dict(title="目标频率 ≥ 3.9GHz", text="在物理实现页调整 X925。",
                 hint="HP 库 + LVT + 时序优先，能换到更高 Fmax，但面积和功耗会涨。",
                 screen="physical", check=lambda d, r: any(g["clock"] >= 3.9 for g in r["groups"])),
            dict(title="Fmax 均值 ≥ 3.95GHz", text="光设目标不算，工艺分布要跟得上。",
                 hint="密度滑杆往左（时序优先）会提高 Fmax。",
                 screen="physical", check=lambda d, r: any(g["fmax"] >= 3.95 for g in r["groups"])),
            dict(title="die ≤ 140mm²", text="别把重实现做成一颗更大的芯片。",
                 hint="长宽比 2:1 通常比 4:1 更省布线。",
                 screen="signoff", check=lambda d, r: r["die_area"] <= 140),
            dict(title="频率 bin ≥ 35%", text="目标频率越接近均值，能卖的 die 越多。",
                 hint="看签核页的 bin 明细。",
                 screen="signoff", check=lambda d, r: r["bin"]["fraction"] >= 0.35),
        ],
    ),
    dict(
        id="t5", title="第五课：把热点拆开", tag="Floorplan / 走线 / 热",
        concept="布局同时决定走线功耗和局部热点；大核和 GPU 不能挤在一起。",
        intro="这是一颗 4×X4 + 4×A720 的全大核设计。默认布局很挤，先让它通过签核检查。",
        make=_d9300_like,
        steps=[
            dict(title="没有模块重叠 / 越界", text="拖动或点“自动布局”。",
                 hint="自动布局是起点，不是答案。",
                 screen="floorplan", check=lambda d, r: not r["errors"]),
            dict(title="走线功耗 ≤ 450mW", text="把通信多的模块放近一点。",
                 hint="GPU 现在被丢在右下角，把它挪回 L3 旁边。",
                 screen="floorplan", check=lambda d, r: r["metrics"]["wire_power"] <= 0.45),
            dict(title="热点 ≤ 75°C", text="局部功率密度太高会触发额外降频。",
                 hint="大核与 GPU 不要挤在一起；拖开一点。",
                 screen="floorplan", check=lambda d, r: r["thermal"]["hotspot"] <= 80),
        ],
    ),
    dict(
        id="t6", title="第六课：跑分与真实体验", tag="Benchmark / 调优 / 口碑",
        concept="官方跑分可以调，但媒体实测和持续体验会揭穿过度优化。",
        intro="这颗芯片默认能跑 2700 分。把官方分推到 2900，同时别让实测和口碑崩掉。",
        make=_xring,
        steps=[
            dict(title="官方 ST ≥ 2900", text="在签核页提高“跑分优化”。",
                 hint="30% 以内算合理调优，再高就开始伤实测。",
                 screen="signoff", check=lambda d, r: r["perf"]["official_st"] >= 2900),
            dict(title="实测 ST ≥ 2600", text="媒体会用真实应用复测。",
                 hint="别把跑分优化拉满。",
                 screen="signoff", check=lambda d, r: r["perf"]["real_st"] >= 2600),
            dict(title="没有被媒体识破", text="过度优化有概率被识破并扣分。",
                 hint="看发布页的提示。",
                 screen="report", check=lambda d, r: not r["market"]["caught"]),
            dict(title="媒体评分 ≥ 85", text="口碑是下一颗芯片的起点。",
                 hint="价格、热、实测分都会影响评分。",
                 screen="report", check=lambda d, r: r["market"]["review"] >= 85),
        ],
    ),
    dict(
        id="t7", title="第七课：定价是最后一颗旋钮", tag="价格 / 需求 / 利润",
        concept="高价不一定高利润；需求弹性和成本共同决定净利。",
        intro="一颗旗舰芯片已经完成，但初始定价 $110 太高。试着在 $75–$95 之间定价，让利润和口碑都成立。",
        make=lambda: _pricey(),
        steps=[
            dict(title="售价在 $75–$95", text="先看签核页的毛利。",
                 hint="定价不是越低越好，需求弹性约 1.8。",
                 screen="signoff", check=lambda d, r: 75 <= d.price <= 95),
            dict(title="媒体评分 ≥ 88", text="价格太离谱会被评测扣分。",
                 hint="评分同时看性能、热和性价比。",
                 screen="report", check=lambda d, r: r["market"]["review"] >= 88),
            dict(title="净利润 ≥ $200M", text="NRE 是一次性成本，必须靠销量摊薄。",
                 hint="试着在 $80–$95 之间微调。",
                 screen="report", check=lambda d, r: r["market"]["profit"] >= 200),
        ],
    ),
]

TUTORIAL_BY_ID = {t["id"]: t for t in TUTORIALS}

LECTURES = {
    "t1": (
        '制程节点是工艺家族的名称，并非一个真实物理尺寸。更先进的节点通常提高逻辑密度，但 SRAM、模拟和 I/O 的缩放速度不同。\n\n本作将逻辑面积与 SRAM 面积分开计算。晶圆费用、掩模费用和缺陷良率同时影响成本。比较节点时，应比较满足相同频率与功能的方案，而不是只看节点数字。'),
    "t2": (
        '动态功耗近似为 α·C·V²·f。提高频率往往需要提高电压，功耗会比频率增长更快；漏电还受温度、阈值电压与工艺影响。\n\n增加性能核可以提高并行吞吐，但串行工作、带宽和散热会限制收益。芯片功耗与整机功耗需要分开测量，超过某个瓦数并不意味着必然烧毁。这里的峰值与持续值来自简化功耗预算，不预测真实设备能够保持峰值的秒数。'),
    "t3": (
        '私有 L2 让核心访问本地数据，共享 L3 提供更大的公共容量，SLC 可以服务多个系统客户端。真实层级与共享范围取决于具体 IP。\n\n缓存的效果依赖工作集、访问模式、命中延迟和一致性流量。共享 L2 的容量是整组总量，不能按每核重复使用。Arm DSU 的支持核数取决于具体版本，本作的十核惩罚只是教学规则。'),
    "t4": (
        '物理实现将 RTL 综合为门级网表，再完成布局、时钟树和布线。单元库、阈值电压组合与时序约束影响面积、频率和漏电。低 VT 常用于关键路径，高 VT 可减少非关键路径漏电。\n\n调整标准单元库不等于修改 CPU 解码器或执行后端。Arm CPU IP 授权与架构授权也不同：前者提供具体设计，后者允许在许可范围内自行实现 ISA。本作把实现选择表示为连续参数，没有生成真实网表。'),
    "t5": (
        'Floorplan 先安排宏单元、I/O、电源与布线通道，再进行细粒度单元布局。长线带来电阻、电容和时序压力，靠近的高功耗模块可能形成热点。\n\n本作规定 PHY 贴边以便教学；真实 flip-chip I/O 可通过 bump 和重新分布层连接，不是所有 I/O 都必须在边缘。硅片视图的金属纹理和 SRAM 网格是示意，不能用于提取电路。'),
    "t6": (
        '跑分结果依赖测试版本、编译器、功耗限制、环境温度与散热设备。短时分数、持续吞吐、帧时间和能耗回答的是不同问题。\n\n合法的编译器与指令优化也能改善真实应用。本作的“测试专用路径”专指只优化测试负载的抽象策略，不表示 ISA 扩展天然没有实用价值。重复测试应固定条件并报告分布，不能只选最高分。'),
    "t7": (
        '晶圆、封装和测试是变动成本，研发与掩模是固定投入。需要足够销量来摊薄固定成本；提高售价会增加单颗毛利，也可能减少需求。\n\n本作按有限市场计算需求，销量上限为基准市场的三倍。芯片方案成本与整机配套成本分别显示，外部内存、存储和散热不会自动计入芯片厂的利润。'),
}

for _t in TUTORIALS:
    if _t["id"] in LECTURES:
        _t["lecture"] = LECTURES[_t["id"]]


def _gpu_base() -> Design:
    d = empty_design("sandbox")
    d.cores = [CoreGroup("x925", 1, 2.0, False, 3.6),
               CoreGroup("a725", 5, 0.512, False, 3.0),
               CoreGroup("a520", 2, 0.256, False, 1.8)]
    d.node_id = "n3e"
    d.gpu_id, d.gpu_units = "g720", 8
    d.npu_id = "npu30"
    d.price = 120
    return d


def _memory_base() -> Design:
    d = empty_design("mid2019")
    d.node_id = "n7"
    d.cores = [CoreGroup("a76", 2, 0.512, False, 2.6),
               CoreGroup("a55", 4, 0.256, False, 1.8)]
    d.gpu_id, d.gpu_units = "maliG76", 12
    d.npu_id = "npu8"
    d.dram = "lpddr4x"
    d.modem_id = "modem_ext"
    d.price = 40
    return d


def _layout_base() -> Design:
    d = empty_design("xring2025")
    d.media = True
    return d


def _fail_base() -> Design:
    # 又热又激进：石墨散热 + 35°C 环境 + 大核 3.6GHz + 调优拉满
    d = _flagship()
    d.cooling_id = "graphite"
    d.ambient_c = 35
    d.cores[0].clock = 3.6
    d.bench_tuning = 0.9
    d.gpu_units = 16
    d.placements.clear()
    return d


def _acc_base() -> Design:
    # 又大又杂：12 核共享 L3 + UFS 2.2 + 4G 基带 + PoP
    d = _flagship()
    d.cores = [
        CoreGroup("x3", 1, 1.0, False, 3.3),
        CoreGroup("a715", 5, 0.512, False, 2.9),
        CoreGroup("a510", 6, 0.256, False, 1.8),
    ]
    d.storage_id = "ufs22"
    d.modem_id = "modem4g"
    d.package_id = "pop"
    d.placements.clear()
    return d


def _riscv_base() -> Design:
    d = empty_design("sandbox")
    d.node_id = "n5"
    d.cores = [CoreGroup("p670", 4, 0.512, False, 2.4)]
    d.l3_mb = 4
    d.gpu_id, d.gpu_units = "g720", 8
    d.npu_id = "npu16"
    d.dram = "lpddr5"
    d.price = 80
    return d


TUTORIALS.extend([
    dict(
        id="t8", title="第八课：GPU、NPU 与兼容性", tag="GPU / CU / NPU / 驱动",
        concept="GPU 可以按 CU/MC 规模规划；不同 GPU 的驱动/游戏兼容性不同。NPU 在没有硬性 AI 需求时可以不集成。",
        intro="这是一颗 1+5+2 的 SoC，GPU 只有 8 个 MC，NPU 是 30T。把 GPU 扩到 12 MC 以上，并试着去掉 NPU。",
        lecture=(
            '不同 GPU 的 MC、CU、WGP 或“核心”没有统一的等价关系。跨架构比较应固定工作负载、API、分辨率和功耗，不能直接比较单元数量。\n\nNPU TOPS 必须注明整数或浮点精度、稀疏条件，以及如何计一次运算。本作 NPU 档位按稠密 INT8 峰值运算能力抽象，AI 指标是游戏综合分。能否运行一个模型还取决于 DRAM 容量、带宽、算子支持与软件栈，不能由 TOPS 单独判断。'),
        make=_gpu_base,
        steps=[
            dict(title="GPU 规模 ≥ 12 MC", text="在架构页把 GPU 单元数拉上去。",
                 hint="g720 默认 12 MC；8 MC 在 2025 年偏小。",
                 screen="architecture", check=lambda d, r: d.gpu_units >= 12),
            dict(title="GPU 兼容性 ≥ 90%", text="驱动/游戏生态也是规格。",
                 hint="Mali/Immortalis 兼容性最好；PowerVR/自研 GPU 会扣分。",
                 screen="architecture", check=lambda d, r: r["perf"]["gpu_compat"] >= 0.90),
            dict(title="去掉 NPU", text="观察面积节省与 AI 综合分的变化。",
                 hint="NPU 选择“无 NPU”。",
                 screen="architecture", check=lambda d, r: d.npu_id == "none"),
        ],
    ),
    dict(
        id="t9", title="第九课：基带与内存", tag="5G / 外挂 / LPDDR / 带宽",
        concept="基带可以集成或外挂；内存代际决定带宽与功耗。两者都不是“附属品”。",
        intro="一颗 2019 中端设计：外挂 5G 基带 + LPDDR4X。试着升级内存，并比较集成/外挂基带的代价。",
        lecture=(
            '内存理论带宽 = 数据率 × 总位宽 ÷ 8。这里的速率单位为 MT/s，每通道为 x16；8533 MT/s、四通道对应约 68.3 GB/s。协议、刷新、访问模式和控制器调度会降低有效带宽。\n\n集成基带减少外部器件，但消耗主 die 面积；外挂方案增加器件费用、板级空间与通信功耗。信号质量不能由集成与否或 4G/5G 名称单独决定，还涉及 RF 前端、天线和运营商网络。'),
        make=_memory_base,
        steps=[
            dict(title="内存升级到 LPDDR5X", text="在架构页切换内存型号。",
                 hint="LPDDR5X 提供约 68GB/s，远高于 LPDDR4X。",
                 screen="architecture", check=lambda d, r: d.dram in ("lpddr5x", "lpddr5t")),
            dict(title="单颗成本 ≤ $35", text="外挂基带省 die，但 BOM 会涨。",
                 hint="集成基带会增加 die 面积，但省掉外挂器件成本。",
                 screen="signoff", check=lambda d, r: r["cost"]["total"] <= 35),
            dict(title="续航 ≥ 8 小时", text="新内存和基带都会影响待机功耗。",
                 hint="看签核页/架构页的电池估算。",
                 screen="signoff", check=lambda d, r: r["perf"]["battery_h"] >= 8),
        ],
    ),
    dict(
        id="t10", title="第十课：布局进阶：旋转、增删、快速设计", tag="Floorplan / 旋转 / 模块增删",
        concept="布局不是只拖位置：模块可以旋转、增删；自动布局只是起点。",
        intro="这颗旗舰设计包含媒体/显示/NPU。试着移除媒体模块、旋转一个模块，并让布局重新通过签核。",
        lecture=(
            '模块面积固定时，改变形状和位置会改变互连长度与可用通道。SRAM 宏的合法方向和引脚边由工艺库规定，不能任意旋转。\n\n自动布局提供起点。减少功能块要同时考虑产品需求：去掉显示或媒体模块可能节省面积，但相关工作需要软件或外部器件承担。本作允许这些实验，不验证完整系统是否可启动。'),
        make=_layout_base,
        steps=[
            dict(title="移除媒体引擎", text="在布局页的“模块”卡片里取消媒体引擎。",
                 hint="没有视频硬解需求时，媒体模块可以省掉。",
                 screen="floorplan", check=lambda d, r: not d.media),
            dict(title="旋转至少一个模块", text="选中模块，点“旋转 90°”。",
                 hint="旋转后检查是否重叠/越界。",
                 screen="floorplan", check=lambda d, r: d.rotated_once),
            dict(title="布局有效且走线 ≤ 600mW", text="点自动布局后微调。",
                 hint="先保证 valid，再追求更短走线。",
                 screen="floorplan", check=lambda d, r: r["valid"] and r["metrics"]["wire_power"] <= 0.60),
        ],
    ),
    dict(
        id="t11", title="第十一课：RISC-V 与自研核", tag="ISA / 生态 / 自研",
        concept="RISC-V 授权自由，但生态是硬成本；自研核可以做出差异化，但 NRE 很高。",
        intro="这是一颗 4×SiFive P670 的 RISC-V 设计。把生态投入拉起来，让它至少能卖。",
        lecture=(
            'ISA 决定软件可见的指令与状态，不直接决定 IPC、面积或功耗。Arm 与 RISC-V 都可以实现简单顺序核或复杂乱序核。\n\n更宽解码、更多 ROB 项目和更大缓存增加资源，也可能提高关键路径和布线压力。软件移植涉及编译器、操作系统、驱动和应用；ISA 使用许可不等于某个 CPU 核 IP 免费。真实 SoC 可以组合不同 ISA 的控制处理器，本作只限制同一应用核集群的混用。'),
        make=_riscv_base,
        steps=[
            dict(title="全部核心使用 RISC-V", text="确认没有混入 ARM 核。",
                 hint="ARM + RISC-V 双软件栈不现实。",
                 screen="architecture", check=lambda d, r: all(
                     (get_ip(d, g.core_id) or {}).get("isa") == "riscv"
                     for g in d.cores if g.count > 0)),
            dict(title="生态适配投入 ≥ 80%", text="在签核页拉高生态投入。",
                 hint="这会增加 NRE，但能补回兼容性。",
                 screen="signoff", check=lambda d, r: d.eco_invest >= 0.80),
            dict(title="生态评分 ≥ 0.86", text="让 RISC-V 至少达到可用的软件体验。",
                 hint="看发布页/市场评分里的 eco。",
                 screen="report", check=lambda d, r: r["market"]["eco"] >= 0.86),
        ],
    ),
    dict(
        id="t12", title='第十二课：稳定性与可靠性', tag='验证 / 供电 / 热应力',
        concept='设计要同时满足功能、性能、功耗和可靠性目标。',
        intro='这颗旗舰频率和测试调优偏激进，散热与供电投入不足。降低风险，同时保住产品目标。',
        lecture=(
            '首发缺陷、持续降频和长期可靠性是不同问题。复位与 CDC 错误、供电瞬态、时序裕量不足都可能导致功能异常，不能只凭节点名称推断故障。\n\n长期可靠性通常考虑 BTI、HCI、电迁移等机制，需要任务占空比、温度、电压、材料和加速寿命测试。本作的风险事件与应力折损只是游戏规则，不能预测真实芯片一年后的性能，也不对应某款手机的故障概率。\n\n先降低激进频率与测试调优，再提高散热和电源网络投入。工程验证页会解释供电、验证与 PVT 约束，发布页显示其商业后果。'),
        make=_fail_base,
        steps=[
            dict(title="游戏风险事件概率 ≤ 12%", text="降低频率与供电相关的模拟风险。",
                 hint="降低调优和目标频率，改善散热，并在工程验证页提高电源网络投入。",
                 screen="signoff", check=lambda d, r: r["market"]["p_crash"] <= 0.12),
            dict(title="应力折损后的性能系数 ≥ 90%", text="比较教学应力情景，不预测实际寿命。",
                 hint="降热点、降持续降频：散热、频率与环境温度一起看。",
                 screen="report", check=lambda d, r: r["market"]["aged_ratio"] >= 0.90),
            dict(title="媒体评分 ≥ 85", text="排完雷，评分自然回来。",
                 hint="黑屏、应力折损、代际提升有限都会扣分；看发布页。",
                 screen="report", check=lambda d, r: r["market"]["review"] >= 85),
        ],
    ),
])
TUTORIAL_BY_ID = {t["id"]: t for t in TUTORIALS}

TUTORIALS.extend([
    dict(
        id="t13", title='第十三课：系统配套与互连', tag="簇规模 / UFS / 基带 / 供电",
        concept='共享互连、存储、基带和供电共同决定系统表现。',
        intro='这个实验方案把十二颗核心放在共享互连上，并采用较低规格存储与 4G 基带。按产品目标逐项调整。',
        lecture=(
            '一致性互连、存储控制器、基带与供电都属于系统设计。共享缓存有容量和仲裁开销，但支持的核心数必须查具体 DSU 或互连 IP 的技术手册。\n\n存储代际会影响带宽上限，应用启动还依赖延迟、队列和软件。基带与射频需要系统测试；供电需要检查稳态 IR drop、瞬态压降和电迁移。本作分别提供教学约束，不把这些因素直接等同于特定品牌的故障。'),
        make=_acc_base,
        steps=[
            dict(title="簇规模合规", text="12 核共享一个 L3 超过了 DSU 簇规模。",
                 hint="把小核减到 4 个以内，或关掉 L3 共享（拆簇）。",
                 screen="architecture",
                 check=lambda d, r: sum(g.count for g in d.cores) <= 10 or not d.l3_shared),
            dict(title="存储 UFS 3.1+", text="旗舰不能配 UFS 2.2。",
                 hint="在架构页把存储换到 UFS 3.1 或 4.0。",
                 screen="architecture", check=lambda d, r: d.storage_id != "ufs22"),
            dict(title="5G 基带", text="5G 时代用 4G 基带会被差评。",
                 hint="集成 5G 或外挂 5G 都可以，看 die 与 BOM 的取舍。",
                 screen="architecture", check=lambda d, r: d.modem_id != "modem4g"),
        ],
    ),
])
TUTORIAL_BY_ID = {t["id"]: t for t in TUTORIALS}


def _verification_base():
    d = empty_design("sandbox")
    d.verification_effort = 0.10
    d.pdn_quality = 0.0
    d.pvt_corner = "ss"
    return d


TUTORIALS.append(dict(
    id="t14", title="第十四课：工程验证与工艺角落", tag="PVT / IR drop / 验证规划",
    concept="高频目标需要供电和验证投入，也要检查慢速、低压、高温条件。",
    intro="标称条件下的方案未必能通过慢速角落。完成验证规划，降低供电压降，再调整频率目标。",
    lecture="TT、SS、FF 表示工艺角落的简化分类。实际签核还需要电压、温度、互连 RC、OCV 和多模式条件。不能从一个均值频率得到所有条件下的保证。\n\n本作把角落表示为相对频率倍率，并通过 I×R 估算供电压降。真实检查需要版图、功耗波形和寄生网络；本页的投入与门槛只提供教学取舍。",
    make=_verification_base,
    steps=[
        dict(title="验证规划完成度 ≥ 85%", text="补齐验证投入。", hint="工程验证页将验证投入调到 75% 或以上。",
             screen="engineering", check=lambda d, r: r["engineering"]["verification_completion"] >= 0.85),
        dict(title="供电压降 ≤ 80mV", text="降低电流或等效电阻。", hint="提高电源网络投入，也可以降低频率。",
             screen="engineering", check=lambda d, r: r["engineering"]["ir_drop_v"] <= 0.08),
        dict(title="SS 角落满足目标档位", text="保留 SS 条件检查目标频率。", hint="将各组频率降低约 15%，再查看角落结果。",
             screen="engineering", check=lambda d, r: d.pvt_corner == "ss" and r["engineering"]["selected_corner"]["bin_supported"]),
        dict(title="全部教学签核检查通过", text="确认方案可以进入流片。", hint="签核页列出剩余约束和修复方式。",
             screen="signoff", check=lambda d, r: r["signoff"]["ready"]),
    ],
))
TUTORIAL_BY_ID = {t["id"]: t for t in TUTORIALS}
