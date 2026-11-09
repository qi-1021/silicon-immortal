"""GPU / NPU / 固定功能块 / 总线 / 内存 / 封装 / 散热 / 金属堆栈。"""
from __future__ import annotations

GPUS = {
    "maliG76": dict(
        id="maliG76", name="Mali-G76 MP12", vendor="Arm", year=2018, ref_node="n7",
        unit_name="MC", default_units=12, min_units=6, max_units=20,
        perf_per_unit=42, area_per_unit=0.80, power_per_unit=0.16,
        license_cost_m=3.0, compat=1.0, cu_per_unit=1, note="2019 中端主力，规模小、能效一般。",
        evidence=[], confidence="medium",
    ),
    "maliG78": dict(
        id="maliG78", name="Mali-G78 MP24", vendor="Arm", year=2020, ref_node="n5",
        unit_name="MC", default_units=24, min_units=10, max_units=24,
        perf_per_unit=36, area_per_unit=0.62, power_per_unit=0.13,
        license_cost_m=4.0, compat=1.0, cu_per_unit=1, note="靠堆核心换性能，面积效率不错。",
        evidence=[], confidence="medium",
    ),
    "g715": dict(
        id="g715", name="Immortalis-G715 MC11", vendor="Arm", year=2022, ref_node="n4p",
        unit_name="MC", default_units=11, min_units=8, max_units=16,
        perf_per_unit=66, area_per_unit=1.05, power_per_unit=0.22,
        license_cost_m=5.0, compat=1.0, cu_per_unit=1, note="首代硬件光追，单核性能强，但很吃面积。",
        evidence=[], confidence="medium",
    ),
    "g720": dict(
        id="g720", name="Immortalis-G720 MC12", vendor="Arm", year=2023, ref_node="n4p",
        unit_name="MC", default_units=12, min_units=10, max_units=16,
        perf_per_unit=68, area_per_unit=1.10, power_per_unit=0.24,
        license_cost_m=5.5, compat=1.0, cu_per_unit=1, note="2023 旗舰常见配置，规模适中。",
        evidence=[], confidence="medium",
    ),
    "g925": dict(
        id="g925", name="Immortalis-G925 MC16", vendor="Arm", year=2024, ref_node="n3e",
        unit_name="MC", default_units=16, min_units=10, max_units=20,
        perf_per_unit=70, area_per_unit=0.98, power_per_unit=0.22,
        license_cost_m=6.5, compat=1.0, cu_per_unit=1, note="玄戒 O1 / 天玑 9400 同款，规模大、能效进步明显。",
        evidence=[], confidence="medium",
    ),
    "powervr": dict(
        id="powervr", name="PowerVR DXT-72", vendor="Imagination", year=2023, ref_node="n4p",
        unit_name="Cluster", default_units=4, min_units=2, max_units=8,
        perf_per_unit=190, area_per_unit=3.0, power_per_unit=0.60,
        license_cost_m=4.0, compat=0.78, cu_per_unit=2, note="授权 GPU 的另一条路线；面积大，驱动生态弱于 Mali。",
        evidence=[], confidence="low",
    ),
    "adreno750": dict(
        id="adreno750", name="Adreno 750", vendor="Qualcomm", year=2023, ref_node="n4p",
        unit_name="Slice", default_units=8, min_units=4, max_units=12,
        perf_per_unit=170, area_per_unit=1.9, power_per_unit=0.45,
        license_cost_m=None, compat=1.0, cu_per_unit=2, note="研究档案：高通自研 GPU，不对外授权。",
        evidence=[], confidence="low",
    ),
    "appleGpu": dict(
        id="appleGpu", name="Apple GPU 10-core", vendor="Apple", year=2022, ref_node="n4p",
        unit_name="Core", default_units=10, min_units=6, max_units=12,
        perf_per_unit=180, area_per_unit=1.8, power_per_unit=0.40,
        license_cost_m=None, compat=1.0, cu_per_unit=1, note="研究档案：苹果自研 GPU。",
        evidence=[], confidence="low",
    ),
    "maleoon": dict(
        id="maleoon", name="Maleoon 910", vendor="Huawei", year=2023, ref_node="smicN2",
        unit_name="Core", default_units=8, min_units=4, max_units=10,
        perf_per_unit=150, area_per_unit=2.1, power_per_unit=0.50,
        license_cost_m=None, compat=0.62, cu_per_unit=1, note="研究档案：华为自研 GPU，受制程限制。",
        evidence=[], confidence="low",
    ),
    "xclipse": dict(
        id="xclipse", name="Xclipse 940 (RDNA 3)", vendor="Samsung/AMD", year=2023, ref_node="n4p",
        unit_name="WGP", default_units=6, min_units=3, max_units=8,
        perf_per_unit=230, area_per_unit=2.8, power_per_unit=0.65,
        license_cost_m=None, compat=0.72, cu_per_unit=2, note="研究档案：AMD RDNA 架构授权给三星。",
        evidence=[], confidence="low",
    ),
}

GPUS.update({
    "g1Ultra": dict(
        id="g1Ultra", name="Immortalis-G1 Ultra", vendor="Arm", year=2025, ref_node="n3p",
        unit_name="MC", default_units=20, min_units=12, max_units=24,
        perf_per_unit=78, area_per_unit=1.10, power_per_unit=0.25,
        license_cost_m=7.5, compat=1.0, cu_per_unit=1,
        note="2025 旗舰 GPU，规模更大；光追与 AI 渲染是卖点。",
        evidence=[], confidence="low",
    ),
    "adreno850": dict(
        id="adreno850", name="Adreno 850", vendor="Qualcomm", year=2025, ref_node="n3p",
        unit_name="Slice", default_units=8, min_units=4, max_units=12,
        perf_per_unit=210, area_per_unit=2.0, power_per_unit=0.50,
        license_cost_m=None, compat=1.0, cu_per_unit=2,
        note="研究档案：高通 2025 自研 GPU。",
        evidence=[], confidence="low",
    ),
    "g2Ultra": dict(
        id="g2Ultra", name="Mali G2 Ultra MP16", vendor="Arm", year=2026, ref_node="n3p",
        unit_name="MC", default_units=16, min_units=10, max_units=24,
        perf_per_unit=88, area_per_unit=1.00, power_per_unit=0.24,
        license_cost_m=8.0, compat=1.0, cu_per_unit=1,
        note="2026 旗舰 GPU，XRING O3 同款 MP16；光追/AI 渲染规模更大。",
        evidence=[], confidence="low",
    ),
    "powervrCXT": dict(
        id="powervrCXT", name="Legacy PowerVR teaching model", vendor="Imagination", year=2021, ref_node="n3p",
        unit_name="Cluster", default_units=4, min_units=2, max_units=6,
        perf_per_unit=150, area_per_unit=2.8, power_per_unit=0.50,
        license_cost_m=3.5, compat=0.62, cu_per_unit=2,
        note="遗留教学参数；不对应已确认的Tensor G5/G6 GPU，年份/资源/PPA均非原版规格。",
        evidence=[], confidence="low",
    ),
    "maleoon920": dict(
        id="maleoon920", name="Maleoon 920", vendor="Huawei", year=2025, ref_node="n3e",
        unit_name="Core", default_units=8, min_units=4, max_units=10,
        perf_per_unit=170, area_per_unit=2.2, power_per_unit=0.55,
        license_cost_m=None, compat=0.60, cu_per_unit=1,
        note="研究档案：华为自研 GPU，游戏兼容性弱于 Mali/Adreno。",
        evidence=[], confidence="low",
    ),
})

NPUS = {
    "none": dict(id="none", name="无 NPU", tops=0, area=0.0, power=0.0,
                 license_cost_m=0.0, note="不集成 NPU：省面积/功耗，但 AI 与影像算法会吃亏。",
                 evidence=[], confidence="high"),
    "npu8": dict(id="npu8", name="入门 NPU", tops=8, area=2.2, power=0.35,
                 license_cost_m=1.5, note="够跑基础影像算法与语音。", evidence=[], confidence="medium"),
    "npu16": dict(id="npu16", name="主流 NPU", tops=16, area=4.0, power=0.7,
                  license_cost_m=2.5, note="2022 旗舰水平，端侧小模型可用。", evidence=[], confidence="medium"),
    "npu30": dict(id="npu30", name="高性能 NPU", tops=30, area=6.8, power=1.2,
                  license_cost_m=4.0, note="教学高算力档位；模型是否能运行还取决于内存、算子和软件。", evidence=[], confidence="medium"),
    "npu45": dict(id="npu45", name="旗舰 NPU", tops=45, area=9.0, power=1.8,
                  license_cost_m=5.5, note="面积和散热压力都不小，但 AI 评分高。", evidence=[], confidence="medium"),
    "npu60": dict(id="npu60", name="桌面级 NPU", tops=60, area=12.0, power=2.8,
                  license_cost_m=7.0, note="笔记本/服务器向，手机压不住。", evidence=[], confidence="low"),
}

FIXED_BLOCKS = {
    "isp": dict(id="isp", name="ISP", area=4.0, power=0.45, license_cost_m=2.0, color="#7ee7c7", edge=False),
    "modem5g": dict(id="modem5g", name="5G 基带", area=8.0, power=1.6, license_cost_m=6.0, color="#ffb86b", edge=False,
                signal=1.00, note_sig="集成 5G，主流选择。"),
    "modem4g": dict(id="modem4g", name="4G 基带", area=4.0, power=0.6, license_cost_m=2.5, color="#ffb86b", edge=False,
                signal=0.95, note_sig="便宜省电，但 5G 时代会被差评（Tensor 早期信号争议的反面教材）。"),
    "modem_ext": dict(id="modem_ext", name="外挂 5G 基带", area=0.01, power=0.0,
                      license_cost_m=3.0, color="#ffb86b", edge=False,
                      external=True, bom_cost=9.0,
                      signal=0.97, note_sig="外挂：成熟方案信号稳，但多一颗芯片的功耗与成本（X50 时代的教训）。"),
    "modem_none": dict(id="modem_none", name="无蜂窝基带", area=0.0, power=0.0,
                       license_cost_m=0.0, color="#ffb86b", edge=False,
                       external=True, bom_cost=0.0, signal=0.97,
                       note_sig="未配置蜂窝连接；不代表没有Wi-Fi、蓝牙或其他I/O。"),
    "media": dict(id="media", name="媒体编解码", area=5.0, power=0.3, license_cost_m=1.5, color="#9d8cff", edge=False),
    "display": dict(id="display", name="显示/视频", area=1.2, power=0.06, license_cost_m=0.8, color="#c6a6ff", edge=False),
    "dramphy": dict(id="dramphy", name="DRAM PHY", area=1.6, power=0.12, license_cost_m=1.0, color="#6db3ff", edge=True),
    "io": dict(id="io", name="IO / 电源", area=2.5, power=0.04, license_cost_m=0.5, color="#8a93a6", edge=True),
}

STORAGE = {
    "ufs22": dict(id="ufs22", name="UFS 2.2", seq_read=1.2, cost=2.0, fluency=0.90,
                  note="低端够用；旗舰用它会被骂卡（P10 闪存门式的教训：存储不能混/降配）。"),
    "ufs31": dict(id="ufs31", name="UFS 3.1", seq_read=2.1, cost=4.0, fluency=0.97,
                  note="提高顺序传输带宽；实际应用收益取决于访问模式。"),
    "ufs40": dict(id="ufs40", name="UFS 4.0", seq_read=4.2, cost=7.0, fluency=1.00,
                  note="旗舰标配；连续读写翻倍，相册/游戏加载更快。"),
}

NOCS = {
    "ring": dict(id="ring", name="环形总线", base_hops=3.2, latency_factor=0.97,
                 area_overhead=0.03, power_factor=0.85,
                 note="面积小、功耗低，核心多时延迟上升。适合 ≤6 核。",
                 evidence=[], confidence="high"),
    "mesh": dict(id="mesh", name="Mesh NoC", base_hops=2.1, latency_factor=0.99,
                 area_overhead=0.06, power_factor=1.0,
                 note="可扩展，8 核以上更稳，面积和布线开销更高。",
                 evidence=[], confidence="high"),
    "crossbar": dict(id="crossbar", name="全交叉开关", base_hops=1.0, latency_factor=1.0,
                     area_overhead=0.10, power_factor=1.25,
                     note="延迟最低，但面积/功耗随端口数平方增长。",
                     evidence=[], confidence="high"),
}

DRAMS = {
    "lpddr4x": dict(id="lpddr4x", name="LPDDR4X-4266", gbps=4266, channels=2,
                    efficiency=0.72, cost_per_channel=4.0, power_per_channel=0.15),
    "lpddr5": dict(id="lpddr5", name="LPDDR5-6400", gbps=6400, channels=4,
                   efficiency=0.75, cost_per_channel=5.5, power_per_channel=0.18),
    "lpddr5x": dict(id="lpddr5x", name="LPDDR5X-8533", gbps=8533, channels=4,
                    efficiency=0.78, cost_per_channel=6.5, power_per_channel=0.20),
    "lpddr5t": dict(id="lpddr5t", name="LPDDR5T-9600", gbps=9600, channels=4,
                    efficiency=0.79, cost_per_channel=7.5, power_per_channel=0.22),
    "lpddr6": dict(id="lpddr6", name="LPDDR6-16000", gbps=16000, channels=4,
                   efficiency=0.86, cost_per_channel=8.5, power_per_channel=0.24),
}

PACKAGES = {
    "pop": dict(id="pop", name="PoP 堆叠封装", rjc=0.35, cost=3.0, max_area=130,
                max_w=13.0, max_h=13.0,
                note="手机主流。内存叠在 SoC 上，省面积，散热一般。",
                evidence=[], confidence="high"),
    "fowlp": dict(id="fowlp", name="Fan-Out WLP", rjc=0.28, cost=6.0, max_area=160,
                  max_w=16.0, max_h=16.0,
                  note="更薄、更好的供电与散热，成本更高。",
                  evidence=[], confidence="medium"),
    "imc25d": dict(id="imc25d", name="2.5D 中介层", rjc=0.22, cost=26.0, max_area=320,
                   max_w=22.0, max_h=22.0,
                   note="可外挂 LPDDR 或 chiplet，适合笔记本/服务器。",
                   evidence=[], confidence="medium"),
}

COOLING = {
    "graphite": dict(id="graphite", name="石墨片", rca=7.5, cost=1.0,
                     note="低端机常见。持续功耗一高就烫手。",
                     evidence=[], confidence="medium"),
    "vc": dict(id="vc", name="VC 均热板", rca=5.2, cost=4.0,
               note="旗舰标配。3–5W 持续功耗的关键。",
               evidence=[], confidence="medium"),
    "vcPro": dict(id="vcPro", name="VC + 石墨烯", rca=4.3, cost=7.0,
                  note="更薄的机身也能压住 5W。",
                  evidence=[], confidence="medium"),
    "laptop": dict(id="laptop", name="笔记本风扇", rca=2.6, cost=12.0,
                   note="轻薄本散热，允许 15–25W 持续。",
                   evidence=[], confidence="medium"),
    "server": dict(id="server", name="服务器风冷", rca=1.2, cost=20.0,
                   note="机架风冷，持续功耗不再是瓶颈。",
                   evidence=[], confidence="medium"),
}

METAL_STACKS = {
    "dense": dict(id="dense", name="高密度堆栈", area_overhead=0.10, wire_power=1.15,
                  freq_factor=0.98, cost_m=2.0,
                  note="层数少、成本低，但全局布线电阻大。"),
    "balanced": dict(id="balanced", name="均衡堆栈", area_overhead=0.14, wire_power=1.00,
                     freq_factor=1.00, cost_m=4.0,
                     note="默认选择，面积、频率、功耗平衡。"),
    "perf": dict(id="perf", name="性能堆栈", area_overhead=0.20, wire_power=0.85,
                 freq_factor=1.04, cost_m=6.0,
                 note="更多厚金属层，降低 RC 延迟；面积和 mask 成本上升。"),
}

for _npu in NPUS.values():
    _npu.update(precision="INT8", sparsity="dense", operations_per_mac=2,
                parameter_basis="teaching-estimate")
for _dram in DRAMS.values():
    _dram.update(channel_width_bits=16, data_rate_unit="MT/s")

for _group in (GPUS, NPUS, FIXED_BLOCKS, STORAGE, NOCS, DRAMS, PACKAGES, COOLING, METAL_STACKS):
    for _item in _group.values():
        _item["parameter_basis"] = "game_assumption"

from copy import deepcopy as _deepcopy
for _id,_name,_base,_vendor,_year in [
    ('adreno640','Adreno 640','maliG76','Qualcomm',2019),
    ('adreno660','Adreno 660','g715','Qualcomm',2021),
    ('adreno740','Adreno 740','g720','Qualcomm',2022),
    ('adreno750','Adreno 750','g720','Qualcomm',2023),
    ('adreno_gen5','Adreno · 8 Elite Gen5','adreno850','Qualcomm',2025),
    ('adreno_gen6','Adreno · 8 Elite Extreme Gen6','adreno850','Qualcomm',2026),
    ('apple_a17gpu','Apple A17 Pro GPU','appleGpu','Apple',2023),
    ('apple_a19gpu','Apple A19 Pro GPU','appleGpu','Apple',2025),
    ('apple_a20gpu','Apple A20 Pro GPU','appleGpu','Apple',2026),
    ('apple_m1gpu','Apple M1 GPU','appleGpu','Apple',2020),
    ('apple_m4gpu','Apple M4 GPU','appleGpu','Apple',2024),
    ('apple_m5gpu','Apple M5 GPU','appleGpu','Apple',2025),
    ('powervr_g6','PowerVR · Tensor G6 model','powervrCXT','Imagination',2026),
]:
    _g=_deepcopy(GPUS[_base]);_g.update(id=_id,name=_name,vendor=_vendor,year=_year,
        note='独立代际身份；PPA与教学分区系数未校准，不能当作真实GPU ISA或计算单元数。')
    GPUS[_id]=_g
GPUS['apple_a20gpu'].update(default_units=7,max_units=7,min_units=7,evidence=['apple_a20pro'])
GPUS['adreno_gen6']['evidence']=['qcom_8ee6']
GPUS['adreno660']['evidence']=['qcom_sd888']


def get_gpu(design):
    from ..engine.ip_library import block_model
    from ..engine.core_bundle import template_model
    return block_model(design,'gpu',template_model(design,'gpu',design.gpu_id) or GPUS.get(design.gpu_id))


def get_npu(design):
    from ..engine.ip_library import block_model
    from ..engine.core_bundle import template_model
    return block_model(design,'npu',template_model(design,'npu',design.npu_id) or NPUS.get(design.npu_id))


def get_isp(design):
    from ..engine.ip_library import block_model
    from ..engine.core_bundle import template_model
    return block_model(design,'isp',template_model(design,'isp','isp') or FIXED_BLOCKS.get('isp'))
