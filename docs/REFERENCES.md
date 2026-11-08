# 参考文献与证据等级
正式来源 23 条：正文核验与仅书目核验分别标注。模型数字为游戏假设，除明确字段级证明外不声称来自论文。
[原有 99 条引用的逐项处置](research/LEGACY_AUDIT.md)；[机器可读核验记录](research/audit.json)。

## T1 · 论文 / 规范 / 方法
### Cost-size optima of monolithic integrated circuits
- id: `murphy1964`
- 作者/机构: B. T. Murphy
- 出处: Proceedings of the IEEE 52(12), 1537–1545 (1964)
- 核验状态: bibliography_checked
- 链接: https://doi.org/10.1109/PROC.1964.3442
- 原文定位: Crossref DOI 10.1109/PROC.1964.3442；题名、作者、卷期与页码。未取得论文正文。
- 支持: 确认这篇论文的身份和良率/尺寸成本研究主题。
- 不支持: 没有核验具体 Murphy 公式、D0、成熟度、晶圆价格或现代节点良率，不能称本作已经按原文校准。
- 本作使用: economics.py 的 Murphy 型公式为游戏选用的解析假设，不标为已验证原文实现。
- 核验文件: `murphy_correct.raw` · SHA-256 `ce4eee5de9bbfb2d3da3c8f8e6b54410caace54d6eadf1377b6818f6697db487`
- 核验文件: `crossref_murphy.raw` · SHA-256 `b6c94469f9d701b0fc372656266a8be92d9e995e8ce7fb159dc1b15703262e32`
### CACTI 7: New Tools for Interconnect Exploration in Innovative Off-Chip Memories
- id: `cacti7`
- 作者/机构: Rajeev Balasubramonian; Andrew B. Kahng; Naveen Muralimanohar; Ali Shafiee; Vaishnav Srinivas
- 出处: ACM TACO 14(2), Article 14, 1–25 (2017)
- 核验状态: fulltext_checked
- 链接: https://doi.org/10.1145/3085572
- 原文定位: 作者公开稿 p.1 Abstract；§1 Introduction；CACTI README 的 process-specific values。
- 支持: 建模片外内存 I/O 的功率、时序、互连与拓扑；论文在明确系统配置下验证工具，并给出两种内存通道案例。
- 不支持: 不是本作 LPDDR5X 控制器仿真，也没有用它计算 3/2nm SRAM 面积；论文中的 18%、22% 和成本收益不能迁移到本作或手机。
- 本作使用: 缓存 lab 为标签/LRU 模拟，PPA 未调用 CACTI；本条只解释可提取延迟/能耗的真实工具需要哪些输入。
- 可读作者稿/全文: https://www.cs.utah.edu/~rajeev/pubs/taco17.pdf
- 核验文件: `cacti_paper.raw` · SHA-256 `0d07f364ef2b73f2e915c3cb436c12bd55149cd67de92aab38ead4789d91bc26`
- 核验文件: `cacti_actual.raw` · SHA-256 `036e1de9a9e4ad7b530d31316ddede8230ffa7b18700f0fc8b3daeac39b65e8d`
- 核验文件: `cacti_repo.raw` · SHA-256 `26f41fa2b22bcb2e37fe0ca22dc0c9c4eaca4e0d1d804a3b91d615e9467f54c5`
### The gem5 Simulator
- id: `gem5`
- 作者/机构: Nathan Binkert; Bradford Beckmann; Gabriel Black; Steven K. Reinhardt; Ali Saidi; Arkaprava Basu; Joel Hestness; Derek R. Hower; Tushar Krishna; Somayeh Sardashti; Rathijit Sen; Korey Sewell; Muhammad Shoaib; Nilay Vaish; Mark D. Hill; David A. Wood
- 出处: ACM SIGARCH Computer Architecture News 39(2), 1–7 (2011)
- 核验状态: fulltext_checked
- 链接: https://doi.org/10.1145/2024716.2024718
- 原文定位: pp.1–3：Abstract、§2 Overall Goals、CPU Models / Memory System；全文共 7 页。
- 支持: gem5 区分不同 CPU 模型、系统模式和内存模型；支持不同模拟详细度。
- 不支持: 本作没有接入 gem5，不实现 gem5 O3CPU；论文不提供任意芯片的 IPC、面积或频率。
- 本作使用: 解释功能模型与时序模型边界。CPU lab 是顺序轨迹 + 简化调度，与 gem5 相互独立。
- 可读作者稿/全文: https://research.cs.wisc.edu/multifacet/papers/can11_gem5.pdf
- 核验文件: `crossref_gem5.raw` · SHA-256 `3133e76c18e8dd7e09c3c8fd0aa8fc706b95d9594b7af17a5eb4dab870790bb6`
- 核验文件: `gem5_pdf.raw` · SHA-256 `e1534a27b06652990620e882e9459ebd88f41735d8488054c8d0bd788980360d`
### A Case for Thermal-Aware Floorplanning at the Microarchitectural Level
- id: `sankaranarayanan2005`
- 作者/机构: Karthik Sankaranarayanan; Sivakumar Velusamy; Mircea R. Stan; Kevin Skadron
- 出处: JILP, October 2005, pp.1–16；PDF 页眉卷 8，站点置于 vol7 (2005)
- 核验状态: fulltext_checked
- 链接: https://jilp.org/vol7/v7paper15.pdf
- 原文定位: p.1 Abstract；§2 Thermal Modeling；§3 Thermal-aware Floorplanning。刊物目录与 PDF 卷号存在差异，保留说明。
- 支持: 在论文的工作负载与热模型中，布局通过横向热扩散影响热点和性能；结果依赖具体温度/互连模型。
- 不支持: 不支持本作 24°C 功率密度系数或任意手机温度预测；不能从布局颜色推导热可靠性。
- 本作使用: 布局热权衡的定性教材；功率密度模糊图不是论文热模型。
- 核验文件: `thermal15.raw` · SHA-256 `4821e0f8a81363fce2da5428aa48ef30384542ebcc4da70c37fa539ec077a864`
- 核验文件: `thermal_index.raw` · SHA-256 `324d158c8cf944adb3118e1419bd39ae49b4e1a6d45ced10dfebc509ca6f5d12`
### Dark silicon and the end of multicore scaling
- id: `esmaeilzadeh2011`
- 作者/机构: Hadi Esmaeilzadeh; Emily Blem; Renee St. Amant; Karthikeyan Sankaralingam; Doug Burger
- 出处: ISCA 2011, 365–376 (2011)
- 核验状态: bibliography_checked
- 链接: https://doi.org/10.1145/2000064.2000108
- 原文定位: Crossref：题名、作者、会议、365–376 页；未核验正文参数。
- 支持: 确认书目身份，作为功耗约束主题的延伸阅读。
- 不支持: 不据此设定手机功耗、暗硅比例或大核争用罚分；正文结果未核验。
- 本作使用: 延伸阅读，不用于数值参数来源。
- 核验文件: `crossref_dark2.raw` · SHA-256 `d8a7e67d9d28a4ed3d1ee6fc4fa35edfe0a1a3190d0e8d5d368d52d7f0af6b8a`
### The future of microprocessors
- id: `borkar2011`
- 作者/机构: Shekhar Borkar; Andrew A. Chien
- 出处: Communications of the ACM 54(5), 67–77 (2011)
- 核验状态: bibliography_checked
- 链接: https://doi.org/10.1145/1941487.1941507
- 原文定位: Crossref 书目与摘要；未取得全文。
- 支持: 已核验摘要把能效描述为性能的根本约束。
- 不支持: 不能证明本作具体电压、漏电温度系数或缺陷率。
- 本作使用: 背景阅读，无数值映射。
- 核验文件: `crossref_borkar2.raw` · SHA-256 `4d37336e1fef002df11e939e718b8de7e7c3bf411ce751c49131cfd9727ae9d1`
### Validity of the single processor approach to achieving large scale computing capabilities
- id: `amdahl1967`
- 作者/机构: Gene M. Amdahl
- 出处: AFIPS Spring Joint Computer Conference, April 18–20 1967；Crossref 起页 483 (1967)
- 核验状态: bibliography_checked
- 链接: https://doi.org/10.1145/1465482.1465560
- 原文定位: Crossref 题名、作者、会议与起页；未取得原文。
- 支持: 书目身份可确认。课程中的 S=1/((1-p)+p/N) 另按固定工作量与理想并行假设推导。
- 不支持: 不称公式已经逐字与原文核对；不将固定串行比例当作所有程序的常数。
- 本作使用: 工程页和课程使用自足推导的理想加速上限；异构核折算额外是游戏假设。
- 核验文件: `crossref_amdahl.raw` · SHA-256 `4f15b219bdc60f69539ff8775ff02dd0bab054f8d945d925977d54c1828a4a24`
### Roofline: an insightful visual performance model for multicore architectures
- id: `roofline2009`
- 作者/机构: Samuel Williams; Andrew Waterman; David Patterson
- 出处: Communications of the ACM 52(4), 65–76 (2009)
- 核验状态: bibliography_checked
- 链接: https://doi.org/10.1145/1498765.1498785
- 原文定位: Crossref 2009 正式出版书目与摘要；正文核验使用另列的 2008 技术报告。
- 支持: 确认正式出版身份；方法由同作者公开技术报告提供可读原文。
- 不支持: 不把 2008 报告称作完全相同的 2009 出版版本。
- 本作使用: 出版版书目，正文方法引用 roofline2008。
- 核验文件: `crossref_roofline.raw` · SHA-256 `130a3f0d98d0dd66cbcd9f79ba88f47d99c95cb13d0f726cc441b14f14823901`
### Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures
- id: `roofline2008`
- 作者/机构: Samuel Williams; Andrew Waterman; David A. Patterson
- 出处: UC Berkeley Technical Report UCB/EECS-2008-134, 17 October 2008 (2008)
- 核验状态: fulltext_checked
- 链接: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-134.pdf
- 原文定位: 报告正文 §3 The Roofline Model（PDF p.3–4），Figure 1；Appendix A 关于带宽/强度测量。
- 支持: 可达到的性能受峰值算力与内存带宽×运算强度二者约束；强度用到达片外 DRAM 的流量作分母。
- 不支持: 纸面理论带宽不等于实测有效带宽；本作抽象 Gop/s 不是 FLOP/s，也不等于真实程序性能。
- 本作使用: 工作负载页 min(compute, bandwidth×intensity)；所有算力/利用率输入明确为假设。
- 核验文件: `roofline_lbnl.raw` · SHA-256 `c92f852eed1070b140302114339271dc1a4d6d665814ac9000be6ce06a7d6bcb`
### SPEC CPU 2017 — Overview
- id: `spec2017`
- 作者/机构: Standard Performance Evaluation Corporation
- 出处: SPEC CPU 2017 documentation, overview.html；2026-11-08 查阅版本 (2017)
- 核验状态: fulltext_checked
- 链接: https://www.spec.org/cpu2017/Docs/overview.html
- 原文定位: overview：What is SPEC CPU 2017?；SPECrate 与 SPECspeed 描述。
- 支持: SPECspeed 测单任务时间，SPECrate 测吞吐；套件结果需要明确硬件、编译器和配置。
- 不支持: SP 游戏分不是 SPEC 结果；没有运行套件，不能称本作已用 SPEC 校准。
- 本作使用: 测试方法说明，不作 IPC/PPA 数值依据。
- 核验文件: `spec_docs.raw` · SHA-256 `6f091c0ac4c36ed57e78b4beb524fde237c9dcd6e305a3bb7978cd3c9d68a418`
### Geekbench 6 Benchmark Internals
- id: `geekbench6`
- 作者/机构: Primate Labs
- 出处: 官方 PDF，版本未在 URL 固定；2026-11-08 查阅文件，以 SHA-256 标识 (2023)
- 核验状态: fulltext_checked
- 链接: https://www.geekbench.com/doc/geekbench6-benchmark-internals.pdf
- 原文定位: 文档页 7–10：Multi-Threading、Instruction Sets、Scores。
- 支持: GB6 的多线程采用 shared task；工作负载可使用 ISA 加速；评分有特定标尺。
- 不支持: 与 SP 分不能等价；ISA 扩展不是必然“测试作弊”；不能把不同程序 IPC 当 GB6 分。
- 本作使用: 教程中解释可比测量与扩展收益边界；旧 bench_isa 是游戏专用路径，不代表本 lab 的扩展。
- 核验文件: `gb6_docs.raw` · SHA-256 `8cb18b140e12e8b308b94d9f8abfa1e4d03b12caf2a4667e90f70495e3570136`
### The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set
- id: `riscv_isa`
- 作者/机构: RISC-V International
- 出处: 文档发布标识 v20260120；RV32I v2.1 (2026)
- 核验状态: fulltext_checked
- 链接: https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html
- 原文定位: Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- 支持: x0 恒为零；32 位整数运算、12 位符号扩展立即数、分支/跳转、大小端与访存语义，FENCE 与环境调用。
- 不支持: 本 lab 不实现特权态、执行环境、二进制取指、外设或全部非对齐访存行为，不能宣称完整 RISC-V 合规。
- 本作使用: isa.py 执行语义与 32 位编码的直接规范。HALT 为实验伪指令，不是标准指令。
- 核验文件: `riscv_versioned.raw` · SHA-256 `0705ae047f800a0a416e2de1d45c8ab83aea814c5225a1e568940ee7fd69d948`
- 核验文件: `opcodes_i.raw` · SHA-256 `146e297ddbe346f325d993aaf56d7006f1bfde39df584b888b221543def17b97`
- 核验文件: `opcodes_rv32_i.raw` · SHA-256 `8ef811f8e1d4435e4c61c1d9e0384032c431106f0ef5068f48d3a506701ce463`
- 核验文件: `opcodes_m.raw` · SHA-256 `1a53ea03820b7044de4f0f04d207c1e4fc0ced46deb2c6ed4a3ca268fa37ddbe`
### RISC-V Unprivileged ISA — M Extension for Integer Multiplication and Division
- id: `riscv_m`
- 作者/机构: RISC-V International
- 出处: v20260120；M v2.0 (2026)
- 核验状态: fulltext_checked
- 链接: https://docs.riscv.org/reference/isa/v20260120/unpriv/m-st-ext.html
- 原文定位: Multiplication；Division；Table 1: Semantics for division by zero and division overflow。
- 支持: 低/高乘积的符号组合；除法向零截断；除零商全 1、余数为被除数；INT_MIN/-1 的规定结果。
- 不支持: M 规范不指定乘除单元延迟、面积或功耗，不能由扩展开关凭空得出能效提升。
- 本作使用: M 指令语义与已实现指令表；延迟由 lab 输入给定。
- 核验文件: `rv_m.raw` · SHA-256 `d490d42bc590985100f8c1660eb47edf1cd10bf3f5ba14f033e54003a7f0f73b`
### RISC-V Unprivileged ISA — RV32 Zbb Basic Bit-manipulation
- id: `riscv_zbb`
- 作者/机构: RISC-V International
- 出处: v20260120；Zbb v1.0.0 (2026)
- 核验状态: fulltext_checked
- 链接: https://docs.riscv.org/reference/isa/v20260120/unpriv/b-st-ext.html
- 原文定位: Zbb: Extension for Basic bit-manipulation；18条RV32指令的各自 Description/Operation；riscv-opcodes rv_zbb/rv32_zbb 的固定位编码。
- 支持: RV32 Zbb 18条指令的行为：ANDN/ORN/XNOR、CLZ/CTZ/CPOP、MIN/MINU/MAX/MAXU、SEXT.B/SEXT.H/ZEXT.H、ROL/ROR/RORI、ORC.B/REV8。
- 不支持: 不支持 RV64 专用 W 指令、Zba/Zbs/Zbc 或完整 B；未通过第三方 ISA 合规套件。规范不指定执行延迟和物理面积。
- 本作使用: RV32 Zbb 的执行语义与编码；延迟和面积仍是本作假设。
- 核验文件: `rv_b.raw` · SHA-256 `b9923ee87b781ac22a74ea157f9b176d1883f4ea1886d36c74d6e0a81397b09a`
- 核验文件: `opcodes_zbb.raw` · SHA-256 `f5d7d97b8d5d74135170cc13ba935bf97f39eac03893428604df71c9f8b64c13`
- 核验文件: `opcodes_rv32_zbb.raw` · SHA-256 `e1274bfd6bb549cd04b60c1c22efbc74078ca6dfd232c5647bcf1b70d14aed70`
### Intel 64 and IA-32 Architectures Software Developer’s Manual, Volumes 1/2A/2B
- id: `intel_ia32`
- 作者/机构: Intel Corporation
- 出处: 253665-093US / 253666-093US / 253667-093US, September 2026 (2026)
- 核验状态: fulltext_checked
- 链接: https://cdrdv2.intel.com/v1/dl/getContent/671199
- 原文定位: Vol.1 §3.4.1.1 pp.3-12–3-13：16个GPR、32位写零扩展；Vol.2A ADD pp.3-14–3-15、IMUL pp.3-451–3-454、Jcc pp.3-499–3-503；Vol.2B MOV pp.4-28–4-31与SAL/SAR/SHL/SHR pp.4-603–4-607。
- 支持: 32/64位整数运算与标志；16个64位GPR/32位别名零扩展；REX.W/R/B与MOV寄存器/访存/imm64形式；双操作数IMUL截断与CF/OF、其余算术标志未定义；Jcc条件；shift计数掩码、OF/CF及count=0标志不变。
- 不支持: 本作仅明确整数子集，无段/分页/OS、8/16位别名、RIP/索引寻址、x87/SSE/AVX、异常或完整编码取指；64KiB对齐访存限制是教学输入，不是x86限制。SDM不支持本作uop/latency或PPA数字。
- 本作使用: arch_cpu.py IA-32与x64_cpu.py Intel64整数子集；原生语义和编码输入资源时序模型，无厂商CPU复刻。
- 可读作者稿/全文: https://cdrdv2.intel.com/v1/dl/getContent/671241
- 核验文件: `intel_vol2a.raw` · SHA-256 `87c5acb6f27e24d9d364841a0d2346c91a8482e36f403409954e2d2a8c817bac`
- 核验文件: `intel_vol2b.raw` · SHA-256 `a261998ace8e07f624bf3e2486bb6cfe950fb8be8d0dc9631bcecb4c5ec953e4`
- 核验文件: `intel_sdm.raw` · SHA-256 `f405c1263418c56b19104513649eec6080a3a21a5956415941bc3aab5d93d020`
- 核验文件: `intel_vol1.raw` · SHA-256 `f6ffc430dfa2dada4f791b1ecb462810e59827befe9a9c23f9160941eea642f9`
### Arm A64 instruction pseudocode and encoding — 2026-03_rel mirror
- id: `arm_a64_isa`
- 作者/机构: Arm Limited; hosted by Stanford / Zachary Yedidia
- 出处: Non-confidential Arm ISA machine-readable pages, 2026-03_rel; hosted mirror (2026)
- 核验状态: fulltext_checked
- 链接: https://www.scs.stanford.edu/~zyedidia/arm64/add_addsub_imm.html
- 原文定位: ADD/SUBS immediate Operation and register31 treatment; MOV register alias of ORR; MOVZ/MOVN encodings; LDR unsigned offset; RET; Shared Pseudocode X accessor and AddWithCarry; B.cond ConditionHolds.
- 支持: A64 W/X位宽、零寄存器与SP在不同形式中的差异、MOVZ/MOVN单指令立即数、NZCV、分支与unsigned-scaled访存编码。
- 不支持: 镜像不是完整Arm架构手册；未实现EL/系统寄存器、SIMD/SVE/SME/原子、SP、所有寻址模式、二进制解码或第三方合规认证；不能据此得出核心面积与能耗。
- 本作使用: A64前端拒绝把immediate ADD/LDR的SP当XZR；MOV仅接收一条MOVZ/MOVN可表达立即数，不虚构多条伪指令的PC。
- 核验文件: `arm_addsub.raw` · SHA-256 `eec4a891f31c606b5720e7ef67dfdc4ff0f6b5860c6228ff328f35c75f9c8f73`
- 核验文件: `arm_subs.raw` · SHA-256 `ab5419675a7639700de8fb64b2eae0d1fe819e4a21e151bfbfa96b9b45303518`
- 核验文件: `arm_mov.raw` · SHA-256 `29592d4c558409aa6beb2f714e20e1d435c71bd8f58dd3573a3827d96b16d5f3`
- 核验文件: `arm_ldr.raw` · SHA-256 `846dc7f99bacae2d0c3e46a0ebc937e541e183a13c9908452373207f92b384ad`
- 核验文件: `arm_ret.raw` · SHA-256 `f230b580f3944a44121f65ac891add791f2464d3a717c0d9d2a71b76e9c7eb5b`
- 核验文件: `arm_movz.raw` · SHA-256 `d7e5180e696ebadf79f0d3967697267684ff3219480b26818f9143049ecac442`
- 核验文件: `arm_movn.raw` · SHA-256 `3a34db480bff07b2a889afce251405aaa18d46662c5883090a9a30efd94f74b2`
- 核验文件: `arm_shared.raw` · SHA-256 `822a15b7ed654f618efd1820279fabf900c28b74692e6df01fe52323d11432fd`
- 核验文件: `arm_bcond.raw` · SHA-256 `14d8c93441b0859b1fc937f3f5b3b415fbf0a71c2371db1015fed2d683688468`
### In-Datacenter Performance Analysis of a Tensor Processing Unit
- id: `tpu2017`
- 作者/机构: Norman P. Jouppi, Cliff Young, Nishant Patil, David Patterson, Gaurav Agrawal, Raminder Bajwa, Sarah Bates, Suresh Bhatia, Nan Boden, Al Borchers, Rick Boyle, Pierre-luc Cantin, Clifford Chao, Chris Clark, Jeremy Coriell, Mike Daley, Matt Dau, Jeffrey Dean, Ben Gelb, Tara Vazir Ghaemmaghami, Rajendra Gottipati, William Gulland, Robert Hagmann, C. Richard Ho, Doug Hogberg, John Hu, Robert Hundt, Dan Hurt, Julian Ibarz, Aaron Jaffey, Alek Jaworski, Alexander Kaplan, Harshit Khaitan, Daniel Killebrew, Andy Koch, Naveen Kumar, Steve Lacy, James Laudon, James Law, Diemthu Le, Chris Leary, Zhuyuan Liu, Kyle Lucke, Alan Lundin, Gordon MacKean, Adriana Maggiore, Maire Mahony, Kieran Miller, Rahul Nagarajan, Ravi Narayanaswami, Ray Ni, Kathy Nix, Thomas Norrie, Mark Omernick, Narayana Penukonda, Andy Phelps, Jonathan Ross, Matt Ross, Amir Salek, Emad Samadiani, Chris Severn, Gregory Sizikov, Matthew Snelham, Jed Souter, Dan Steinberg, Andy Swing, Mercedes Tan, Gregory Thorson, Bo Tian, Horia Toma, Erick Tuttle, Vijay Vasudevan, Richard Walter, Walter Wang, Eric Wilcox, and Doe Hyun Yoon
- 出处: arXiv:1704.04760, author preprint stating ISCA 2017; accessed PDF version pinned by SHA-256 (2017)
- 核验状态: fulltext_checked
- 链接: https://arxiv.org/abs/1704.04760
- 原文定位: Abstract; §2 TPU Architecture / Figure 1–2: 256×256 MAC array, Accumulators, Unified Buffer; §4 roofline analysis.
- 支持: 特定TPUv1的稠密矩阵阵列、本地缓冲、数据搬运与算力/带宽限制；原文INT16输入有吞吐降低，非统一同速实现。
- 不支持: 本作不实现TPU ISA、92TOPS/28MiB或论文硬件精度时序；假设每PE每周期一个INT8/INT16 MAC，INT16需要独立更宽乘法器PPA估算；无稀疏/量化标定。
- 本作使用: NPU lab为整数GEMM与tile/scratchpad实验，不将论文实际TPU指标映射任意设计。
- 可读作者稿/全文: https://arxiv.org/pdf/1704.04760
- 核验文件: `tpu_paper.raw` · SHA-256 `19793e4ae1486630ac45a12facabc0e80609dd679db8ca7a3a040f8bf0d8e0be`
### Malvar-He-Cutler Linear Image Demosaicking
- id: `demosaic2011`
- 作者/机构: Pascal Getreuer
- 出处: Image Processing On Line, 2011; DOI 10.5201/ipol.2011.g_mhcd; retrieved PDF contains v0.5.1 class header (2011)
- 核验状态: fulltext_checked
- 链接: https://doi.org/10.5201/ipol.2011.g_mhcd
- 原文定位: §1 Introduction / Figure 2 Bayer pattern; §2 Algorithm, initial bilinear green axial-neighbor and red/blue diagonal-neighbor formulas.
- 支持: Bayer采样与demosaic问题；文章先介绍bilinear baseline再讨论Malvar-He-Cutler的5×5跨通道校正。
- 不支持: 本作只实现基础bilinear，未实现论文MHC 5×5改进；边缘缩小邻域与gamma/black-level是本作规则，未由论文验证；不是完整相机ISP。
- 本作使用: ISP lab讲解bilinear插值、black-level、幂gamma与输出量化；原文MHC仅为延伸阅读。
- 可读作者稿/全文: https://www.ipol.im/pub/art/2011/g_mhcd/article.pdf
- 核验文件: `demosaic.raw` · SHA-256 `e5d80b13743e3fe1813e41670c8e1b58c7742890501302e076c5b37ca1b01a60`

## T2 · 官方资料 / 案例
### Apple unleashes M1
- id: `apple_m1`
- 作者/机构: Apple Newsroom
- 出处: 10 November 2020 官方发布资料 (2020)
- 核验状态: fulltext_checked
- 链接: https://www.apple.com/newsroom/2020/11/apple-unleashes-m1/
- 原文定位: The World’s Best CPU Performance Per Watt；Unified Memory Architecture；Footnotes 的测试系统。
- 支持: 官方陈述 M1 为四性能核+四效率核、统一内存架构、5nm 和 160 亿晶体管。收益比较是厂商在脚注条件下的声明。
- 不支持: 没有披露 119mm²、ROB/解码宽度、实际 GHz、热阻或授权价格；不能当独立测评。
- 本作使用: 芯片案例只引结构和配置；沙盒 PPA 与分数不从本来源推导。
- 核验文件: `m1_official.raw` · SHA-256 `a3a219af0c41f6a692c655382b5356019ae50fa6e4c6a1d05ccc2a22514588be`
### Apple introduces M4 chip
- id: `apple_m4`
- 作者/机构: Apple Newsroom
- 出处: 7 May 2024 官方发布资料 (2024)
- 核验状态: fulltext_checked
- 链接: https://www.apple.com/newsroom/2024/05/apple-introduces-m4-chip/
- 原文定位: New 10-core CPU；A GPU Brings New Capabilities to iPad Pro；脚注测试条件。
- 支持: 官方配置为最多四性能核+六效率核、十核 GPU、第二代 3nm；发布设备为 iPad Pro，非统一的风冷笔记本情景。
- 不支持: 该发布文没有 4.4GHz、准确 ROB、N3E 身份或 die 面积；38 TOPS 未明确精度不能映射本作 INT8 档位。
- 本作使用: 纠正 M4 案例上下文；性能、面积、频率均为独立游戏输入。
- 核验文件: `m4_official.raw` · SHA-256 `53fe617998ec36e1fed97537fd4004ec0f53ade7929cbc2f36d899e81bd10d1d`
### SiFive Performance P600 Series — P650/P670
- id: `sifive_p670`
- 作者/机构: SiFive
- 出处: 官方产品页当前版本；2026-11-08 查阅，不据此推定首次发布年 (2026)
- 核验状态: fulltext_checked
- 链接: https://www.sifive.com/cores/performance-p650-670
- 原文定位: P650/P670；P670 的 thirteen-stage, four-issue, out-of-order pipeline 与 vector application processor 描述。
- 支持: 厂商将 P670 描述为 13 级、四发射、乱序、向量应用处理器；P650 面向不需要向量计算的情况。
- 不支持: 不支持游戏 2.76mm²、2.4GHz、1.2W、授权费或 Android 生态分；不把营销 SPEC/GHz 与本作模型等价。
- 本作使用: 区分实际核心产品与基础 ISA；定制核 lab 不模拟 P670 本身。
- 核验文件: `sifive_p670_exact.raw` · SHA-256 `0448f5253934c261ac1c4907e16434f1e551f38b677645994906f25a28581e51`
### CUDA Programming Guide — 2.3 Writing SIMT Kernels
- id: `cuda_simt`
- 作者/机构: NVIDIA
- 出处: CUDA Programming Guide v13.5, 2.3 Writing SIMT Kernels；获取于2026-11-08，SHA-256固定文件 (2026)
- 核验状态: fulltext_checked
- 链接: https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/writing-cuda-kernels.html
- 原文定位: Basics of SIMT; Global Memory / coalescing; shared-memory bank conflicts. Source page describes divergent code paths and 32-thread NVIDIA warps.
- 支持: SIMT每线程状态/控制流、warp内分歧、访存事务合并和bank冲突影响吞吐。
- 不支持: 本作可调warp4–64是研究假设，不是CUDA支持的warp宽度；未运行CUDA、PTX或真实光栅pipeline，不声称模拟NVIDIA GPU。
- 本作使用: GPU lab计算FP32逐lane任务，并对分歧路径假设串行；两指令AXPY非FMA，传输与计算不重叠。
- 核验文件: `cuda_simt.raw` · SHA-256 `8ccdde3e39fa2512e98c1f256e56d0547a2aa058153b8bf187fdc62e2130ce33`
### PicoRV32 — pinned upstream RTL and README
- id: `picorv32_rtl`
- 作者/机构: Claire Xenia Wolf; YosysHQ contributors
- 出处: Git revision ef203c2b0a3fb793280f5114941416c425c5b461 (2026)
- 核验状态: fulltext_checked
- 链接: https://github.com/YosysHQ/picorv32/tree/ef203c2b0a3fb793280f5114941416c425c5b461
- 原文定位: README: Introduction, Parameters, Native Memory Interface; picorv32.v module picorv32; COPYING ISC license.
- 支持: 真实Verilog RV32核心，可配置I/E/C/M等功能，有明确ISC开放许可；本包固定提交并保留版权。
- 不支持: 本作独立冒烟测试不是上游riscv-tests或完整ISA认证；解析lab模型不是PicoRV32时序/PPA，不能据此声明芯片可制造。
- 本作使用: 独立iverilog/vvp编译真实上游RTL，ADDI/ADDI/SW存42的冒烟测试。未用其评分替代任意命名IP的PPA。
- 核验文件: `third_party/picorv32/picorv32.v` · SHA-256 `0836050971b3c6cdd28ac3b1e5719a67fb645161912bef1e472e63995ceb0622`
- 核验文件: `third_party/picorv32/COPYING` · SHA-256 `041ebc727233e5bf096dd41260cbb81014d3d29ca007a15f3b1807d4e9ff288e`
- 核验文件: `third_party/picorv32/README.md` · SHA-256 `399c2d2e00e4581ee4ef33034089992401e10c4e917a33cd363b80dfb283e964`
- 核验文件: `third_party/picorv32/tb_silicon.v` · SHA-256 `eb6d8eb735050d1b2892daadae3e36cd546cab9046bc32467abcc790aa00f648`

## T3 · 独立评测

## T4 · 报道
