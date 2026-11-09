# 当前模型与计算边界

当前开发游戏 `0.1.0-alpha.6`，模型 `analytic-v0.9+smt-rescue-observatory-v1`。以下公式解释SoC教学引擎的行为，不是工艺库参数或真实签核模型。长度用 mm、面积用 mm²、频率用 GHz、功耗用 W；单颗费用为 USD，研发、营收和利润为百万 USD。性能分数是 SP 模型分。

## 逻辑、SRAM 与物理实现

```
ratio = target.area_scale / reference.area_scale
logic_area = ip.logic_area × ratio × impl_area_factor
private_L2_area = L2_MB × target.sram_mb
shared_L2_area = group_L2_MB × target.sram_mb × (0.80 + 0.04 × core_count)
Fmax_mean = reference_Fmax × target.freq_scale/reference.freq_scale × impl_freq_factor × metal.freq_factor
```

`sram_mb` 已是目标节点的 mm²/MB，不能再次乘逻辑节点倍率。共享 L2 容量是整组总量。共享方案的附加因子是教学用交叉连接开销，不是 CACTI 的实际输出。

HD/SD/HP、ULVT/LVT/SVT/HVT、面积/时序偏向共同改变面积、频率、动态功耗与漏电。频率来自参数模型，不是关键路径提取。ISA 本身不固定增加 4% 面积。

## 功耗与热

```
fr = clock / mean_Fmax
V = 0.55 + 0.37 × fr^1.6
Pdyn ∝ reference_power × fr × V² × node_factor × implementation_factor
Pleak ∝ area_ratio × V × node_leak_factor × VT_factor × 2^((T−25)/75)
```

这些参数只表示趋势。电压、活动因子、温度、频率与芯片工作模式在实际设备中都需要测量或提取。

```
Rtotal = Rjc(package) + Rca(device)
Pskin = max(0.3, (skin_limit − ambient) / Rca)
Ptj = max(0.5, (105 − ambient) / Rtotal)
Psustain = min(Pskin, Ptj)
Pburst = min((118 − ambient)/Rtotal, max(3.2 × Psustain, Psustain + 2))
```

持续模式通过二分求频率，并以阻尼迭代耦合结温和 CPU 漏电。峰值仍使用 85°C 参考漏电；这是保留的简化，不能预测峰值维持时间。达到最低缩放后功耗仍可能超过热预算，此时签核的机身温度检查可继续阻塞。

`Tj = ambient + Psustain_actual × Rtotal`；局部热点在包平均温度上叠加功率密度代理值，并随持续频率缩放。SoC持续性能模型不含热容、多节点瞬态RC网络或真实材料参数。独立功耗/热实验室另有单节点热容与瞬态RC，不能把它自动当作SoC的瞬态结果。功率密度图不是绝对温度分布。

## 内存与工作负载

```
total_width_bits = x16_channels × 16
theoretical_GB/s = data_rate_MT/s × total_width_bits / 8000
effective_GB/s = theoretical_GB/s × efficiency
```

四个 x16 通道、8533 MT/s 对应 68.264 GB/s。通道数同时改变 PHY 面积、功耗和外部 DRAM 配套费用；容量只影响配套费用，不直接推导带宽或缓存命中率。

CPU 的异构算力以最快核归一：

```
effective_cores = sum(IPC_i × f_i × count_i) / max(IPC_i × f_i)
Amdahl_speedup = 1 / ((1−parallel_fraction) + parallel_fraction/effective_cores)
compute_ceiling = fastest_rate × sustained_scale × Amdahl_speedup
memory_ceiling = effective_GB/s × workload_intensity_op_per_DRAM_byte
achievable = min(compute_ceiling, memory_ceiling)
```

Gop/s 使用“每单位 IPC 对应一次抽象运算”的代理值，该SoC工作负载估算不含真实SIMD、程序trace或实际程序依赖；实验室单独执行玩家输入的汇编，并不为该工作负载式提供应用trace。它适合比较同一工作负载的方案，不等于 GFLOPS 或实机跑分。共享缓存容量/工作集容量只作为容量指标显示，不据此伪造命中率。

CPU ST/MT 的旧 SP 模型继续通过 IPC、缓存、频率、共享资源、带宽与热预算估算。GPU 的 MC、WGP、Slice、CU 不能跨架构统一比较；驱动系数是教学假设。NPU 的 TOPS 档位约定为稠密 INT8、每 MAC 两次运算。AI 综合分混合 NPU 与 GPU 能力，不能称为 TOPS。

## 工程检查

- 相对 Fmax：TT ×1.00、SS ×0.88、FF ×1.06；标签中的温压只是情景描述，没有独立 SPICE 温压模型。
- 相对均值频率裕量：`1 − requested_clock/(mean_Fmax × corner_factor)`。
- 所选角落的可分档门槛：目标不超过该均值的 110%；这不能保证每颗 die 达标。
- 验证规划完成度：`0.55 + 0.40 × verification_effort`；这是工程投入代理值，不是功能、代码或故障覆盖率。
- 电源等效电阻：`(0.014 − 0.010 × PDN_quality) × package_factor` Ω。
- `I = peak_power / estimated_Vdd`；`IR_drop = I × R`，教学上限 80mV。
- 验证投入与 PDN 投入增加 NRE；验证投入也降低游戏风险事件概率。

没有电源网络拓扑、瞬态电流、寄生参数、电迁移或真实形式验证输入。

## 晶圆、良率与成本

```
A_cm2 = die_area_mm2 / 100
Ydefect = ((1−exp(−A_cm2 × D0))/(A_cm2 × D0))² × maturity
bin = min_i NormalCDF((mean_Fmax_i − requested_clock_i)/(0.045 × mean_Fmax_i))
expected_good_dies = complete_sites × Ydefect × bin
die_cost = wafer_cost / expected_good_dies
```

频率档位最小可用率保留数值稳定下限 0.0001，取消旧版 5% 的乐观下限。完整 die 位点通过矩形四角是否位于半径 147mm 内计算；晶圆直径 300mm、边缘排除 3mm、划片槽 80µm。成本与晶圆视图共用几何函数。没有 reticle field、步进曝光、测试结构或实际 wafer map。

Chiplet 按加速器面积份额拆成两颗同节点 die。CPU 频率分档只作用于 CPU die；两颗 die 的成本分别相加，封装及组装增加费用，跨 die 性能与功耗仍使用固定代理值。展示中的逻辑总图不能代表真实多 die 排版。

`cost.total` 是芯片方案成本：裸 die、封装、测试、组装、外挂基带和 Chiplet 组装。
`cost.platform_total` 另加外部 DRAM、存储与散热。只有前者用于芯片方案的售价与毛利。尚未计入其它 RF、PMIC、主板、电池、渠道和供应链费用。

## 流片与市场

`valid` 保留为结构、IP 使用范围与设备约束检查；`signoff.ready` 才决定能否流片。它统一检查结构、研发预算、成本、机身温度、峰值功耗、验证规划、供电、所选角落及频率档位可用率。主窗口、工程验证页和签核按钮共享这些结果。

销量按价格弹性、模拟评分和口碑计算，最高为关卡基准市场的三倍；利润为销量乘单颗毛利再减 NRE。没有订单、产能、库存、时间推进或渠道系统。

功能异常是按 seed 抽取的游戏事件。热应力后的性能系数也只是游戏惩罚，不代表一年后硬件衰退或真实品牌故障概率。工程机/零售机差距为情景代理值，不假定折叠芯片必然经过更好的挑选。

## 来源

- [Amdahl](https://doi.org/10.1145/1465482.1465560)
- [Roofline](https://doi.org/10.1145/1498765.1498785)
- [Murphy](https://doi.org/10.1109/PROC.1964.3442)

上式良率函数作为游戏假设保留；Murphy目前只完成书目核验，不能声称这个具体公式已由论文正文确认。Roofline教学对应实际核对的2008年Berkeley报告，2009年期刊条目用于书目识别。文献类型不能证明本作参数经过校准。来源状态和逐项使用范围见[REFERENCES.md](REFERENCES.md)与[遗留审计](research/LEGACY_AUDIT.md)。

## 实验、复用IP与真实RTL

实验室的CPU功能解释器执行RV32I/M/Zbb、IA-32和AArch64整数子集。RV32和A64采用32位指令编码，IA-32采用可变长字节编码；都不从二进制取指。执行语义与异常限制详见[实验手册](LAB_MANUAL.md)。

通用资源调度器对功能轨迹建依赖图，模拟分派、发射、完成和顺序提交。结果值由顺序功能解释器预先产生，不包含分支推测、异常恢复、多hart内存模型或真实厂商流水线。回放显示提交后的架构状态；内部提交一致性不等于独立RTL验证。实验周期是模型周期，不是PDK得到的关键路径时间。

保存的CPU IP以固定加法/存储/加载任务的IPC映射到SoC模型分，IA-32标为32位x86。面积、功耗、Fmax来自资源参数公式，均标记`game_assumption`。GPU IP为SIMT计算实验，NPU为整数GEMM与有限阵列，ISP为RGGB基本图像流水线；实例化时采用相应教学PPA，并不自动生成RTL或完整驱动。

## 核心设计台的结构与估算

设计台把硬件和测试台分开。CPU端口上限限制每周期发射，顺序模式不越过最早未发射的指令，乱序模式可发射独立后继；共同宽度限制分派和提交，在途容量限制队列。Cache使用所选KiB/行长/路数。SMT的两个实际测试线程均分ROB，独立寄存器与地址空间，共享执行资源和缓存。MSHR最多16个，在途缓存行合并；独立load可重叠，store/FENCE维持线程内顺序。二位方向计数器每上下文256项，只影响解析后的恢复开销；没有错误路径执行、有限物理寄存器、store buffer、OS或一致性。

GPU每处理器单向量发射、发射间隔和ALU延迟由定义指定，独立驻留warp交错调度；FP32乘、加分别舍入，不是FMA。NPU按有限整数精度与累加器wrap执行稠密GEMM。ISP旁路移除对应模块和延迟，去马赛克旁路也移除两行缓冲，输出RAW灰度；量化始终存在。GPU/NPU/ISP均不重叠计算与传输，`transfer_cycles = ceil(bytes / (GB/s ÷ GHz))`。

以下设计台PPA系数是游戏假设，没有论文或PDK校准。旧实验资产保留历史映射；新资产从hardware重建：

- CPU逻辑面积：`1.4 + .20×width + .20×ALU + .0015×queue + .006×L1_KiB` mm²；乘除模块加`.25×ports`，Zbb加`.10`，乱序加`.30 + .001×queue`；第二上下文加`.08`，每额外MSHR加`.012`，二位方向预测加`.05`。全为未校准教学系数。
- CPU参考Fmax：`1000 / ((2200 + 50×width + 35×ALU + .3×queue) / pipeline + 70)` GHz。pipeline在时序器中只是前端填充周期，这个面积/频率函数不能证明真实级数或时序收敛。
- CPU参考功耗：`.4 + .10×width + .12×ALU + .03×logic_area` W。SoC IPC指数取固定套件总指令/总周期乘3并限于`.15..2.5`；不能把玩家选的单段有利程序用作普遍IPC或跨ISA排名。
- GPU每处理器面积：`.5 + .05×lane + .002×lane×resident_warps + .005×lane×latency` mm²；功耗`.1×GHz×lane/8` W。SoC吞吐指数由lane/间隔/时钟映射，未使用真实驱动、占用率或显存trace。
- NPU峰值：`2×rows×cols×GHz/1000`稠密整数TOPS，明确精度，每MAC两次运算。面积`.2 + .004×PE×(input_bits/8)² + .001×PE×acc_bits/32 + .002×scratchpad_KiB` mm²；功耗`.1 + .002×PE×GHz×input_bits/8` W。
- ISP面积：`.15 + .08×(enabled_modules+1)×parallel_pixels + .0001×max_width` mm²，最后一项仅启用去马赛克时计入；功耗`.03×(enabled_modules+1)×parallel_pixels×GHz` W。两行RAW12以16位存放，占用`4×max_width` B。

这些系数让资源选择产生可解释的游戏代价，没有覆盖所有资源对真实PPA的影响。核心结构图是逻辑连接示意，不是RTL、网表或物理布局。固定验证的ISP常量帧/范围只检验相应不变量，不证明插值质量；NPU溢出wrap通过只证明指定整数语义，不证明数值精度适合模型。

`.sil`保存自定义硬件与模板全参数，CPU/GPU模板参考制程也随文件保存；导入优先使用快照，目录缺失仍可读取。模型版本用于诊断，公式与非核心目录仍由运行引擎解释，跨模型版本重算可能变化。

PicoRV32固定提交源码单独经Icarus运行ADDI/ADDI/SW冒烟测试，观察存储42。它提供真实RTL学习入口，未执行完整ISA合规、综合或物理签核。测试结果不用于校准玩家IP的PPA。

资料库49条，原有99条逐条记录处置。正文核验、书目核验与仅定位待核验分别标明；特定厂家/产品的资料不会自动证明本作所有参数。文件版本、导入约束与未知字段处理见[格式说明](FORMAT.md)。

## 历史修复与移动复盘

`rescue.py`的`rescue-chip-evidence-v2`依据Edelman论文验证Pentium SRT商选择局部边界，依据AMD勘误298验证PTE A/D更新-驱逐-探测事件，并检验端口隔离后连接能力。它不是完整x87/IEEE754、全系统一致性或SATA电气仿真。

移动案例的统一7000pF/C/V/f模型已删除。`rescue_measurements.py`保存9个具体芯片的原始设备/系统/CPU/GPU/内存/工作负载数据，未取得完整校准时只显示档案、禁止通关。性能合同至少检查单核90%、多核/GPU峰值85%保留与持续绝对吞吐；必需数据缺失不默认通过。旧模型进度不代表新验收。

`geekbench.py`实现GB6分项几何平均和整数65%/浮点35%加权，但不生成缺失分项；现有实测分数独立展示，不将SP分数换算为GB6。没有足够workload模型的任意ISA核心返回不可估计。具体反事实GB6推算仍需工作负载校准，不宣称已实现。

执行观测由实际调度事件和计算语义生成：CPU按线程提交，GPU逐发射事件/掩码，NPU按PE波前和位宽累加，ISP按计算得到的阶段图像与简化流水进度。加速器传输只记汇总流量账本，不表示实际DMA先后。详见[执行观测](guide/observatory.md)与[拯救芯片](guide/rescue.md)。

## 挑战验收

12项新委托为虚构情景，全部门槛是游戏规则。engine/challenges.py列出独立检查，只有项目目标和常规签核同时通过才能流片记录完成。随机市场结果不改变委托是否完成。设计可携带关卡ID与全部核心，但工作负载/热/成本仍用本版模型解释；参考方案仅是一种已验证可行解。

## 分任务CPU性能观察

core_performance.py提供96条独立流、129条依赖链、32行四次重用cache工作集与乘法/整数混合；每项IPC=实际提交指令/总模型周期，含前端填充和冷cache。不代替固定验证，也不用于跨ISA或实物排名。基线只对同ISA同任务集合比较，CPU硬件变化重新运行，测试结果缓存以完整硬件为键。默认短访存样例可对加宽保持53周期；这不是遗漏宽度参数。
