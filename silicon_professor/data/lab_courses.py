"""进阶课程：明确目标、可运行初始输入、参考解和逐项判定。"""
from __future__ import annotations

from copy import deepcopy
from ..engine.labs import DEFAULTS


def lesson(id, title, kind, lecture, initial, solution, goals, sources, explanation, prerequisites=()):
    return dict(id=id, title=title, kind=kind, lecture=lecture,
                initial=dict(deepcopy(DEFAULTS[kind]), **initial),
                solution=dict(deepcopy(DEFAULTS[kind]), **solution), goals=goals,
                sources=sources, explanation=explanation, prerequisites=list(prerequisites))


COURSES = [
    lesson("l01", "01 · 寄存器、ISA 与编码", "cpu",
        "ISA 规定软件可见状态和指令行为；流水线宽度、ROB 和工艺不是 ISA 的组成部分。RV32I 有 32 个 32 位整数寄存器，x0 固定为零，PC 是字节地址。这里程序先由汇编转换成指令对象，再显示真实的 32 位编码；不会从二进制编码重新解码取指。\n\nADDI x1,x0,42 将 12 位立即数扩展为 32 位并相加。对应编码为 0x02a00093。尝试写 x0 不会改变它；向 x1 写入 41 与 42 只是数据差异，硬件不因此变快。HALT 是本实验终止指令，没有标准 RISC-V 编码。\n\n任务：让 x1=42，仍保持 x0=0；运行后检查编码表、寄存器表和提交结果。",
        dict(source="ADDI x0,x0,9\nADDI x1,x0,41\nHALT"),
        dict(source="ADDI x0,x0,9\nADDI x1,x0,42\nHALT"),
        [dict(label="x1 为 42", type="register", reg=1, value=42), dict(label="x0 恒为 0", type="register", reg=0, value=0)],
        ["riscv_isa"], "将 x1 的立即数改为 42。x0 的写入被忽略，编码 0x02a00093 的 rd 字段为 x1。"),
    lesson("l02", "02 · 符号、移位与溢出", "cpu",
        "同一串 32 位比特可以解释为有符号或无符号整数。0xffffffff 的无符号值是 4294967295，有符号值是 -1。ADD/ADDI 只保留低 32 位，不产生溢出异常；SLT 使用有符号比较，SLTU 使用无符号比较。\n\nSRL 补零，SRA 复制最高位。对 0xfffffff8（-8）右移一位，SRL 得到 0x7ffffffc，SRA 得到 0xfffffffc（-4）。寄存器移位只看移位量低五位；立即数移位要求 0..31。\n\n任务：保留负数算术右移的语义，让 x3=-4；不要把 SRL 的巨大正整数当作计算错误，而要分析指令含义。",
        dict(source="ADDI x1,x0,-8\nSRLI x3,x1,1\nHALT"),
        dict(source="ADDI x1,x0,-8\nSRAI x3,x1,1\nHALT"),
        [dict(label="x3 = 0xfffffffc（-4）", type="register",reg=3,value=0xfffffffc),dict(label="实际使用 SRAI",type="uses",op="SRAI")],
        ["riscv_isa"], "将 SRLI 改为 SRAI。解释器显示 unsigned 与 signed 两种值；指令编码的 funct 位也不同。", ["l01"]),
    lesson("l03", "03 · M 扩展：除法的边界", "cpu",
        "M 是整数乘法与除法扩展，不是所有 RISC-V 核都自动具备。RV32 的 MUL 返回低 32 位，高位乘积分别由 MULH/MULHSU/MULHU 根据符号组合获得。DIV 向零截断，不是 Python 的向负无穷取整。\n\n因此 -7÷3 的商为 -2，余数为 -1。除零不是未定义：商全 1，余数为被除数；INT_MIN/-1 的商为 INT_MIN，余数为零。规范只规定结果，不规定乘除延迟，本实验延迟由左侧输入给定。\n\n任务：用 DIV/REM 算出结果，勾选 M，并看乘除单元较长的执行延迟如何影响依赖指令。",
        dict(source="ADDI x1,x0,-7\nADDI x2,x0,3\nADD x3,x1,x2\nSUB x4,x1,x2\nHALT"),
        dict(source="ADDI x1,x0,-7\nADDI x2,x0,3\nDIV x3,x1,x2\nREM x4,x1,x2\nHALT"),
        [dict(label="DIV 给出 -2",type="register",reg=3,value=0xfffffffe),dict(label="REM 给出 -1",type="register",reg=4,value=0xffffffff),dict(label="使用 DIV",type="uses",op="DIV")],
        ["riscv_m"], "替换为 DIV 与 REM，保持 M 开关启用。关闭 M 会得到明确的不支持指令错误。", ["l02"]),
    lesson("l04", "04 · 字节寻址与大小端", "cpu",
        "RV32 地址以字节为单位。LW 读取四字节，LB 读取一个字节并符号扩展，LBU 则零扩展；SW/SH/SB 分别写入 32/16/8 位。这里选择小端执行环境：最低地址放最低有效字节。\n\n写入 0x1234ff78 后，地址 0..3 是 78、ff、34、12。LB 从地址 1 取 ff 并扩展为 -1；LBU 得到 255。本执行环境拒绝非对齐半字/字访问，并提供 64KiB 数据存储。规范允许其它执行环境对非对齐访问采用不同处理方式。\n\n任务：只取地址 1 的无符号字节到 x2，验证没有错误读取整个字，也没有意外改变其它字节。",
        dict(source="LUI x1,0x12350\nADDI x1,x1,-136\nSW x1,0(x0)\nLB x2,1(x0)\nHALT"),
        dict(source="LUI x1,0x12350\nADDI x1,x1,-136\nSW x1,0(x0)\nLBU x2,1(x0)\nHALT"),
        [dict(label="x2 为 255",type="register",reg=2,value=255),dict(label="使用 LBU",type="uses",op="LBU")],
        ["riscv_isa"], "0x12350000-136=0x1234ff78。LBU 读取一个字节再零扩展。", ["l02"]),
    lesson("l05", "05 · 分支、循环与返回地址", "cpu",
        "分支比较寄存器并改变 PC，不会把标签地址当作绝对编码立即数：机器编码存的是相对分支 PC 的字节偏移。BNE 在不相等时跳转；BLT 与 BLTU 的符号解释不同。JAL 把 PC+4 写入 rd，JALR 的目标地址清除 bit0，未启用 C 的本实验要求四字节对齐。\n\n循环的正确性需要同时检查初值、更新和终止条件。这里每轮计数增加 1，目标为 5。BEQ 会在第一次计数不相等时直接退出，而 BNE 会继续循环直到计数达到 5。\n\n任务：运行一个恰好五次的循环。观察动态 PC 重复和分支造成的前端等待；本时序器不采用预测器，不能代表现代核心的分支行为。",
        dict(source="ADDI x1,x0,0\nADDI x2,x0,5\nloop:\nADDI x1,x1,1\nBEQ x1,x2,loop\nHALT"),
        dict(source="ADDI x1,x0,0\nADDI x2,x0,5\nloop:\nADDI x1,x1,1\nBNE x1,x2,loop\nHALT"),
        [dict(label="x1 达到 5",type="register",reg=1,value=5),dict(label="BNE 参与控制流",type="uses",op="BNE")],
        ["riscv_isa"], "将 BEQ 改为 BNE，运行轨迹里会出现五次更新。可把目标设为 0 体验循环上限错误。", ["l01"]),
    lesson("l06", "06 · Zbb 位操作与扩展声明", "cpu",
        "扩展不能只靠名字宣布支持，必须逐条定义指令行为、编码和验证。B 位操作规范包括多个子扩展；本实验实现 RV32 Zbb 的18条指令，包括布尔操作、计数、MIN/MAX、符号扩展、旋转和字节操作；没有进行第三方 ISA 合规认证。\n\nCPOP 返回设置为 1 的位数，不是数值大小；255 的低八位为 1，所以答案为 8。CLZ/CTZ 对零均返回 32。硬件加速能减少某个算法的指令数，但规范不规定具体延迟或能耗。本实验没有自动把扩展开关转成更高 SP 分。\n\n任务：启用RV32 Zbb 子集，并实际用 CPOP 算出 x2=8；关闭开关时应明确报错。",
        dict(source="ADDI x1,x0,255\nADDI x2,x0,255\nHALT"),
        dict(source="ADDI x1,x0,255\nCPOP x2,x1\nHALT",extensions=["M","Zbb"]),
        [dict(label="CPOP 得到 8",type="register",reg=2,value=8),dict(label="实际使用 CPOP",type="uses",op="CPOP")],
        ["riscv_zbb"], "启用 RV32 Zbb，再用 CPOP x2,x1。开启未实现的 A/F/D/C/V 不会被接受。", ["l02"]),
    lesson("l07", "07 · 数据冒险与可用并行度", "cpu",
        "多发射只决定一个周期最多处理多少指令，不保证程序存在足够并行度。RAW 表示后继需要前驱结果；WAR/WAW 可以通过重命名消除假依赖。ROB 维护按程序顺序提交，乱序执行不能随意改变软件可见结果。\n\n这个程序生成 48 个独立立即数，读取 x0，因此具有较高指令级并行度。把 dispatch/retire 宽度和执行端口从 1 增至 4，会减少周期；但如果改成 ADD x1,x1,x1 的依赖链，单纯增加宽度几乎不加速。\n\n任务：保留 48 条指令，将总周期降至 30 以内；检查每条 dispatch<issue<done≤retire。该模型没有分支推测、物理寄存器容量或真实 issue queue。",
        dict(source="\n".join(f"ADDI x{i%30+1},x0,{i}" for i in range(1,49))+"\nHALT",width=1,execution_ports=1),
        dict(source="\n".join(f"ADDI x{i%30+1},x0,{i}" for i in range(1,49))+"\nHALT",width=4,execution_ports=4),
        [dict(label="保留 48 条动态指令",type="metric",key="instructions",cmp="eq",value=48),dict(label="周期 ≤ 30",type="metric",key="cycles",cmp="le",value=30)],
        ["gem5","riscv_isa"], "将宽度与执行端口都设为 4。只增加前端宽度而端口仍为 1，瓶颈不会消失。", ["l01"]),
    lesson("l08", "08 · 组相联缓存与冲突", "cache",
        "缓存将地址拆成 block、set 和 tag。64B 行、1KiB 容量、direct mapped 时有 16 个 set，地址 0 与 1024 映射到同一个 set。即使工作集只有两行，交替访问也会不断冲突。\n\n两路组相联在相同容量下有八个 set，每个能容纳两行；同样的两个地址可以同时保存。替换采用 LRU 或 FIFO，写命中置 dirty，写 miss 为 write-allocate，dirty 淘汰计一次写回。本页的串行 AMAT 不含多请求并行、预取或协议开销。\n\n任务：保持容量为 1KiB 和六次交替访问，把 miss 降至 2。不要用删掉访问的方法伪装缓存优化。",
        dict(addresses="0 1024 0 1024 0 1024",capacity_kb=1,ways=1),
        dict(addresses="0 1024 0 1024 0 1024",capacity_kb=1,ways=2),
        [dict(label="保持六次访问",type="metric",key="accesses",cmp="eq",value=6),dict(label="只发生两次 miss",type="metric",key="misses",cmp="eq",value=2),dict(label="容量为 1KiB",type="input",key="capacity_kb",value=1)],
        ["gem5","cacti7"], "选择 two-way。容量没增加，只通过相联度减少冲突；CACTI 的物理延迟没有在本页实际运行。", ["l04"]),
    lesson("l09", "09 · AMAT、cold miss 与访存计数", "cache",
        "AMAT=命中延迟+miss率×miss额外代价。这里 miss_latency 输入的是总延迟，所以等价公式为 hit率×hit总延迟+miss率×miss总延迟。不要把总延迟再次加到 hit 上。\n\n地址 0、4、8 在同一个 64B 缓存行，只有第一次 cold miss。地址 64 在下一行，产生第二次 cold miss。hit=2 周期、miss总延迟=40 周期时，四次串行访问需 84 周期，AMAT=21。\n\n任务：保持访问与容量，得到 AMAT=21。真实系统的多个 miss 可重叠，AMAT 不一定等于整个程序每次访存的停顿。统计值仅适用于本次确定性轨迹。",
        dict(addresses="0 4 8 64",capacity_kb=1,ways=1,miss_latency=80),
        dict(addresses="0 4 8 64",capacity_kb=1,ways=1,miss_latency=40),
        [dict(label="四次访问",type="metric",key="accesses",cmp="eq",value=4),dict(label="AMAT = 21",type="metric",key="amat",cmp="eq",value=21)],
        ["gem5"], "将 miss 总延迟设为 40，不能设为 42 再重复计算 hit 部分。", ["l08"]),
    lesson("l10", "10 · NoC 路径与争用", "network",
        "网络延迟不能只比较平均跳数，还要看链路争用、注入模式和路由规则。这里单 flit 包逐跳存储转发，使用有向链路，链路每周期接收一包；包 ID 决定同周期仲裁。Mesh 采用先 X 再 Y 的确定性路由，Ring 选最短方向。\n\n三个包在周期 0 都从端点 0 到端点 1，会在同一链路排队；平均到达延迟为 2 周期。若三个包分别使用互不相同的链路 0→1、2→3、4→5，则都在 1 周期到达。\n\n任务：保持三个包和 Ring，改为分散流量，平均延迟≤1。本实验没有多 flit、有限 buffer、VC 或 credit，不能验证真实网络死锁。",
        dict(packets="0 1 0\n0 1 0\n0 1 0",count=8,topology="ring"),
        dict(packets="0 1 0\n2 3 0\n4 5 0",count=8,topology="ring"),
        [dict(label="保留三个包",type="packet_count",value=3),dict(label="平均延迟 ≤ 1",type="metric",key="avg_latency",cmp="le",value=1)],
        ["gem5"], "使用不共享同一有向链路的路径。平均跳数相同，排队延迟不同。", ["l08"]),
    lesson("l11", "11 · Setup 时序与流水线分割", "timing",
        "setup 检查要求数据在采样沿前稳定。此实验把每级 tCQ+组合路径合并为 delay，并加上 setup 与最坏时钟不确定度。required=delay+setup+uncertainty，slack=Tclock-required；最差 slack 为 WNS。\n\n2GHz 的周期为 500ps。若最长级为 450ps，加40ps setup和20ps不确定度，则 required=510ps，WNS=-10ps，setup 不满足。降低目标时钟或合理切分路径可以修复；切分会增加寄存器、延迟与时钟功耗。\n\n任务：保留2GHz，把最长级缩到400ps，得到WNS=40ps。此计算是给定级延迟的算术实验，没有 STA 网表、hold/OCV/多模式分析。",
        dict(delays="300 450",clock_ghz=2),dict(delays="300 400",clock_ghz=2),
        [dict(label="目标仍为 2GHz",type="input",key="clock_ghz",value=2),dict(label="WNS ≥ 40ps",type="metric",key="wns",cmp="ge",value=40)],
        ["gem5"], "500−400−40−20=40ps。这里由定义推导公式，gem5 只用于区分架构模拟与电路 STA；不是 setup 参数来源。", ["l07"]),
    lesson("l12", "12 · 电压平方与瞬态热", "power",
        "动态功耗使用 P=αCV²f。输入的 C 为等效开关电容而非热容；pF×10⁻¹²、GHz×10⁹ 必须正确换算。α 是活动因子，漏电另加。降电压会降低动态功耗，但这里没有验证降压后时序仍然成立。\n\n热部分是单节点 RC 的阶跃功耗解析解：ΔT(t)=Ptotal×R×(1−exp(−t/(RC)))，R为K/W，热容C为J/K，时间常数τ=RC。恒定漏电假设下，一个τ后升温达到稳态的约63.2%。\n\n任务：保持α=.2、开关电容1000pF、2GHz，将电压由1V降至.8V，使动态功耗≤.26W。这是功耗/热实验，不能单凭通过就宣称芯片能在低压流片。",
        dict(voltage=1),dict(voltage=.8),
        [dict(label="动态功耗 ≤ .26W",type="metric",key="dynamic_w",cmp="le",value=.26),dict(label="仍为 2GHz",type="input",key="frequency_ghz",value=2)],
        ["sankaranarayanan2005"], ".2×1000×10⁻¹²×.8²×2×10⁹=.256W；实际还需要电路延迟对电压的模型。", ["l11"]),
    lesson("l13", "13 · ALU：进位不等于溢出", "logic",
        "固定8位加法器保留低8位。无符号进位表示结果大于255；有符号溢出表示同号操作数得到异号结果。这两种标志回答不同的问题，不能混用。\n\n127+1=128，无符号没有进位，但128作为8位有符号数是-128，因此有符号溢出。255+1则得到低8位0且有进位，按有符号解释是-1+1=0，没有溢出。RISC-V基础整数加法不提供标志寄存器；本页的标志是用于理解门级算术的额外观测。\n\n任务：保留127+1，把位宽从16改为8，观察 signed=-128 与 overflow=true。此实验可执行ALU真值，未生成门级网表。",
        dict(a=127,b=1,bits=16),dict(a=127,b=1,bits=8),
        [dict(label="结果按 signed 为 -128",type="metric",key="signed",cmp="eq",value=-128),dict(label="溢出为 true",type="metric",key="overflow",cmp="eq",value=True)],
        ["riscv_isa"], "8位结果0x80；正+正得到负，溢出为真，进位为假。", ["l02"]),
]
COURSES.extend([
    lesson('l14','14 · x86 标志与条件跳转','cpu',
        'IA-32使用EAX/ECX/EDX/EBX等32位寄存器，ADD/SUB/CMP改变算术标志，MOV保持标志。JE读取ZF，JL比较SF与OF，JB读取CF；有符号和无符号条件不同。这里显示的标志观测值只包含算术位，不是整个EFLAGS状态。\n\n0xffffffff解释为-1，CMP EAX,1之后JL成立，但JB不成立。IMUL双操作数仅定义CF/OF，后面的JE不能假定ZF；本执行器会报告未定义标志使用。x86编码可变长，显示的PC按编码字节长度推进，HALT为实验标记。\n\n任务：按有符号比较跳转，使EDX=3。程序功能是原生x86子集，共同调度器不表示真实Intel uop拆解、解码或缓存层级。',
        dict(architecture='x86_32',extensions=[],source='MOV EAX,0xffffffff\nMOV EBX,1\nCMP EAX,EBX\nJB signed\nMOV EDX,9\nJMP done\nsigned:\nMOV EDX,3\ndone:\nHALT'),
        dict(architecture='x86_32',extensions=[],source='MOV EAX,0xffffffff\nMOV EBX,1\nCMP EAX,EBX\nJL signed\nMOV EDX,9\nJMP done\nsigned:\nMOV EDX,3\ndone:\nHALT'),
        [dict(label='EDX得到3',type='register',reg=2,value=3),dict(label='使用JL有符号条件',type='uses',op='JL')],
        ['intel_ia32'],'将JB改为JL：SF!=OF表示signed less；CF=0表示unsigned not below。',['l02']),
    lesson('l15','15 · AArch64 W/X与零寄存器','cpu',
        'AArch64的W0与X0是同一架构寄存器的不同宽度视图。写W0会把X0高32位清零；不是只改低32位并保留高位。XZR/WZR是零寄存器，但编码31在某些立即数和访存形式表示SP，不能把它们一概替换为零。\n\nMOV寄存器是ORR别名，立即数可以由MOVZ/MOVN/MOVK组合生成；本子集仅接受一条MOVZ/MOVN能表示的值，复杂伪指令会拒绝。CMP是SUBS到零寄存器，更新NZCV，C表示减法无借位，与x86的CF借位含义不同。\n\n任务：先设置X0=-1，再通过写W0=1使X0为1。保持命名一致并观察64位寄存器视图；此任务不证明完整Arm架构符合性。',
        dict(architecture='aarch64',extensions=[],source='MOV X0,#-1\nADD X1,X0,#1\nHALT'),
        dict(architecture='aarch64',extensions=[],source='MOV X0,#-1\nMOV W0,#1\nADD X1,X0,#1\nHALT'),
        [dict(label='X0为1，高32位清零',type='register',reg=0,value=1),dict(label='X1为2',type='register',reg=1,value=2)],
        ['arm_a64_isa'],'写W0而非X0的局部位修改；架构规范规定W写入清零高位。',['l01']),
    lesson('l16','16 · GPU SIMT与分歧成本','gpu',
        'GPU设计不能只数CU，需要定义线程、warp、执行路径、存储与吞吐。本实验为逐lane FP32计算，分支true路径执行mul/add，false路径执行square。一个warp内两类lane混合时必须按此模型分别执行路径；并没有同时让所有lane完成不同的指令。\n\nCUDA资料说明warp内分歧会影响效率，但本作warp4..64是研究参数，不是NVIDIA支持的所有宽度。这里不模拟PTX、FMA、纹理、光栅、barrier或真实shader缓存；总周期是计算和数据搬运相加，没有假定二者完美重叠。\n\n任务：保持64元素和分支任务，通过分散到更多SIMT处理器降低计算周期。输出每个lane仍与FP32参考一致，性能变化不能来自改变问题规模。',
        dict(task='branch',processors=1,elements=64),dict(task='branch',processors=4,elements=64),
        [dict(label='计算周期≤6',type='metric',key='compute_cycles',cmp='le',value=6),dict(label='保持64元素',type='input',key='elements',value=64)],
        ['cuda_simt'],'八个warp各需三周期；四处理器分配后计算六周期。带宽开销没有消失。',['l07']),
    lesson('l17','17 · NPU矩阵阵列与填充','npu',
        'NPU的TOPS必须同时定义精度、MAC计数和能达到的吞吐。这里每个PE每周期执行一个有符号整数MAC，一个MAC计两次运算；INT8/16是两种独立宽度设计假设，不按TPUv1的真实复用倍率实现。阵列填充、排空与tile数量影响实测吞吐，峰值不是整个模型速度。\n\n对8×8输出、K=8，4×4阵列要处理四个tile，每tile为K+r+c−2=14周期，共56。8×8阵列只需一个tile22周期，但需要更多PE、local storage和供电。外部传输周期独立计算，scratchpad不足阻止保存为验证IP；wrap溢出会让结果区别于无限精度整数参考。\n\n任务：保持8×8×8矩阵，把计算周期降到22。看准确整数与累加结果是否一致，再保存自定义NPU。',
        dict(rows=4,cols=4),dict(rows=8,cols=8),
        [dict(label='计算周期≤22',type='metric',key='compute_cycles',cmp='le',value=22),dict(label='保持512 MAC',type='metric',key='macs',cmp='eq',value=512)],
        ['tpu2017'],'将阵列改为8×8；总周期仍包含传输。论文的256×256真实TPU结构不意味着本作任意阵列已得到校准。',['l09']),
    lesson('l18','18 · ISP插值与图像流水线','isp',
        'ISP不是一个固定面积方块，而是与传感器采样、曝光和色彩处理相关的流水线。RGGB中green占一半位置，red和blue各占四分之一。missing channel的基础bilinear插值使用相邻同色样本平均；边缘缩小邻域是本作显式规则。\n\n黑电平应在插值前处理，增益与饱和会改变后续颜色；幂gamma并非标准sRGB OETF。引用文章讨论Malvar-He-Cutler的5×5改进，本作仅实现其介绍的bilinear baseline，未实现MHC。这里的functional_check是范围和形状检查，不声称图像质量最好或完整ISP验证。\n\n任务：保持8×8图像，将每周期像素数从1提升到4，计算周期降低而输出图像不应改变。真实流水线还需line buffer、精确固定点位宽、噪声/HDR/AWB/CCM等设计。',
        dict(pixels_per_cycle=1),dict(pixels_per_cycle=4),
        [dict(label='计算周期≤35',type='metric',key='compute_cycles',cmp='le',value=35),dict(label='仍为64像素',type='metric',key='pixels',cmp='eq',value=64)],
        ['demosaic2011'],'64/4 + 2×8 + 3=35周期；变吞吐不改变功能输出。仍需比较图像的真实误差与视觉表现。',['l04']),
])
COURSE_BY_ID = {c["id"]: c for c in COURSES}


def evaluate_course(course, inputs, result):
    checks = []
    for goal in course["goals"]:
        kind = goal["type"]
        if kind == "register": ok = result.get("registers", [])[goal["reg"]] == goal["value"]
        elif kind == "uses": ok = goal["op"] in result.get("used_ops", [])
        elif kind == "input": ok = inputs.get(goal["key"]) == goal["value"]
        elif kind == "packet_count": ok = len(result.get("packets", [])) == goal["value"]
        else:
            actual, wanted = result.get(goal["key"]), goal["value"]
            ok = actual is not None and ({"eq": lambda: abs(actual - wanted) < 1e-8, "le": lambda: actual <= wanted + 1e-8, "ge": lambda: actual >= wanted - 1e-8}[goal["cmp"]]())
        checks.append(bool(ok))
    return checks
