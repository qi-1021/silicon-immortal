# 参考文献与证据等级
资料库 49 条：正文核验、仅书目核验与仅定位待核验分别标注。模型数字为游戏假设，除明确字段级证明外不声称来自论文。
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
### The Mathematics of the Pentium Division Bug
- id: `pentium_srt`
- 作者/机构: Alan Edelman
- 出处: 原始测量定位 (1997)
- 核验状态: fulltext_checked
- 链接: https://math.mit.edu/~edelman/homepage/papers/pentiumbug.pdf
- 原文定位: SIAM Review39(1),54–67；§2–4，图4.1与表4.1。
- 支持: radix4 SRT冗余商位、部分余数边界与五个错误+2→0表项；D=17/20/23/26/29÷16。
- 不支持: 不是完整IEEE754/x87仿真；未定义本作修复性能门槛或CPU PPA。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pentium_edelman.pdf` · SHA-256 `d5c3f956e8800db1a7731ea4c7618e61844f4f8f55c0111cec7d20e0f4da51eb`

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
### Intel Corporation Annual Report 1994
- id: `intel_fdiv1994`
- 作者/机构: Intel Corporation
- 出处: 厂商原始资料 (1994)
- 核验状态: fulltext_checked
- 链接: https://www.annualreports.com/HostedData/AnnualReportArchive/i/NASDAQ_INTC_1994.pdf
- 原文定位: 厂商年报公开镜像，PDF第3页 To our stockholders；180dpi OCR复核浮点问题、更换政策与费用段落。
- 支持: 1994年Pentium浮点问题引发更换与核销；最初选择性更换后来改为无条件更换。
- 不支持: 不提供FDIV选择表的实现、故障概率或本作整数除法参数；未声称复刻Pentium。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `intel94.pdf` · SHA-256 `b00af8c9fa14951f507852cde8ecf55725f7eb839ac3752c95975bdd1a93b107`
### Intel Corporation Annual Report 2011 · Note 20
- id: `intel_cougar2011`
- 作者/机构: Intel Corporation
- 出处: 厂商原始资料 (2011)
- 核验状态: fulltext_checked
- 链接: https://www.annualreports.com/HostedData/AnnualReportArchive/i/NASDAQ_INTC_2011.pdf
- 原文定位: 厂商年报公开镜像，Note 20: Chipset Design Issue，正文印刷页72。
- 支持: 2011年1月确认6系列/Cougar Point设计问题，2011年2月开始出货硅修订版。
- 不支持: 此段不能证明本作端口分组、退化曲线、桥接周期、故障率或四设备任务需求。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `intel2011.pdf` · SHA-256 `11444e995ddbb3e74bef3e3fabc914c1fab02b4a90319041f5bb7c0185e7b1f9`
### Revision Guide for AMD Family 10h Processors · Rev3.92
- id: `amd_10h_298`
- 作者/机构: AMD
- 出处: 厂商原始资料 (2012)
- 核验状态: fulltext_checked
- 链接: https://www.amd.com/content/dam/amd/en/documents/archived-tech-docs/revision-guides/41322_10h_Rev_Gd.pdf
- 原文定位: 2012-03 Rev3.92，印刷p66勘误298、p31修订矩阵。DR-BA/B2受影响，DR-B3未标。
- 支持: PTE Accessed/Dirty位更新不原子，旧PTE可进入L3；探测可导致A/D未设、一致性丢失/数据损坏。建议HWCR[TlbCacheDis]及MSRC001_1023[1]。
- 不支持: 不是所有并发load都挂起；未提供通用性能损失百分比。规避代价须用对应工作负载测量，不按固定50%声称实测。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `amd_41322_full.pdf` · SHA-256 `6cc58481d898139e58c1659fe5cc6f45d9a74eea9ee07807541a4a2ee1edc1aa`
### Google Tensor debuts on the new Pixel 6 this fall
- id: `tensor_g1`
- 作者/机构: Google
- 出处: 厂商原始资料 (2021)
- 核验状态: fulltext_checked
- 链接: https://blog.google/products/pixel/google-tensor-debuts-new-pixel-6-fall/
- 原文定位: 2021-08-02，正文 Tensor 与计算摄影/安全段落。
- 支持: 首代Tensor面向Pixel 6/6 Pro；官方设计目标包括计算摄影、AI/ML与安全。
- 不支持: 厂商介绍不是独立功耗/持续性能测量，不能据此称整代失败。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `tensor_g1.html` · SHA-256 `7df44136628f77b571a11462f6771fdea3f5aaa388bdd761157cfa9d29b3d151`
### The redesigned Pixel 7 and Pixel 7 Pro are here
- id: `tensor_g2`
- 作者/机构: Google
- 出处: 厂商原始资料 (2022)
- 核验状态: fulltext_checked
- 链接: https://blog.google/products/pixel/pixel-7-pixel-7-pro/
- 原文定位: 2022-10-06，Google Tensor G2与多个子系统协同段落。
- 支持: 确认G2对应Pixel 7/7 Pro，官方强调软件、机器学习与子系统协同。
- 不支持: 不能证明功耗、持续性、基带短板或本作参数，更不是商业失败判定。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `tensor_g2.html` · SHA-256 `9647864d5bb80beb6e6d9338bc27f6bbf0d305c35eab90c6511e1b5bebb1d90a`
### Google Tensor G3: The new chip that gives your Pixel an AI upgrade
- id: `tensor_g3`
- 作者/机构: Google
- 出处: 厂商原始资料 (2023)
- 核验状态: fulltext_checked
- 链接: https://blog.google/products/pixel/google-tensor-g3-pixel-8/
- 原文定位: 2023-10-04，正文 every major subsystem 与CPU/GPU/ISP/Imaging DSP/TPU段落。
- 支持: G3服务Pixel 8/8 Pro，官方声明升级多个计算和成像子系统，目标包含端侧AI。
- 不支持: 没有核验真实PPA、持续性能、ISP画质或商业成败。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `tensor_g3.html` · SHA-256 `9ed3a3b49fc64d2c4241f643a3d07ef1373c6051036269adf6fb7910d1720904`
### The new Pixel 9 phones bring you the best of Google AI
- id: `tensor_g4`
- 作者/机构: Google
- 出处: 厂商原始资料 (2024)
- 核验状态: fulltext_checked
- 链接: https://blog.google/products-and-platforms/devices/pixel/google-pixel-9-pro-xl/
- 原文定位: 2024-08-13，AI helpfulness, powered by Google Tensor G4段落。
- 支持: 确认Pixel 9系列使用G4，官方目标包括多模态端侧AI。
- 不支持: 厂商效率表述不是本作实测校准或失败证据。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `g4_spec.html` · SHA-256 `bc830175026f1b03865f92de76481b93a0ecee5b2187fd3c024ba28b66a88041`
### Powerful and proactive: Pixel 10 phones are here
- id: `tensor_g5`
- 作者/机构: Google
- 出处: 厂商原始资料 (2025)
- 核验状态: fulltext_checked
- 链接: https://blog.google/products-and-platforms/devices/pixel/google-pixel-10-pro-xl/
- 原文定位: 2025-08-20，Tensor G5与Gemini Nano及成像段落。
- 支持: 确认G5对应Pixel 10系列，官方描述其端侧AI和计算摄影目标。
- 不支持: 不证明真实持续性能、功耗或本作RC模型，也不构成失败判定。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `g5_spec.html` · SHA-256 `b5fef5223e088de55b7945399237dacb37de3b32057f4b531aba7b904cc9fbfc`
### The Pixel 11 series: Your most personal Pixel yet
- id: `tensor_g6`
- 作者/机构: Google
- 出处: 厂商原始资料 (2026)
- 核验状态: fulltext_checked
- 链接: https://blog.google/products-and-platforms/devices/pixel/google-pixel-11-pro-xl/
- 原文定位: 2026-08-12，All powered by Google Tensor G6与ISP/CPU/TPU说明。
- 支持: 确认Pixel 11系列/G6已经发布；官方描述CPU、TPU和ISP的升级方向。
- 不支持: 厂商给出的相对提升未独立复测；不映射为本作商业芯片数据或失败结论。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pixel11_spec.html` · SHA-256 `1e907d64a8561ddb928144b776543834bc86acafe046aa4c7a4cd41f6d88e7a3`
### Apple unveils iPhone 17 Pro and iPhone 17 Pro Max
- id: `apple_a19pro`
- 作者/机构: Apple Newsroom
- 出处: 厂商原始资料 (2025)
- 核验状态: fulltext_checked
- 链接: https://www.apple.com/newsroom/2025/09/apple-unveils-iphone-17-pro-and-iphone-17-pro-max/
- 原文定位: 2025-09-09，A19 Pro一节：6核CPU、GPU内置Neural Accelerators、16核Neural Engine。
- 支持: 确认A19 Pro的CPU/GPU/Neural Engine代际与GPU神经加速器位置。
- 不支持: 不公布CPU核心代号、解码宽度、ROB、每核缓存或本作IPC/PPA；不能称A20沿用此CPU。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `apple_a19.html` · SHA-256 `d87cf963a452f05bfce1a88019a64f128ad680311edcc900b067b896121fc4b9`
### Apple debuts iPhone 18 Pro and iPhone 18 Pro Max
- id: `apple_a20pro`
- 作者/机构: Apple Newsroom
- 出处: 厂商原始资料 (2026)
- 核验状态: fulltext_checked
- 链接: https://www.apple.com/newsroom/2026/09/apple-debuts-iphone-18-pro-and-iphone-18-pro-max/
- 原文定位: 2026-09-08，A20 Pro与封装/热设计两节。
- 支持: 新6核CPU内置Neural Accelerators、7核GPU、双16核Neural Engine、2nm；内存带宽相对A19 Pro增加50%。
- 不支持: 厂商相对提升不是本作实测；没有确认P/E分组频率、解码/ROB或精确缓存，不能拿A19或Sawtooth填空。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `apple_a20.html` · SHA-256 `8e2e102356c5fd31afd1104c2b0a1dbebd01c94ed132aed5b72511894c5f5bb1`
### Apple A20 Pro: Inside the iPhone 18 Pro’s TSMC 2nm Processor
- id: `techinsights_a20pro`
- 作者/机构: TechInsights
- 出处: 厂商原始资料 (2026)
- 核验状态: fulltext_checked
- 链接: https://www.techinsights.com/blog/apple-a20-pro-tsmc-2nm-processor-analysis
- 原文定位: 公开拆解说明：TSMC N2/GAA、约8.0×12.3mm计算die、封装。完整微架构报告未取得。
- 支持: 确认A20 Pro使用TSMC N2与GAA，计算die约98.2mm²；面积近似不意味着CPU结构相同。
- 不支持: 未核验付费报告的CPU内部管线/缓存细节；不能由die尺寸推导频率或IPC。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `a20_teardown.html` · SHA-256 `52bc1557560522af0bb3d49a77230393cd0424feba09246a01aa8ad034b38b91`
### Snapdragon 888 5G Mobile Platform · Product Brief
- id: `qcom_sd888`
- 作者/机构: Qualcomm
- 出处: 厂商原始资料 (2020)
- 核验状态: fulltext_checked
- 链接: https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/prod_brief_qcom_sd888_5g_1.pdf
- 原文定位: 2页官方简报，CPU/GPU/Camera/Memory/General Specifications；SM8350。
- 支持: Kryo680/Cortex-X1最高2.84GHz、Adreno660、Hexagon780、Spectra580、LPDDR5、5nm。
- 不支持: 26TOPS是AI Engine整体营销峰值；未提供CPU/GPU功率曲线、真实PPA或本作通关门槛。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `sd888_brief.pdf` · SHA-256 `4ea94100634b28cde06148e71a5e7a65e801e9cfbb33b4133377c9a3d940257f`
### Snapdragon 8 Elite Extreme Gen 6 · Product Brief
- id: `qcom_8ee6`
- 作者/机构: Qualcomm
- 出处: 厂商原始资料 (2026)
- 核验状态: fulltext_checked
- 链接: https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/Snapdragon-8-Elite-Extreme-Gen-6-Product-Brief.pdf
- 原文定位: Specs and features：2 Prime最高5.0GHz、6 Performance最高4.0GHz、16MB Flex Cache、Adreno矩阵核、三20-bit ISP。
- 支持: 明确芯片名称、CPU集群频率上限、Flex Cache与GPU矩阵核，不能再沿用Oryon3/Adreno850。
- 不支持: 不支持所谓黑屏根因、缓存电压耦合或能效退步的社区推测；不提供实测功耗曲线。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `sd8ee6_brief.pdf` · SHA-256 `73ae2311f28505bddf3bd9c012fd9b8f978ff0b025e008955e80f581c7e06dca`
### Geekbench 6 Benchmark Internals
- id: `geekbench6_method`
- 作者/机构: Primate Labs
- 出处: 厂商原始资料 (2024)
- 核验状态: fulltext_checked
- 链接: https://www.geekbench.com/doc/geekbench6-benchmark-internals.pdf
- 原文定位: May2024 pp7–9多核/ISA，p11 Scores：2500基准、分项几何平均与65/35整数/浮点加权。
- 支持: GB6包含CPU/内存工作负载和共享任务多核；分项与综合计分规则。
- 不支持: 不支持本作整数IPC×核数换算GB6，不提供任意芯片的性能校准或PPA。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。

## T3 · 独立评测
### HTC One M9／Snapdragon 810 原始测量定位（待核验）
- id: `snapdragon810`
- 作者/机构: AnandTech
- 出处: 原始测量定位 (2015)
- 核验状态: unverified_locator
- 链接: https://www.anandtech.com/show/9137/the-htc-one-m9-review
- 原文定位: 原始评测页面定位；当前请求未返回评测正文，不使用网上转述数字。
- 支持: 案例对象与待查的原始测量方向，不作为已核验的热/功耗结论。
- 不支持: 不能证明810的功耗、频率、温度、降频比例或本作热模型；设备/固件/环境未核验。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
### Galaxy S21 Ultra／Snapdragon 888 原始测量定位（待核验）
- id: `snapdragon888`
- 作者/机构: AnandTech
- 出处: 原始测量定位 (2021)
- 核验状态: unverified_locator
- 链接: https://www.anandtech.com/show/16446/the-samsung-galaxy-s21-ultra-exynos-and-snapdragon-review
- 原文定位: 原始评测页面定位；当前请求未返回评测正文，不与Exynos数据混用。
- 支持: 案例对象与待查测量方向，不作为已核验的芯片缺陷结论。
- 不支持: 不能证明888的功耗、结温、持续性能或本作通关门槛；固件/设备条件未核验。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
### Xiaomi Mi 11 review · Software and performance
- id: `mi11_original`
- 作者/机构: GSMArena
- 出处: 原始测量定位 (2021)
- 核验状态: fulltext_checked
- 链接: https://www.gsmarena.com/xiaomi_mi_11-review-2228p4.php
- 原文定位: 原评测Performance：X1/A78/A55、Adreno660；约22C，Wild Life 20轮在第12–14轮过热中止。
- 支持: 明确Mi11测试对象、CPU集群、GPU与特定压力测试未完成；普通游戏未见同样中止。
- 不支持: 不支持将整机过热等同于888芯片缺陷，不提供完整20轮最低分或可用于校准的芯片结温/功率。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `mi11_gsm.html` · SHA-256 `ee82d6de5d5508daff4c02252d9e4554dad373a09fb7996420651c9fd5c9406f`
### Google Pixel 9 Pro XL review
- id: `pixel9_original`
- 作者/机构: Notebookcheck
- 出处: 原始测量定位 (2024)
- 核验状态: fulltext_checked
- 链接: https://www.notebookcheck.net/Google-Pixel-9-Pro-XL-review-Top-smartphone-with-more-of-a-high-end-feeling-also-in-terms-of-price.911586.0.html
- 原文定位: Specifications与Performance/3DMark；1X4+3A720+4A520、Mali-G715 MP7。动态比较图与后来评测的同机记录分别保留。
- 支持: 确认G4集群与MP7 GPU；该整机在3DMark中降频。
- 不支持: 不能把动态图的平均值/范围当成单次稳定性；没有芯片PPA或结温曲线。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pixel9_nbc.html` · SHA-256 `2a49c8f776f10b21a98ac5dc385d32eb0f5791daa0a7ab6aafc59953711782c9`
### Google Pixel 11 Pro XL review
- id: `pixel11_original`
- 作者/机构: Digital Trends
- 出处: 原始测量定位 (2026)
- 核验状态: fulltext_checked
- 链接: https://www.digitaltrends.com/phones/google-pixel-11-pro-xl-review/
- 原文定位: 规格表与性能/测试方法：7核C1集群；3DMark Wild Life Extreme 3411分/20.43fps，20轮稳定性74.2%。
- 支持: 明确评测机、集群与所执行的工作负载；记录峰值和稳定性而非仅看温度。
- 不支持: 未公布精确GPU型号/电压曲线或热阻；不能把评测结果推广为所有Pixel11设备。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pixel11_dt.html` · SHA-256 `c7c390aa92d38533b835eabdf7f606a60a2f045f99bb1dfdf44fdb4aa2f7bc0e`
### HTC One M9 Smartphone Review
- id: `htc_m9_original`
- 作者/机构: Notebookcheck
- 出处: 原始测量定位 (2015)
- 核验状态: fulltext_checked
- 链接: https://www.notebookcheck.net/HTC-One-M9-Smartphone-Review.142065.0.html
- 原文定位: Specifications/Performance/Temperature；原文CPU段误写A15，但规格和芯片为A53，不能照抄
- 支持: 支持具体设备的架构记录与相应原始工作负载测量，数据版本/条件须随记录保留。
- 不支持: 不提供完整功率/电压/热阻或真实芯片内部微架构，不能把测量锚点或反事实估计当认证。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `m9_nbc.html` · SHA-256 `1573ace84a0e9393172c0a7aaff5f47d6aa78ecc243821f118f4ffcb1fd7cd12`
### Google Pixel 6 Pro review · Performance
- id: `pixel6_original`
- 作者/机构: GSMArena
- 出处: 原始测量定位 (2021)
- 核验状态: fulltext_checked
- 链接: https://www.gsmarena.com/google_pixel_6_pro-review-2343p4.php
- 原文定位: Performance：2X1+2A76+4A55，G78MP20；无壳20分钟Genshin、电池温度43C
- 支持: 支持具体设备的架构记录与相应原始工作负载测量，数据版本/条件须随记录保留。
- 不支持: 不提供完整功率/电压/热阻或真实芯片内部微架构，不能把测量锚点或反事实估计当认证。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pixel6_gsm.html` · SHA-256 `d19122fc913ddcaef938fc8c61bec53ba1b70c71d54b76f4210d7fa6a825e842`
### Google Pixel 7 Pro review
- id: `pixel7_original`
- 作者/机构: Notebookcheck
- 出处: 原始测量定位 (2022)
- 核验状态: fulltext_checked
- 链接: https://www.notebookcheck.net/Google-Pixel-7-Pro-review-Premium-smartphone-with-stock-Android.669256.0.html
- 原文定位: Specifications/3DMark稳定性表；本机G2与对照G1记录不混为同轮
- 支持: 支持具体设备的架构记录与相应原始工作负载测量，数据版本/条件须随记录保留。
- 不支持: 不提供完整功率/电压/热阻或真实芯片内部微架构，不能把测量锚点或反事实估计当认证。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pixel7_nbc.html` · SHA-256 `e45818f38f0fc45e7eded456ab458a59b9fb3655e739045daf30a5961afd504c`
### Google Pixel 8 Pro review
- id: `pixel8_original`
- 作者/机构: Notebookcheck
- 出处: 原始测量定位 (2023)
- 核验状态: fulltext_checked
- 链接: https://www.notebookcheck.net/Google-Pixel-8-Pro-review-Powerful-Android-smartphone-with-seven-years-of-updates.765989.0.html
- 原文定位: Geekbench6.7表、Specifications/Temperatures/3DMark；不是同页GB5.5
- 支持: 支持具体设备的架构记录与相应原始工作负载测量，数据版本/条件须随记录保留。
- 不支持: 不提供完整功率/电压/热阻或真实芯片内部微架构，不能把测量锚点或反事实估计当认证。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pixel8_nbc.html` · SHA-256 `8c3c8850e031d3cb1503e0a9ad925d90b52889d5537d901909e9d206e5161cca`
### Google Pixel 10 Pro XL Smartphone Review
- id: `pixel10_original`
- 作者/机构: Notebookcheck
- 出处: 原始测量定位 (2025)
- 核验状态: fulltext_checked
- 链接: https://www.notebookcheck.net/Google-Pixel-10-Pro-XL-Smartphone-Review-Gorgeous-flagship-that-offers-a-great-Android-experience-with-one-Achilles-heel.1100253.0.html
- 原文定位: Specifications/GB6.7/GPU API/Stress：G5PowerVR与G4对照，部分重测Android16QPR1
- 支持: 支持具体设备的架构记录与相应原始工作负载测量，数据版本/条件须随记录保留。
- 不支持: 不提供完整功率/电压/热阻或真实芯片内部微架构，不能把测量锚点或反事实估计当认证。
- 本作使用: 历史与目标说明；实验参数均为游戏假设，不据此标定商业PPA。
- 核验文件: `pixel10_nbc.html` · SHA-256 `a3feadd155ced230920e99ea920319e9bd5f50e90e50e60734c32c5de257af9a`

## T4 · 报道
