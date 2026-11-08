"""公开资料参考与未核验的前瞻条目：只用于图鉴/对照。

数据来自公开拆解、发布会与测试的估算中值。置信度标在每条记录里，
不是官方签核数据。
"""
from __future__ import annotations

BLUEPRINTS = [
    dict(
        id="sd855", name="Snapdragon 855", vendor="Qualcomm", year=2019, node="n7",
        die_area=73, cpu="1×A76@2.84 + 3×A76@2.42 + 4×A55@1.80", gpu="Adreno 640",
        cache="L2 512KB/Core · L3 2MB", scores=dict(st=950, mt=2700, gpu=480),
        confidence="medium", evidence=[],
        insight=('1+3+4 配置将同一类性能核分成两个频率档位。高频核处理短时响应，其余核心承担并行任务；能效还取决于电压、调度和整机散热。'),
        layout=[
            dict(k="big", label="A76", x=3, y=4, w=22, h=26),
            dict(k="big", label="A76", x=27, y=4, w=22, h=26),
            dict(k="mid", label="A76×2", x=3, y=32, w=46, h=20),
            dict(k="little", label="A55×4", x=3, y=54, w=46, h=18),
            dict(k="gpu", label="Adreno 640", x=53, y=4, w=44, h=40),
            dict(k="npu", label="NPU", x=53, y=46, w=20, h=26),
            dict(k="modem", label="X24", x=75, y=46, w=22, h=26),
            dict(k="io", label="IO", x=3, y=74, w=94, h=20),
        ],
        build={'node': 'n7', 'cores': [('a76', 1, 0.512, 2.84), ('a76', 3, 0.512, 2.42), ('a55', 4, 0.256, 1.8)], 'l3': 2, 'gpu': ('maliG76', 12), 'npu': 'npu8', 'modem': 'modem4g', 'price': 45},
    ),
    dict(
        id="sd888", name="Snapdragon 888", vendor="Qualcomm", year=2021, node="n5",
        die_area=110, cpu="1×X1@2.84 + 3×A78@2.42 + 4×A55@1.80", gpu="Adreno 660",
        cache="L2 1MB/X · L3 4MB", scores=dict(st=1150, mt=3400, gpu=720),
        confidence="medium", evidence=[],
        insight=('Cortex-X1 提高了单核性能目标，也提高了峰值功耗。比较这一代产品时，应同时观察持续频率、整机散热和实测电压，不能把所有发热归因于一个制程名称。'),
        layout=[
            dict(k="big", label="X1", x=4, y=5, w=26, h=30),
            dict(k="mid", label="A78×3", x=32, y=5, w=28, h=30),
            dict(k="little", label="A55×4", x=4, y=38, w=28, h=22),
            dict(k="gpu", label="Adreno 660", x=62, y=5, w=34, h=46),
            dict(k="l3", label="L3", x=32, y=38, w=28, h=22),
            dict(k="npu", label="NPU", x=4, y=63, w=28, h=17),
            dict(k="isp", label="ISP", x=34, y=63, w=26, h=17),
            dict(k="modem", label="X60", x=62, y=54, w=34, h=26),
            dict(k="io", label="IO", x=4, y=83, w=92, h=12),
        ],
        build={'node': 'n5', 'cores': [('x1', 1, 1.0, 2.84), ('a78', 3, 0.512, 2.42), ('a55', 4, 0.256, 1.8)], 'l3': 4, 'gpu': ('g715', 11), 'npu': 'npu16', 'modem': 'modem5g', 'price': 90},
    ),
    dict(
        id="sd8g3", name="Snapdragon 8 Gen 3", vendor="Qualcomm", year=2023, node="n4p",
        die_area=137, cpu="1×X4@3.30 + 3×A720@3.15 + 2×A720@2.96 + 2×A520@2.27",
        gpu="Adreno 750", cache="L2 2MB/X · L3 12MB", scores=dict(st=2200, mt=6800, gpu=1400),
        confidence="medium", evidence=[],
        insight=('1+5+2 配置提高了性能核占比。共享缓存与内存带宽决定这些核心在并行任务中的利用率；增加核心不保证同比例的加速。'),
        layout=[
            dict(k="big", label="X4", x=3, y=4, w=24, h=27),
            dict(k="mid", label="A720×2", x=28, y=4, w=25, h=27),
            dict(k="mid", label="A720×3", x=3, y=33, w=50, h=17),
            dict(k="l3", label="L3 12MB", x=3, y=52, w=50, h=13),
            dict(k="little", label="A520×2", x=3, y=67, w=24, h=14),
            dict(k="gpu", label="Adreno 750", x=56, y=4, w=41, h=43),
            dict(k="npu", label="NPU", x=56, y=49, w=19, h=32),
            dict(k="isp", label="ISP", x=77, y=49, w=20, h=15),
            dict(k="modem", label="X75", x=77, y=66, w=20, h=15),
            dict(k="io", label="IO", x=3, y=83, w=94, h=12),
        ],
        build={'node': 'n4p', 'cores': [('x4', 1, 2.0, 3.3), ('a720', 5, 0.512, 3.0), ('a520', 2, 0.256, 2.2)], 'l3': 12, 'gpu': ('g720', 12), 'npu': 'npu30', 'modem': 'modem5g', 'price': 150},
    ),
    dict(
        id="d9300", name="Dimensity 9300", vendor="MediaTek", year=2023, node="n4p",
        die_area=150, cpu="4×X4@3.25 + 4×A720@2.85", gpu="Immortalis-G720 MC12",
        cache="L2 1MB/X · L3 8MB", scores=dict(st=2100, mt=7500, gpu=1350),
        confidence="medium", evidence=[],
        insight=('四颗 Cortex-X4 与四颗 A720 组成全性能核配置。轻载可以通过降频和关闭空闲核心控制功耗，缺少小核并不直接等于待机功耗更高。'),
        layout=[
            dict(k="big", label="X4×2", x=3, y=4, w=30, h=30),
            dict(k="big", label="X4×2", x=35, y=4, w=30, h=30),
            dict(k="mid", label="A720×4", x=3, y=36, w=62, h=22),
            dict(k="l3", label="L3 8MB", x=3, y=60, w=62, h=12),
            dict(k="gpu", label="G720 MC12", x=68, y=4, w=29, h=40),
            dict(k="npu", label="APU", x=68, y=46, w=29, h=24),
            dict(k="isp", label="ISP", x=68, y=72, w=14, h=12),
            dict(k="modem", label="M80", x=83, y=72, w=14, h=12),
            dict(k="io", label="IO", x=3, y=84, w=94, h=11),
        ],
        build={'node': 'n4p', 'cores': [('x4', 4, 1.0, 3.25), ('a720', 4, 0.512, 2.85)], 'l3': 8, 'gpu': ('g720', 12), 'npu': 'npu30', 'modem': 'modem5g', 'price': 140},
    ),
    dict(
        id="d9400", name="Dimensity 9400", vendor="MediaTek", year=2024, node="n3e",
        die_area=150, cpu="1×X925@3.62 + 3×X4@3.30 + 4×A725@2.90",
        gpu="Immortalis-G925 MC12", cache="L2 2MB/X · L3 12MB",
        scores=dict(st=2800, mt=9000, gpu=1600),
        confidence="medium", evidence=[],
        insight=('1 颗 X925、3 颗 X4 和 4 颗 A725 都属于性能核，没有 A5 系列效率核。新节点、缓存与调度共同影响能效，应在相同负载与功耗下比较。'),
        layout=[
            dict(k="big", label="X925", x=3, y=4, w=26, h=28),
            dict(k="big", label="X4×3", x=31, y=4, w=28, h=28),
            dict(k="mid", label="A725×4", x=3, y=34, w=56, h=20),
            dict(k="l3", label="L3 12MB", x=3, y=56, w=56, h=14),
            dict(k="gpu", label="G925 MC12", x=61, y=4, w=36, h=42),
            dict(k="npu", label="NPU 890", x=61, y=48, w=18, h=30),
            dict(k="isp", label="ISP", x=81, y=48, w=16, h=14),
            dict(k="modem", label="M90", x=81, y=64, w=16, h=14),
            dict(k="io", label="IO", x=3, y=84, w=94, h=11),
        ],
        build={'node': 'n3e', 'cores': [('x925', 1, 2.0, 3.62), ('x4', 3, 2.0, 3.3), ('a725', 4, 0.512, 2.9)], 'l3': 12, 'gpu': ('g925', 12), 'npu': 'npu30', 'modem': 'modem5g', 'price': 160},
    ),
    dict(
        id="a17pro", name="Apple A17 Pro", vendor="Apple", year=2023, node="n3e",
        die_area=103, cpu="2×Everest@3.78 + 4×Sawtooth@2.11", gpu="Apple GPU 6-core",
        cache="L2 4MB/P-core · SLC 24MB", scores=dict(st=2900, mt=7200, gpu=1700),
        confidence="low", evidence=[],
        insight=('两颗性能核和四颗效率核服务于不同负载。CPU 核数量不能直接代表单核能力；缓存、前端、后端和内存系统共同决定实际吞吐。'),
        layout=[
            dict(k="big", label="P×2", x=3, y=4, w=30, h=26),
            dict(k="mid", label="E×4", x=35, y=4, w=26, h=26),
            dict(k="l3", label="SLC 24MB", x=3, y=32, w=58, h=16),
            dict(k="gpu", label="GPU 6C", x=63, y=4, w=34, h=44),
            dict(k="npu", label="NPU 16C", x=3, y=50, w=28, h=18),
            dict(k="isp", label="ISP", x=33, y=50, w=28, h=18),
            dict(k="modem", label="5G", x=63, y=50, w=34, h=18),
            dict(k="io", label="IO", x=3, y=70, w=94, h=24),
        ],
        build={'node': 'n3e', 'cores': [('everest', 2, 4.0, 3.78), ('sawtooth', 4, 1.0, 2.11)], 'l3': 24, 'gpu': ('appleGpu', 6), 'npu': 'npu30', 'modem': 'modem5g', 'price': 180},
    ),
    dict(
        id="m1", name="Apple M1", vendor="Apple", year=2020, node="n5",
        die_area=119, cpu="4×Firestorm@3.20 + 4×Icestorm@2.06", gpu="Apple GPU 8-core",
        cache="L2 12MB cluster · SLC 16MB", scores=dict(st=2300, mt=8500, gpu=1900),
        confidence="medium", evidence=[],
        insight=('统一内存让 CPU 与 GPU 共享同一物理内存系统，减少部分数据复制。收益与带宽、软件模型和缓存一致性有关，不表示所有程序都会加速。'),
        layout=[
            dict(k="big", label="Firestorm×4", x=3, y=3, w=30, h=26),
            dict(k="mid", label="Icestorm×4", x=35, y=3, w=22, h=26),
            dict(k="l3", label="SLC", x=3, y=31, w=54, h=10),
            dict(k="gpu", label="GPU 8C", x=59, y=3, w=38, h=50),
            dict(k="npu", label="NPU", x=3, y=43, w=22, h=16),
            dict(k="isp", label="ISP", x=27, y=43, w=30, h=16),
            dict(k="modem", label="IO/PHY", x=59, y=55, w=38, h=12),
            dict(k="io", label="Memory PHY", x=3, y=61, w=94, h=12),
        ],
        build={'node': 'n5', 'cores': [('firestorm', 4, 3.0, 3.2), ('icestorm', 4, 1.0, 2.06)], 'l3': 16, 'gpu': ('appleGpu', 8), 'npu': 'npu16', 'modem': 'modem4g', 'price': 200},
    ),
    dict(
        id="m4", name="Apple M4", vendor="Apple", year=2024, node="n3e",
        die_area=165, cpu="4×P-core@4.40 + 6×E-core@2.89", gpu="Apple GPU 10-core",
        cache="L2 4MB/P · SLC 28MB", scores=dict(st=3800, mt=14500, gpu=2600),
        confidence="low", evidence=[],
        insight=('高频、缓存与内存系统需要一起评估。同一 M4 会用于不同散热条件的设备，不能把某一整机的持续性能视为所有产品的固定表现。'),
        layout=[
            dict(k="big", label="P×4", x=3, y=3, w=28, h=28),
            dict(k="mid", label="E×6", x=33, y=3, w=24, h=28),
            dict(k="l3", label="SLC", x=3, y=33, w=54, h=9),
            dict(k="gpu", label="GPU 10C", x=59, y=3, w=38, h=48),
            dict(k="npu", label="NPU 16C", x=3, y=44, w=24, h=16),
            dict(k="isp", label="媒体引擎", x=29, y=44, w=28, h=16),
            dict(k="modem", label="IO", x=59, y=53, w=38, h=14),
            dict(k="io", label="Memory PHY", x=3, y=62, w=94, h=12),
        ],
        build={'node': 'n3e', 'cores': [('m4p', 4, 4.0, 4.4), ('sawtooth', 6, 1.0, 2.89)], 'l3': 28, 'gpu': ('appleGpu', 10), 'npu': 'npu45', 'modem': 'modem5g', 'price': 240},
    ),
    dict(
        id="xringO1", name="XRING O1（玄戒 O1）", vendor="Xiaomi", year=2025, node="n3e",
        die_area=109, cpu="2×X925@3.90 + 4×A725@3.40 + 2×A725@1.90 + 2×A520@1.80",
        gpu="Immortalis-G925 MC16", cache="L2 2MB/X · L3 16MB",
        scores=dict(st=3000, mt=9500, gpu=1700),
        confidence="low", evidence=[],
        insight=('公版 Arm CPU IP 仍需完成综合、布局布线和时序收敛。将 A725 分成频率组有助于调度取舍；物理实现后端与 CPU 微架构后端是两种不同含义。'),
        layout=[
            dict(k="big", label="X925×2", x=3, y=4, w=27, h=26),
            dict(k="mid", label="A725×2", x=32, y=4, w=24, h=26),
            dict(k="mid", label="A725×2", x=3, y=32, w=24, h=16),
            dict(k="little", label="A520×2", x=29, y=32, w=27, h=16),
            dict(k="l3", label="L3 16MB", x=3, y=50, w=53, h=13),
            dict(k="gpu", label="G925 MC16", x=59, y=4, w=38, h=42),
            dict(k="npu", label="NPU", x=59, y=48, w=18, h=26),
            dict(k="isp", label="ISP", x=79, y=48, w=18, h=12),
            dict(k="modem", label="5G", x=79, y=62, w=18, h=12),
            dict(k="io", label="IO", x=3, y=66, w=53, h=12),
        ],
        build={'node': 'n3e', 'cores': [('xringX925', 2, 2.0, 3.9), ('a725', 4, 0.512, 3.4), ('a725', 2, 0.512, 1.9), ('a520', 2, 0.256, 1.8)], 'l3': 16, 'gpu': ('g925', 16), 'npu': 'npu30', 'modem': 'modem5g', 'price': 130},
    ),
    dict(
        id="kirin9000s", name="Kirin 9000s", vendor="Huawei", year=2023, node="smicN2",
        die_area=107, cpu="1×Taishan@2.62 + 3×Taishan@2.15 + 4×A510@1.53",
        gpu="Maleoon 910", cache="L2 512KB · L3 4MB", scores=dict(st=700, mt=2500, gpu=600),
        confidence="low", evidence=[],
        insight=('可用工艺、IP 和供应链会限制设计空间。系统优化可以改善部分任务的体验，但不能消除面积、漏电和频率方面的物理约束。'),
        layout=[
            dict(k="big", label="Taishan", x=4, y=5, w=24, h=26),
            dict(k="mid", label="Taishan×3", x=30, y=5, w=28, h=26),
            dict(k="little", label="A510×4", x=4, y=34, w=30, h=18),
            dict(k="gpu", label="Maleoon", x=62, y=5, w=34, h=38),
            dict(k="l3", label="L3", x=30, y=34, w=28, h=18),
            dict(k="npu", label="NPU", x=4, y=55, w=26, h=18),
            dict(k="isp", label="ISP", x=32, y=55, w=26, h=18),
            dict(k="modem", label="5G", x=62, y=46, w=34, h=27),
            dict(k="io", label="IO", x=4, y=76, w=92, h=18),
        ],
        build={'node': 'smicN2', 'cores': [('taishan', 1, 1.0, 2.62), ('taishan', 3, 0.512, 2.15), ('a510', 4, 0.256, 1.53)], 'l3': 4, 'gpu': ('maleoon', 8), 'npu': 'npu16', 'modem': 'modem5g', 'price': 100},
    ),
]

BLUEPRINT_BY_ID = {b["id"]: b for b in BLUEPRINTS}

BLUEPRINTS.extend([
    dict(
        id="sd8g2", name="Snapdragon 8 Gen 2", vendor="Qualcomm", year=2022, node="n4",
        die_area=137, cpu="1×X3@3.20 + 4×A715@2.80 + 3×A510@2.00", gpu="Adreno 740",
        cache="L2 1MB/X · L3 8MB", scores=dict(st=2000, mt=5500, gpu=1300),
        confidence="medium", evidence=[],
        insight=('性能核比例、共享缓存和 GPU 配置都影响最终表现。与上代比较时，需要统一设备散热、系统版本和测试负载。'),
        layout=[
            dict(k="big", label="X3", x=3, y=4, w=25, h=28),
            dict(k="mid", label="A715×4", x=30, y=4, w=28, h=28),
            dict(k="mid", label="A510×3", x=3, y=34, w=55, h=18),
            dict(k="l3", label="L3 8MB", x=3, y=54, w=55, h=13),
            dict(k="gpu", label="Adreno 740", x=60, y=4, w=37, h=43),
            dict(k="npu", label="NPU", x=60, y=49, w=17, h=30),
            dict(k="isp", label="ISP", x=79, y=49, w=18, h=14),
            dict(k="modem", label="X70", x=79, y=65, w=18, h=14),
            dict(k="io", label="IO", x=3, y=84, w=94, h=11),
        ],
    ),
    dict(
        id="exynos2400", name="Exynos 2400", vendor="Samsung", year=2024, node="sf4",
        die_area=144, cpu="1×X4@3.20 + 2×A720@2.90 + 3×A720@2.60 + 4×A520@1.95",
        gpu="Xclipse 940 (RDNA 3)", cache="L2 2MB/X · L3 8MB",
        scores=dict(st=2200, mt=6800, gpu=1500),
        confidence="low", evidence=[],
        insight=('CPU 配置与基于 AMD RDNA 技术的 GPU 是不同的设计选择。图形特性、驱动、带宽和散热都会影响游戏表现，架构品牌本身不决定结果。'),
        layout=[
            dict(k="big", label="X4", x=3, y=4, w=25, h=28),
            dict(k="mid", label="A720×2", x=30, y=4, w=24, h=28),
            dict(k="mid", label="A720×3", x=3, y=34, w=51, h=18),
            dict(k="little", label="A520×4", x=3, y=54, w=51, h=16),
            dict(k="gpu", label="Xclipse 940", x=57, y=4, w=40, h=44),
            dict(k="npu", label="NPU", x=57, y=50, w=19, h=30),
            dict(k="isp", label="ISP", x=78, y=50, w=19, h=14),
            dict(k="modem", label="5G", x=78, y=66, w=19, h=14),
            dict(k="io", label="IO", x=3, y=84, w=94, h=11),
        ],
    ),
])
BLUEPRINT_BY_ID = {b["id"]: b for b in BLUEPRINTS}

BLUEPRINT_BY_ID["sd8g2"]["build"] = dict(
    node="n4", cores=[("x3", 1, 1.0, 3.2), ("a715", 4, 0.512, 2.8), ("a510", 3, 0.256, 2.0)],
    l3=8, gpu=("g720", 12), npu="npu30", modem="modem5g", price=140)
BLUEPRINT_BY_ID["exynos2400"]["build"] = dict(
    node="sf4", cores=[("x4", 1, 2.0, 3.2), ("a720", 2, 0.512, 2.9),
                       ("a720", 3, 0.512, 2.6), ("a520", 4, 0.256, 1.95)],
    l3=8, gpu=("xclipse", 6), npu="npu30", modem="modem5g", price=150)

BLUEPRINTS.extend([
    dict(
        id="sd8elite5", name="Snapdragon 8 Elite Gen 5", vendor="Qualcomm", year=2025, node="n3p",
        die_area=128, die_aspect=1.0,
        cpu="2×Oryon 2@4.30 + 6×Oryon 2@3.60", gpu="Adreno 830",
        cache="L2 3MB/Oryon · L3 16MB", scores=dict(st=3400, mt=10500, gpu=2400),
        confidence="low", evidence=[],
        insight=('此条用于比较全性能核方案的频率、缓存与成本。各项参数为研究估算，性能与能效结论需要有明确测试设备、版本和功耗条件的原始资料。'),
        layout=[
            dict(k="big", label="Oryon×2", x=3, y=3, w=34, h=26),
            dict(k="mid", label="Oryon×6", x=3, y=31, w=34, h=24),
            dict(k="l3", label="L3 16MB", x=3, y=57, w=34, h=13),
            dict(k="gpu", label="Adreno 850", x=40, y=3, w=34, h=44),
            dict(k="npu", label="NPU", x=77, y=3, w=20, h=24),
            dict(k="isp", label="ISP", x=77, y=29, w=20, h=18),
            dict(k="modem", label="X85", x=40, y=49, w=34, h=16),
            dict(k="media", label="媒体", x=40, y=67, w=20, h=12),
            dict(k="display", label="显示", x=62, y=67, w=14, h=12),
            dict(k="dramphy", label="PHY", x=78, y=49, w=8, h=30),
            dict(k="io", label="IO", x=3, y=72, w=34, h=10),
        ],
    ),
    dict(
        id="d9500", name="Dimensity 9500", vendor="MediaTek", year=2025, node="n3p",
        die_area=145, die_aspect=1.19,
        cpu="1×C1-Ultra@4.21 + 3×C1-Premium@3.50 + 4×C1-Pro@2.70",
        gpu="Mali G1-Ultra MP12 @1.7GHz", cache="L2 4MB/C1 · L3 16MB · SLC 10MB",
        die_shot_url="https://kurnal-insights.com/uploads/MTK/mediatek-dimensity-9500-mt6993/D9500-Dieshot.thumb.webp",
        scores=dict(st=3300, mt=10500, gpu=2400),
        confidence="low", evidence=[],
        insight=('研究配置采用不同频率的性能核与分级共享缓存。公开资料中的缓存标注和 die 面积仍需核验；沙盒配置用于比较取舍。'),
        layout=[
            dict(k="big", label="C1-Ultra", x=3, y=3, w=26, h=26),
            dict(k="big", label="C1-Premium×3", x=31, y=3, w=30, h=26),
            dict(k="mid", label="C1-Pro×4", x=3, y=31, w=58, h=20),
            dict(k="l3", label="L3 16MB", x=3, y=53, w=58, h=15),
            dict(k="gpu", label="G1 Ultra MC20", x=63, y=3, w=34, h=42),
            dict(k="npu", label="NPU 990", x=63, y=47, w=18, h=30),
            dict(k="isp", label="ISP", x=83, y=47, w=14, h=14),
            dict(k="modem", label="M90", x=83, y=63, w=14, h=14),
            dict(k="media", label="媒体", x=3, y=70, w=28, h=12),
            dict(k="dramphy", label="PHY", x=33, y=70, w=8, h=12),
            dict(k="io", label="IO", x=43, y=70, w=18, h=12),
        ],
    ),
    dict(
        id="xringO3", name="XRING O3（玄戒 O3）", vendor="Xiaomi", year=2026, node="n3p",
        die_area=138.3, die_aspect=1.186,
        cpu="2×C1-Ultra@4.35 + 4×C1-Premium@3.60 + 4×C1-Pro@3.15",
        gpu="Mali G2 Ultra MP16 @1.6GHz", cache="L2 3MB/C1 · L3 16MB · SLC 16MB",
        die_shot_url="https://kurnal-insights.com/uploads/Xiaomi/xiaomi-xring-o3/Dieshot-V1-Xring-O3-12.81x10.80x0.16mm.thumb.webp",
        scores=dict(st=3200, mt=10000, gpu=2300),
        confidence="low", evidence=[],
        insight=('近期型号条目，原始资料尚未核验。这里的 CPU、缓存、面积和频率只能作为沙盒实验输入，不能据此断言已发布规格或厂商的物理实现能力。'),
        layout=[
            dict(k="big", label="C1-Ultra×2", x=3, y=3, w=28, h=26),
            dict(k="big", label="C1-Premium×4", x=33, y=3, w=30, h=26),
            dict(k="little", label="C1-Nano×2", x=3, y=31, w=28, h=15),
            dict(k="l3", label="L3 16MB", x=3, y=48, w=60, h=14),
            dict(k="gpu", label="G1 Ultra MC16", x=65, y=3, w=32, h=42),
            dict(k="npu", label="NPU", x=65, y=47, w=16, h=28),
            dict(k="isp", label="ISP", x=83, y=47, w=14, h=13),
            dict(k="modem", label="5G", x=83, y=62, w=14, h=13),
            dict(k="media", label="媒体", x=3, y=64, w=28, h=12),
            dict(k="dramphy", label="PHY", x=33, y=64, w=8, h=12),
            dict(k="io", label="IO", x=43, y=64, w=20, h=12),
        ],
    ),
    dict(
        id="kirin9500", name="Kirin 9500", vendor="Huawei", year=2025, node="n5",
        die_area=118, die_aspect=1.0,
        cpu="1×Taishan 2.0@3.20 + 3×Taishan 2.0@2.60 + 4×A510@1.80",
        gpu="Maleoon 920", cache="L2 1MB/Taishan · L3 8MB",
        scores=dict(st=2100, mt=6800, gpu=1500),
        confidence="low", evidence=[],
        insight=('原始规格与来源待核验。工艺、微架构、封装和系统优化对不同负载的影响并不等价，本条不提供已证实的性能排名。'),
        layout=[
            dict(k="big", label="Taishan×1", x=3, y=3, w=26, h=26),
            dict(k="mid", label="Taishan×3", x=31, y=3, w=30, h=26),
            dict(k="little", label="A510×4", x=3, y=31, w=58, h=18),
            dict(k="l3", label="L3 8MB", x=3, y=51, w=58, h=13),
            dict(k="gpu", label="Maleoon 920", x=63, y=3, w=34, h=40),
            dict(k="npu", label="NPU", x=63, y=45, w=17, h=24),
            dict(k="isp", label="ISP", x=82, y=45, w=15, h=12),
            dict(k="modem", label="5G", x=82, y=59, w=15, h=12),
            dict(k="media", label="媒体", x=3, y=66, w=28, h=12),
            dict(k="dramphy", label="PHY", x=33, y=66, w=8, h=12),
            dict(k="io", label="IO", x=43, y=66, w=18, h=12),
        ],
    ),
    dict(
        id="tensorG6", name="Google Tensor G6", vendor="Google", year=2026, node="n3p",
        die_area=128, die_aspect=1.0,
        cpu="1×C1-Ultra@4.11 + 4×C1-Pro@3.38 + 2×C1-Pro@2.20（7 核）",
        gpu="PowerVR CXTP-48-1536", cache="L2 2MB · L3 12MB",
        scores=dict(st=1900, mt=6000, gpu=1400),
        confidence="low", evidence=[],
        insight=('部分配置来自未核验的前瞻资料。GPU 的发布时间不能直接推导游戏兼容性，实际表现还依赖驱动、API 支持和设备测试。'),
        layout=[
            dict(k="big", label="C1-Premium", x=3, y=3, w=25, h=25),
            dict(k="mid", label="C1-Pro×3", x=30, y=3, w=30, h=25),
            dict(k="little", label="C1-Nano×4", x=3, y=30, w=57, h=17),
            dict(k="l3", label="L3 12MB", x=3, y=49, w=57, h=13),
            dict(k="gpu", label="G1 Ultra MC12", x=62, y=3, w=35, h=38),
            dict(k="npu", label="TPU", x=62, y=43, w=18, h=28),
            dict(k="isp", label="ISP", x=82, y=43, w=15, h=13),
            dict(k="modem", label="Exynos 5400", x=82, y=58, w=15, h=13),
            dict(k="media", label="媒体", x=3, y=64, w=28, h=12),
            dict(k="dramphy", label="PHY", x=33, y=64, w=8, h=12),
            dict(k="io", label="IO", x=43, y=64, w=18, h=12),
        ],
    ),
    dict(
        id="a19pro", name="Apple A19 Pro", vendor="Apple", year=2025, node="n3p",
        die_area=105, die_aspect=1.0,
        cpu="2×A19 Pro P-core@4.30 + 4×Sawtooth@2.90", gpu="Apple GPU 6-core",
        cache="L2 4MB/P · SLC 24MB", scores=dict(st=4000, mt=10000, gpu=2600),
        confidence="low", evidence=[],
        insight=('性能核与效率核配置可用于研究不同负载的资源分配。页面数值为估算参考，单核排名与缓存细节需要原始测试和可靠拆解确认。'),
        layout=[
            dict(k="big", label="A19 Pro×2", x=3, y=3, w=31, h=28),
            dict(k="mid", label="Sawtooth×4", x=36, y=3, w=25, h=28),
            dict(k="l3", label="SLC 24MB", x=3, y=33, w=58, h=16),
            dict(k="gpu", label="GPU 6C", x=63, y=3, w=34, h=44),
            dict(k="npu", label="NPU 16C", x=3, y=51, w=28, h=18),
            dict(k="isp", label="ISP", x=33, y=51, w=28, h=18),
            dict(k="modem", label="5G", x=63, y=49, w=34, h=16),
            dict(k="media", label="媒体", x=3, y=71, w=30, h=12),
            dict(k="dramphy", label="PHY", x=35, y=71, w=8, h=12),
            dict(k="io", label="IO", x=45, y=71, w=18, h=12),
        ],
    ),
    dict(
        id="m5", name="Apple M5", vendor="Apple", year=2025, node="n3p",
        die_area=170, die_aspect=1.0,
        cpu="4×M5 P-core@4.60 + 6×Sawtooth@3.00", gpu="Apple GPU 10-core",
        cache="L2 4MB/P · SLC 32MB", scores=dict(st=4600, mt=16000, gpu=3000),
        confidence="low", evidence=[],
        insight=('CPU、GPU 和共享内存争用同一功耗与带宽预算。研究这一类 SoC 时，需要区分芯片型号、核心配置和具体设备的持续功耗限制。'),
        layout=[
            dict(k="big", label="M5 P×4", x=3, y=3, w=29, h=28),
            dict(k="mid", label="E×6", x=34, y=3, w=23, h=28),
            dict(k="l3", label="SLC 32MB", x=3, y=33, w=54, h=11),
            dict(k="gpu", label="GPU 10C", x=59, y=3, w=38, h=48),
            dict(k="npu", label="NPU 16C", x=3, y=46, w=24, h=18),
            dict(k="isp", label="媒体引擎", x=29, y=46, w=28, h=18),
            dict(k="modem", label="IO", x=59, y=53, w=38, h=14),
            dict(k="media", label="显示", x=3, y=66, w=24, h=10),
            dict(k="dramphy", label="PHY", x=29, y=66, w=8, h=10),
            dict(k="io", label="IO", x=39, y=66, w=18, h=10),
        ],
    ),
])
BLUEPRINT_BY_ID = {b["id"]: b for b in BLUEPRINTS}
BLUEPRINT_BY_ID["sd8elite5"]["build"] = dict(
    node="n3p", cores=[("oryon2", 2, 3.0, 4.3), ("oryon2", 6, 3.0, 3.6)],
    l3=16, gpu=("adreno850", 8), npu="npu45", modem="modem5g", price=165)
BLUEPRINT_BY_ID["d9500"]["build"] = dict(
    node="n3p", cores=[("c1_ultra", 1, 4.0, 4.21), ("c1_premium", 3, 4.0, 3.5),
                       ("c1_pro", 4, 2.0, 2.7)],
    l3=16, slc=10, gpu=("g1Ultra", 12), npu="npu60", modem="modem5g",
    dram="lpddr5x", price=165)
BLUEPRINT_BY_ID["xringO3"]["build"] = dict(
    node="n3p", cores=[("c1_ultra", 2, 3.0, 4.35), ("c1_premium", 4, 2.0, 3.6),
                       ("c1_pro", 4, 1.0, 3.15)],
    l3=16, slc=16, gpu=("g2Ultra", 16), npu="npu60", modem="modem5g",
    dram="lpddr6", price=145)
BLUEPRINT_BY_ID["kirin9500"]["build"] = dict(
    node="n5", cores=[("taishan2_5nm", 1, 1.0, 3.2), ("taishan2_5nm", 3, 1.0, 2.8),
                      ("a510", 4, 0.256, 1.5)],
    l3=8, gpu=("maleoon920", 8), npu="npu30", modem="modem5g", price=120)
BLUEPRINT_BY_ID["tensorG6"]["build"] = dict(
    node="n3p", cores=[("c1_ultra", 1, 3.0, 4.11), ("c1_pro", 4, 1.0, 3.38),
                       ("c1_pro", 2, 1.0, 2.20)],
    l3=12, gpu=("powervrCXT", 4), npu="npu45", modem="modem5g", price=130)
BLUEPRINT_BY_ID["a19pro"]["build"] = dict(
    node="n3p", cores=[("a19p", 2, 4.0, 4.3), ("sawtooth", 4, 1.0, 2.9)],
    l3=24, gpu=("appleGpu", 6), npu="npu45", modem="modem5g", price=190)
BLUEPRINT_BY_ID["m5"]["build"] = dict(
    node="n3p", cores=[("m5p", 4, 4.0, 4.6), ("sawtooth", 6, 1.0, 3.0)],
    l3=32, gpu=("appleGpu", 10), npu="npu45", modem="modem5g", price=260)

BLUEPRINT_BY_ID["xringO3"]["layout"] = [
    dict(k="isp", label="小米 ISP", x=2, y=3, w=22, h=20),
    dict(k="big", label="C1 Ultra×2", x=26, y=3, w=17, h=15),
    dict(k="mid", label="C1 Premium×4", x=45, y=3, w=22, h=20),
    dict(k="mid", label="C1 Pro×4", x=26, y=20, w=22, h=13),
    dict(k="l3", label="L3 16MB", x=26, y=35, w=25, h=10),
    dict(k="l3", label="SLC 16MB", x=2, y=25, w=22, h=12),
    dict(k="npu", label="NPU ×4", x=69, y=3, w=13, h=26),
    dict(k="npu", label="NPU L2", x=83, y=3, w=14, h=16),
    dict(k="gpu", label="Mali G2 Ultra MP16", x=2, y=47, w=64, h=35),
    dict(k="display", label="DPU/DSI", x=69, y=31, w=28, h=10),
    dict(k="media", label="媒体", x=69, y=43, w=18, h=9),
    dict(k="dramphy", label="LPDDR6 PHY", x=2, y=84, w=18, h=11),
    dict(k="dramphy", label="LPDDR6 PHY", x=80, y=55, w=17, h=15),
    dict(k="io", label="IO", x=22, y=84, w=58, h=11),
]
BLUEPRINT_BY_ID["d9500"]["layout"] = [
    dict(k="big", label="C1 Ultra", x=27, y=3, w=18, h=18),
    dict(k="mid", label="C1 Premium×3", x=47, y=3, w=22, h=18),
    dict(k="mid", label="C1 Pro×4", x=27, y=23, w=22, h=13),
    dict(k="l3", label="L3 16MB", x=27, y=38, w=30, h=10),
    dict(k="l3", label="SLC 10MB", x=3, y=23, w=21, h=12),
    dict(k="npu", label="NPU 990", x=3, y=3, w=21, h=18),
    dict(k="isp", label="ImageIQ 1190", x=71, y=3, w=26, h=14),
    dict(k="media", label="Video", x=71, y=19, w=26, h=10),
    dict(k="display", label="MiraVision", x=71, y=31, w=26, h=10),
    dict(k="gpu", label="Mali G1 Ultra MP12", x=3, y=47, w=56, h=35),
    dict(k="modem", label="M90 5G", x=62, y=53, w=21, h=16),
    dict(k="dramphy", label="LPDDR5X PHY", x=2, y=84, w=18, h=11),
    dict(k="dramphy", label="LPDDR5X PHY", x=85, y=44, w=14, h=24),
    dict(k="io", label="IO", x=22, y=84, w=60, h=11),
]

BLUEPRINTS.extend([
    dict(
        id="kirin9030", name="Kirin 9030", vendor="Huawei", year=2025, node="smicN2",
        die_area=141.7, die_aspect=1.184,
        cpu="Taishan 2.0 ×4 + A510 ×4", gpu="Maleoon 920",
        cache="L2 1MB · L3 8MB", scores=dict(st=2000, mt=6500, gpu=1500),
        confidence="low",
        evidence=[],
        die_shot_url="https://kurnal-insights.com/uploads/Huawei/hisilicon-hi36d0-kirin-9030/k9030-hi36D0-12.95x10.94x0.11.thumb.webp",
        insight='原始拆解引用尚未核验。面积只能结合工艺、宏单元和功能块分析，不能单凭尺寸推导封装形式或系统优化效果。',
        layout=[
            dict(k="big", label="Taishan×4", x=3, y=3, w=30, h=24),
            dict(k="little", label="A510×4", x=35, y=3, w=26, h=24),
            dict(k="l3", label="L3 8MB", x=3, y=29, w=58, h=12),
            dict(k="gpu", label="Maleoon 920", x=63, y=3, w=34, h=38),
            dict(k="npu", label="NPU", x=63, y=43, w=17, h=24),
            dict(k="isp", label="ISP", x=82, y=43, w=15, h=12),
            dict(k="modem", label="5G", x=82, y=57, w=15, h=12),
            dict(k="dramphy", label="PHY", x=3, y=43, w=8, h=26),
            dict(k="io", label="IO", x=13, y=43, w=46, h=26),
        ],
    ),
    dict(
        id="kirin9050", name="Kirin 9050", vendor="Huawei", year=2026, node="smicN2",
        die_area=120.6, die_aspect=1.027,
        cpu="Taishan 3.0 ×4 + A510 ×4", gpu="Maleoon 930",
        cache="L2 1MB · L3 8MB", scores=dict(st=2300, mt=7500, gpu=1700),
        confidence="low",
        evidence=[],
        die_shot_url="https://kurnal-insights.com/uploads/Huawei/hisilicon-hi36e0-kirin-9050/K9050-Hi36E0-Logic-Die.thumb.webp",
        insight='近期型号与参数待核验。面积变小可能来自节点、功能删减、宏单元布局等多种原因，本作不从一个面积值推断原因。',
        layout=[
            dict(k="big", label="Taishan 3.0×4", x=3, y=3, w=30, h=24),
            dict(k="little", label="A510×4", x=35, y=3, w=26, h=24),
            dict(k="l3", label="L3 8MB", x=3, y=29, w=58, h=12),
            dict(k="gpu", label="Maleoon 930", x=63, y=3, w=34, h=38),
            dict(k="npu", label="NPU", x=63, y=43, w=17, h=24),
            dict(k="isp", label="ISP", x=82, y=43, w=15, h=12),
            dict(k="modem", label="5G", x=82, y=57, w=15, h=12),
            dict(k="dramphy", label="PHY", x=3, y=43, w=8, h=26),
            dict(k="io", label="IO", x=13, y=43, w=46, h=26),
        ],
    ),
    dict(
        id="sd8elite6", name="Snapdragon 8 Elite Extreme Gen6", vendor="Qualcomm", year=2026,
        node="n2p", die_area=133.2, die_aspect=1.153,
        cpu="2×Oryon 3@4.6 + 6×Oryon 3@3.6", gpu="Adreno 850",
        cache="L2 3MB · L3 16MB", scores=dict(st=3700, mt=11500, gpu=2700),
        confidence="low", evidence=[],
        die_shot_url="https://kurnal-insights.com/uploads/Qualcomm/qualcomm-8elite-extreme-gen6sm8975/SM8975.thumb.webp",
        insight=('近期型号与评测引用尚未核验。旧版关于黑屏、能效倒退和市场排名的结论已撤下；沙盒参数不构成对真实产品可靠性的评价。'),
        layout=[
            dict(k="big", label="Oryon×2", x=3, y=3, w=32, h=25),
            dict(k="mid", label="Oryon×6", x=3, y=30, w=32, h=20),
            dict(k="l3", label="L3 16MB", x=3, y=52, w=32, h=12),
            dict(k="gpu", label="Adreno 850", x=38, y=3, w=36, h=43),
            dict(k="npu", label="NPU", x=77, y=3, w=20, h=24),
            dict(k="isp", label="ISP", x=77, y=29, w=20, h=18),
            dict(k="modem", label="X90", x=38, y=49, w=36, h=16),
            dict(k="dramphy", label="PHY", x=77, y=49, w=8, h=28),
            dict(k="io", label="IO", x=3, y=68, w=70, h=10),
        ],
    ),
    dict(
        id="a20pro", name="Apple A20 Pro", vendor="Apple", year=2026, node="n2",
        die_area=98.8, die_aspect=0.648,
        cpu="2×A19 Pro P-core@4.3 + 4×Sawtooth@2.9", gpu="Apple GPU 6-core",
        cache="L2 4MB/P · SLC 24MB", scores=dict(st=4200, mt=10500, gpu=2800),
        confidence="low", evidence=[],
        die_shot_url="https://kurnal-insights.com/uploads/Apple/apple-a20-pro/A20Pro-8.00x12.35x0.67.thumb.webp",
        insight='近期型号与 die 尺寸待核验。此条仅保留为前瞻沙盒配置，不作为真实拆解或公开跑分记录。',
        layout=[
            dict(k="big", label="P×2", x=3, y=3, w=34, h=28),
            dict(k="mid", label="E×4", x=3, y=33, w=34, h=22),
            dict(k="l3", label="SLC 24MB", x=39, y=3, w=26, h=18),
            dict(k="gpu", label="GPU 6C", x=67, y=3, w=30, h=38),
            dict(k="npu", label="NPU", x=39, y=23, w=26, h=18),
            dict(k="isp", label="ISP", x=67, y=43, w=30, h=14),
            dict(k="modem", label="5G", x=3, y=57, w=34, h=14),
            dict(k="dramphy", label="PHY", x=39, y=43, w=8, h=28),
            dict(k="io", label="IO", x=49, y=43, w=16, h=10),
        ],
    ),
    dict(
        id="tensorG4", name="Google Tensor G4", vendor="Google", year=2024, node="sf4",
        die_area=136.2, die_aspect=1.181,
        cpu="1×X4@3.1 + 3×A720@2.6 + 4×A520@1.9", gpu="Mali-G715 MC10",
        cache="L2 2MB · L3 8MB", scores=dict(st=2000, mt=6400, gpu=1400),
        confidence="low", evidence=[],
        die_shot_url="https://kurnal-insights.com/uploads/Google/google-tensor-g4/google-tensor-g4.thumb.webp",
        insight='CPU、GPU、影像与安全模块共享芯片面积。本文提供结构示意，模块面积比例需要实际 die shot 或可靠拆解支持。',
        layout=[
            dict(k="big", label="X4", x=3, y=3, w=26, h=26),
            dict(k="mid", label="A720×3", x=31, y=3, w=30, h=26),
            dict(k="little", label="A520×4", x=3, y=31, w=58, h=16),
            dict(k="l3", label="L3 8MB", x=3, y=49, w=58, h=12),
            dict(k="gpu", label="G715 MC10", x=63, y=3, w=34, h=38),
            dict(k="npu", label="TPU", x=63, y=43, w=18, h=28),
            dict(k="isp", label="ISP", x=83, y=43, w=14, h=13),
            dict(k="modem", label="Exynos 5400", x=83, y=58, w=14, h=13),
            dict(k="dramphy", label="PHY", x=3, y=63, w=8, h=14),
            dict(k="io", label="IO", x=13, y=63, w=46, h=14),
        ],
    ),
])
BLUEPRINT_BY_ID = {b["id"]: b for b in BLUEPRINTS}

BLUEPRINT_BY_ID["kirin9030"]["build"] = dict(
    node="smicN2", cores=[("taishan2_5nm", 4, 1.0, 2.2), ("a510", 4, 0.256, 1.5)],
    l3=8, gpu=("maleoon920", 8), npu="npu30", modem="modem5g", price=110)
BLUEPRINT_BY_ID["kirin9050"]["build"] = dict(
    node="smicN2", cores=[("taishan2_5nm", 4, 1.0, 2.4), ("a510", 4, 0.256, 1.5)],
    l3=8, gpu=("maleoon920", 8), npu="npu30", modem="modem5g", price=120)
BLUEPRINT_BY_ID["sd8elite6"]["build"] = dict(
    node="n2p", cores=[("oryon3", 2, 3.0, 4.6), ("oryon3", 6, 3.0, 3.6)],
    l3=16, gpu=("adreno850", 8), npu="npu45", modem="modem5g", price=180)
BLUEPRINT_BY_ID["a20pro"]["build"] = dict(
    node="n2", cores=[("a19p", 2, 4.0, 4.3), ("sawtooth", 4, 1.0, 2.9)],
    l3=24, gpu=("appleGpu", 6), npu="npu45", modem="modem5g", price=200)
BLUEPRINT_BY_ID["tensorG4"]["build"] = dict(
    node="sf4", cores=[("x4", 1, 2.0, 3.1), ("a720", 3, 0.512, 2.6), ("a520", 4, 0.256, 1.9)],
    l3=8, gpu=("g715", 10), npu="npu30", modem="modem5g", price=120)

_DIE_SHOT_URLS = {
    "sd8g3": "/uploads/Qualcomm/qualcomm-snapdragon-8gen3/SM8650.thumb.webp",
    "d9300": "/uploads/MTK/mediatek-dimensity-9300-mt6989/D9300-mt6989.thumb.webp",
    "d9400": "/uploads/MTK/mediatek-dimensity-9400-mt6991/MT6991-mt6991.thumb.webp",
    "a17pro": "/uploads/Apple/apple-a17pro-apl1v02/a17pro.thumb.webp",
    "m1": "/uploads/Apple/Apple%20M/M1Pro.thumb.webp",
    "m4": "/uploads/Apple/Apple%20M/M4.thumb.webp",
    "xringO1": "/uploads/Xiaomi/xiaomi-xring-o1/Xring-O1.thumb.webp",
    "kirin9000s": "/uploads/Huawei/hisilicon-hi36a0v120-s-kirin-9000s/Hi36A0V120.thumb.webp",
}
for _bid, _u in _DIE_SHOT_URLS.items():
    if _bid in BLUEPRINT_BY_ID:
        BLUEPRINT_BY_ID[_bid]["die_shot_url"] = "https://kurnal-insights.com" + _u

BLUEPRINTS.extend([
    dict(
        id="d9600pro", name="Dimensity 9600 Pro", vendor="MediaTek", year=2026, node="n2",
        die_area=134.0, die_aspect=0.818,
        cpu="2×C2-Ultra@4.55 + 3×C2-Pro@4.35",
        gpu="Mali-G2 Ultra MP12 @1.8GHz", cache="L2 4MB/C2 · L3 16MB · SLC 10MB",
        die_shot_url="https://kurnal-insights.com/uploads/MTK/mediatek-dimensity-9600-pro-mt6995/D9600-Pro-MT6995Z-10.47x12.80x0.15mm.thumb.webp",
        scores=dict(st=3500, mt=10800, gpu=2500),
        confidence="low", evidence=[],
        insight=('近期型号、CPU 命名、制程和 die shot 引用待核验。不能将营销节点名称当作晶体管的实际线宽，也不能由节点数字直接推导能效。'),
        layout=[
            dict(k="big", label="C2 Ultra×2", x=34, y=12, w=36, h=14),
            dict(k="mid", label="C2 Pro×3", x=34, y=3, w=36, h=9),
            dict(k="l3", label="L3 16MB", x=36, y=28, w=28, h=10),
            dict(k="l3", label="SLC 10MB", x=28, y=48, w=40, h=12),
            dict(k="gpu", label="G2 Ultra MP12", x=3, y=55, w=50, h=29),
            dict(k="npu", label="NPU 1090", x=3, y=3, w=26, h=22),
            dict(k="isp", label="ImageIQ 1290", x=72, y=10, w=25, h=16),
            dict(k="display", label="MiraVision", x=72, y=28, w=25, h=10),
            dict(k="modem", label="M90 5G", x=72, y=62, w=25, h=16),
            dict(k="media", label="Video", x=72, y=40, w=25, h=9),
            dict(k="dramphy", label="LPDDR5X", x=3, y=86, w=30, h=9),
            dict(k="dramphy", label="LPDDR5X", x=80, y=30, w=16, h=24),
            dict(k="io", label="IO", x=35, y=86, w=45, h=9),
        ],
    ),
    dict(
        id="kirin9050pro", name="Kirin 9050 Pro", vendor="Huawei", year=2026, node="smicN2",
        die_area=120.6, die_aspect=1.027,
        cpu="4×Taishan 3.0@2.80 + 4×A510@1.80", gpu="Maleoon 930",
        cache="L2 1MB · L3 8MB", scores=dict(st=2100, mt=6800, gpu=1500),
        confidence="low", evidence=[],
        die_shot_url="https://kurnal-insights.com/uploads/Huawei/hisilicon-hi36e0-kirin-9050/K9050-Hi36E0-Logic-Die.thumb.webp",
        insight=('原始显微与封装资料待核验。旧版的“逻辑折叠”与性能结论不具备已确认的证据；3D 集成需要分别分析互连、热路径和组合良率。'),
        layout=[
            dict(k="big", label="Taishan 3.0×4", x=3, y=3, w=32, h=26),
            dict(k="little", label="A510×4", x=37, y=3, w=24, h=26),
            dict(k="l3", label="L3 8MB", x=3, y=31, w=58, h=12),
            dict(k="gpu", label="Maleoon 930", x=63, y=3, w=34, h=40),
            dict(k="npu", label="NPU", x=63, y=45, w=17, h=24),
            dict(k="isp", label="ISP", x=82, y=45, w=15, h=12),
            dict(k="modem", label="5G", x=82, y=59, w=15, h=12),
            dict(k="dramphy", label="PHY", x=3, y=45, w=8, h=26),
            dict(k="io", label="IO", x=13, y=45, w=46, h=26),
        ],
    ),
    dict(
        id="xringO100", name="XRING O100", vendor="Xiaomi", year=2026, node="n3p",
        die_area=95, die_aspect=1.0,
        cpu="2×C1-Ultra@4.00 + 4×C1-Pro@3.20", gpu="Mali G2 Ultra MP8 @1.6GHz",
        cache="L2 2MB · L3 12MB", scores=dict(st=3000, mt=8500, gpu=1800),
        confidence="low", evidence=[],
        insight=('三层堆叠与混合键合的原始引用待核验。此条不证明真实产品采用这些技术；本作 Chiplet 模型也不包含 TSV 或混合键合的物理实现。'),
        layout=[
            dict(k="big", label="C1-Ultra×2", x=3, y=3, w=28, h=24),
            dict(k="mid", label="C1-Pro×4", x=33, y=3, w=30, h=24),
            dict(k="l3", label="L3 12MB", x=3, y=29, w=60, h=12),
            dict(k="gpu", label="G2 Ultra MP8", x=65, y=3, w=32, h=36),
            dict(k="npu", label="NPU", x=65, y=41, w=16, h=24),
            dict(k="isp", label="ISP", x=83, y=41, w=14, h=12),
            dict(k="modem", label="5G", x=83, y=55, w=14, h=12),
            dict(k="dramphy", label="PHY/TSV", x=3, y=43, w=14, h=22),
            dict(k="io", label="IO", x=19, y=43, w=44, h=22),
        ],
    ),
])
BLUEPRINT_BY_ID = {b["id"]: b for b in BLUEPRINTS}
BLUEPRINT_BY_ID["d9600pro"]["build"] = dict(
    node="n2", cores=[("c2_ultra", 2, 4.0, 4.55), ("c2_pro", 3, 2.0, 4.35)],
    l3=16, slc=10, gpu=("g2Ultra", 12), npu="npu60", modem="modem5g",
    dram="lpddr5x", price=175)

# 证据类型与内容核验是两回事。保留遗留研究输入，不把近期低置信条目当作已确认规格。
for _bp in BLUEPRINTS:
    _bp["data_status"] = "unverified" if _bp.get("confidence") == "low" or _bp["year"] >= 2026 else "reference_estimate"
    _bp["score_basis"] = "approximate-reference"
BLUEPRINT_BY_ID["kirin9050pro"]["build"] = dict(
    node="smicN2", cores=[("taishan2", 4, 1.0, 2.8), ("a510", 4, 0.256, 1.8)],
    l3=8, gpu=("maleoon920", 8), npu="npu30", modem="modem5g", price=130)
BLUEPRINT_BY_ID["xringO100"]["build"] = dict(
    node="n3p", cores=[("c1_ultra", 2, 3.0, 4.0), ("c1_pro", 4, 1.0, 3.2)],
    l3=12, gpu=("g2Ultra", 8), npu="npu30", modem="modem5g",
    price=140, chiplet=True)

BLUEPRINTS.append(
    dict(
        id="d9600m", name="Dimensity 9600M", vendor="MediaTek", year=2026, node="n2",
        die_area=134.0, die_aspect=0.818,
        cpu="2×C2-Ultra@4.65 + 3×C2-Pro@4.45（9600 Pro 超频版）",
        gpu="Mali-G2 Ultra MP12 @1.8GHz", cache="L2 4MB/C2 · L3 16MB · SLC 10MB",
        die_shot_url="https://kurnal-insights.com/uploads/MTK/mediatek-dimensity-9600-pro-mt6995/D9600-Pro-MT6995Z-10.47x12.80x0.15mm.thumb.webp",
        scores=dict(st=3600, mt=11000, gpu=2500),
        confidence="low", evidence=[],
        insight=('型号与频率配置待核验。调整已有设计的频率档位仍需重新检查电压、功耗和可出售比例，本条不对真实产品作“超频马甲”的判断。'),
        layout=[
            dict(k="big", label="C2 Ultra×2", x=34, y=12, w=36, h=14),
            dict(k="mid", label="C2 Pro×3", x=34, y=3, w=36, h=9),
            dict(k="l3", label="L3 16MB", x=36, y=28, w=28, h=10),
            dict(k="l3", label="SLC 10MB", x=28, y=48, w=40, h=12),
            dict(k="gpu", label="G2 Ultra MP12", x=3, y=55, w=50, h=29),
            dict(k="npu", label="NPU 1090", x=3, y=3, w=26, h=22),
            dict(k="isp", label="ImageIQ 1290", x=72, y=10, w=25, h=16),
            dict(k="modem", label="M90 5G", x=72, y=62, w=25, h=16),
            dict(k="dramphy", label="LPDDR5X", x=3, y=86, w=30, h=9),
            dict(k="io", label="IO", x=35, y=86, w=45, h=9),
        ],
    )
)
BLUEPRINT_BY_ID = {b["id"]: b for b in BLUEPRINTS}
BLUEPRINT_BY_ID["d9600m"]["build"] = dict(
    node="n2", cores=[("c2_ultra", 2, 4.0, 4.65), ("c2_pro", 3, 2.0, 4.45)],
    l3=16, slc=10, gpu=("g2Ultra", 12), npu="npu60", modem="modem5g",
    dram="lpddr5x", price=175)

for _bp in BLUEPRINTS:
    _bp["parameter_basis"] = "game_assumption"
    _bp["data_status"] = "unverified"
    _bp.pop("die_shot_url", None)
BLUEPRINT_BY_ID["m1"]["evidence"] = ["apple_m1"]
BLUEPRINT_BY_ID["m4"]["evidence"] = ["apple_m4"]
