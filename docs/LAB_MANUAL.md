# 实验室手册

当前游戏版本 `0.1.0-alpha.4`，模型 `analytic-v0.7+x86-studio-v1`。九个可运行工作台：核心与指令、GPU、NPU、ISP、缓存、互连、时序、功耗/热和数字逻辑。18节进阶实验课与14节产品设计课程互补。下面给出输入、观察目标、参考解、原文定位和实现边界。

## 先设计核心，再用实验验证

LAB默认打开核心设计台，可独立新建、命名、复制CPU/GPU/NPU/ISP。选择结构模块编辑硬件，在验证页运行固定向量，再发布.cor或加入研究沙盒SoC。测试程序/矩阵/校准值不参与硬件身份。具体步骤与可复现设计比较见[设计台指南](CORE_STUDIO.md)。

本手册的课程位于设计台“实验与教学”。课程配置是学习样例；核心设计不要求先完成课程。新的.sil同时携带自定义核心和模板名称/全参数，设计台IP页可直接编辑SoC内嵌核心。

## 从第一节实验开始

1. 在LAB点击“实验与教学”选择课程，读清要观察的寄存器、周期或图像输出。
2. 运行初始输入，记录结果；初始配置可能故意没有完成任务。
3. 每次只改变一个因素，再运行，对照输出与轨迹。先说明原因，再查看参考解。
4. 完成任务后给CPU/GPU/NPU/ISP命名，验证并保存至IP库；其他工作台导出实验记录。
5. 在研究沙盒实例化已保存IP。跨ISA替换应用CPU集群时，明确选择替换原集群。

学习模式只控制提示与参数展开程度，实验输入和底层计算相同。随时可以展开全部资源参数。

| 模式 | 入口重点 |
| --- | --- |
| 初级 | 先做功能实验，提示逐步完成；复杂资源参数折叠。 |
| 中级 | 展开缓存、并行与带宽，对照实验结果。 |
| 高级 | 展开ISA、微架构、时序与加速器资源。 |
| 专业 | 完整输入、轨迹、原文和模型边界；不宣称真实PDK签核。 |

## 结果的含义

- CPU有RV32、IA-32和AArch64整数子集；汇编经过解析再执行，不从二进制取指。各自的指令编码用于学习与核对。单执行上下文、小端、64KiB数据内存；未执行第三方完整合规测试。
- IA-32显示原生算术标志；双操作数IMUL后的未定义标志保留为未知，不能用它推导条件分支。A64区分W写入清零高32位、X64位、零寄存器与NZCV；不支持的SP形式明确报错。MOV立即数只接受一次MOVZ/MOVN能表示的值。
- 功能解释器产生动态轨迹；时序器按依赖与资源调度。结果值来自正确功能轨迹，不能把内部提交一致性检查当成独立硬件验证。
- ALU为1周期、乘除延迟由输入指定，发射单元均按教学流水化模型处理；不是真实乘除器设计。访存串行，没有store buffer/MSHR、分支推测、异常恢复或有限物理寄存器。
- 回放按已生成轨迹的提交时间更新架构寄存器，不是交互式执行环境，也不展现投机寄存器状态。
- 默认时序的cold cache对每次运行重新初始化；HALT不计为标准指令。顺序落出程序末尾视为实验结束，显式跳转出代码区报错。
- 三类CPU及GPU/NPU/ISP均能保存为实验IP，在研究沙盒实例化。模型分不能证明完整ISA兼容、驱动可用或商业授权；面积/功耗/Fmax仍来自未校准公式。
- GPU执行逐lane FP32 AXPY与分支分歧，未实现完整GPU ISA、shader与图形流水线；NPU执行整数GEMM并检查有限累加器与scratchpad。
- ISP实现RGGB raw12、黑电平、增益、基本双线性去马赛克和幂gamma/量化；黑帧和范围检查不能证明图像质量。它没有实现MHC算法、自动曝光/白平衡或完整sRGB传递函数。
- 独立PicoRV32入口编译固定上游RTL并观察ADDI/ADDI/SW后的写入42，只是冒烟测试。解析核心与其RTL时序独立；玩家配置不会自动生成可制造的RTL。

## 可运行架构与原文

### RISC-V · 32位（RV32）

RV32I整数/编码、M、18条RV32 Zbb；无特权/OS/二进制取指/浮点/向量。

- [The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)；fulltext_checked。定位：Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- [RISC-V Unprivileged ISA — M Extension for Integer Multiplication and Division](https://docs.riscv.org/reference/isa/v20260120/unpriv/m-st-ext.html)；fulltext_checked。定位：Multiplication；Division；Table 1: Semantics for division by zero and division overflow。
- [RISC-V Unprivileged ISA — RV32 Zbb Basic Bit-manipulation](https://docs.riscv.org/reference/isa/v20260120/unpriv/b-st-ext.html)；fulltext_checked。定位：Zbb: Extension for Basic bit-manipulation；18条RV32指令的各自 Description/Operation；riscv-opcodes rv_zbb/rv32_zbb 的固定位编码。

### x86 · Intel/AMD 指令家族 · 32位（IA-32）

8个E寄存器，MOV、ADD/SUB/CMP、布尔、双操作数IMUL、Jcc/JMP与32位MOV访存。无x87/SSE/AVX、段/页表、长模式或异常。

- [Intel 64 and IA-32 Architectures Software Developer’s Manual, Volumes 2A/2B](https://cdrdv2.intel.com/v1/dl/getContent/671199)；fulltext_checked。定位：Vol.2A ADD pp.3-14–3-15; CMP、IMUL pp.3-451–3-454; Jcc pp.3-499–3-503. Vol.2B MOV pp.4-27–4-31, Flags Affected: None.

### Arm · 64位（AArch64）

W/X整数、零寄存器/NZCV、MOV/ADD/SUB/布尔/MUL、B/BL/RET、LDR/STR子集；无SIMD/SVE/SME/EL/系统寄存器。

- [Arm A64 instruction pseudocode and encoding — 2026-03_rel mirror](https://www.scs.stanford.edu/~zyedidia/arm64/add_addsub_imm.html)；fulltext_checked。定位：ADD/SUBS immediate Operation and register31 treatment; MOV register alias of ORR; MOVZ/MOVN encodings; LDR unsigned offset; RET; Shared Pseudocode X accessor and AddWithCarry; B.cond ConditionHolds.

历史目录目前35项家族/模式。其余仅为目录，不能保存为可执行架构IP，也不声称已经收录所有历史ISA。

## 文件与IP复用

`.cor`是CPU/GPU/NPU/ISP定义，`kind`区分类别；`.sil`是完整SoC，内嵌所用IP，换机器不依赖本地库。两者是UTF-8 JSON，旧扩展名也可读取。游戏、结构、模型版本作为诊断信息保留，读取依据实际字段。导入重新运行模型与固定功能向量，不信任文件中的评分或验证标志。详见[格式说明](FORMAT.md)与[可直接导入的示例](examples/README.md)。

## 编码与扩展目录

### RV32I — 40 条

`ADD`, `ADDI`, `AND`, `ANDI`, `AUIPC`, `BEQ`, `BGE`, `BGEU`, `BLT`, `BLTU`, `BNE`, `EBREAK`, `ECALL`, `FENCE`, `JAL`, `JALR`, `LB`, `LBU`, `LH`, `LHU`, `LUI`, `LW`, `OR`, `ORI`, `SB`, `SH`, `SLL`, `SLLI`, `SLT`, `SLTI`, `SLTIU`, `SLTU`, `SRA`, `SRAI`, `SRL`, `SRLI`, `SUB`, `SW`, `XOR`, `XORI`

### M — 8 条

`DIV`, `DIVU`, `MUL`, `MULH`, `MULHSU`, `MULHU`, `REM`, `REMU`

### Zbb — 18 条

`ANDN`, `CLZ`, `CPOP`, `CTZ`, `MAX`, `MAXU`, `MIN`, `MINU`, `ORC.B`, `ORN`, `REV8`, `ROL`, `ROR`, `RORI`, `SEXT.B`, `SEXT.H`, `XNOR`, `ZEXT.H`

未实现的A/F/D/C/V/Zicsr/Zifencei不能启用。规范中的完整B还包含其它子扩展；RV64的W类指令不属于此RV32实现。

## 01 · 寄存器、ISA 与编码

ISA 规定软件可见状态和指令行为；流水线宽度、ROB 和工艺不是 ISA 的组成部分。RV32I 有 32 个 32 位整数寄存器，x0 固定为零，PC 是字节地址。这里程序先由汇编转换成指令对象，再显示真实的 32 位编码；不会从二进制编码重新解码取指。

ADDI x1,x0,42 将 12 位立即数扩展为 32 位并相加。对应编码为 0x02a00093。尝试写 x0 不会改变它；向 x1 写入 41 与 42 只是数据差异，硬件不因此变快。HALT 是本实验终止指令，没有标准 RISC-V 编码。

任务：让 x1=42，仍保持 x0=0；运行后检查编码表、寄存器表和提交结果。

### 必须观察的结果

- x1 为 42
- x0 恒为 0

### 初始输入

```json
{
  "source": "ADDI x0,x0,9\nADDI x1,x0,41\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 参考解

将 x1 的立即数改为 42。x0 的写入被忽略，编码 0x02a00093 的 rd 字段为 x1。

```json
{
  "source": "ADDI x0,x0,9\nADDI x1,x0,42\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 原文与使用范围

- [The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)；fulltext_checked。
- 定位：Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- 支持：x0 恒为零；32 位整数运算、12 位符号扩展立即数、分支/跳转、大小端与访存语义，FENCE 与环境调用。
- 不支持：本 lab 不实现特权态、执行环境、二进制取指、外设或全部非对齐访存行为，不能宣称完整 RISC-V 合规。
- 本作使用：isa.py 执行语义与 32 位编码的直接规范。HALT 为实验伪指令，不是标准指令。

## 02 · 符号、移位与溢出

同一串 32 位比特可以解释为有符号或无符号整数。0xffffffff 的无符号值是 4294967295，有符号值是 -1。ADD/ADDI 只保留低 32 位，不产生溢出异常；SLT 使用有符号比较，SLTU 使用无符号比较。

SRL 补零，SRA 复制最高位。对 0xfffffff8（-8）右移一位，SRL 得到 0x7ffffffc，SRA 得到 0xfffffffc（-4）。寄存器移位只看移位量低五位；立即数移位要求 0..31。

任务：保留负数算术右移的语义，让 x3=-4；不要把 SRL 的巨大正整数当作计算错误，而要分析指令含义。

### 必须观察的结果

- x3 = 0xfffffffc（-4）
- 实际使用 SRAI

### 初始输入

```json
{
  "source": "ADDI x1,x0,-8\nSRLI x3,x1,1\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 参考解

将 SRLI 改为 SRAI。解释器显示 unsigned 与 signed 两种值；指令编码的 funct 位也不同。

```json
{
  "source": "ADDI x1,x0,-8\nSRAI x3,x1,1\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 原文与使用范围

- [The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)；fulltext_checked。
- 定位：Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- 支持：x0 恒为零；32 位整数运算、12 位符号扩展立即数、分支/跳转、大小端与访存语义，FENCE 与环境调用。
- 不支持：本 lab 不实现特权态、执行环境、二进制取指、外设或全部非对齐访存行为，不能宣称完整 RISC-V 合规。
- 本作使用：isa.py 执行语义与 32 位编码的直接规范。HALT 为实验伪指令，不是标准指令。

## 03 · M 扩展：除法的边界

M 是整数乘法与除法扩展，不是所有 RISC-V 核都自动具备。RV32 的 MUL 返回低 32 位，高位乘积分别由 MULH/MULHSU/MULHU 根据符号组合获得。DIV 向零截断，不是 Python 的向负无穷取整。

因此 -7÷3 的商为 -2，余数为 -1。除零不是未定义：商全 1，余数为被除数；INT_MIN/-1 的商为 INT_MIN，余数为零。规范只规定结果，不规定乘除延迟，本实验延迟由左侧输入给定。

任务：用 DIV/REM 算出结果，勾选 M，并看乘除单元较长的执行延迟如何影响依赖指令。

### 必须观察的结果

- DIV 给出 -2
- REM 给出 -1
- 使用 DIV

### 初始输入

```json
{
  "source": "ADDI x1,x0,-7\nADDI x2,x0,3\nADD x3,x1,x2\nSUB x4,x1,x2\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 参考解

替换为 DIV 与 REM，保持 M 开关启用。关闭 M 会得到明确的不支持指令错误。

```json
{
  "source": "ADDI x1,x0,-7\nADDI x2,x0,3\nDIV x3,x1,x2\nREM x4,x1,x2\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 原文与使用范围

- [RISC-V Unprivileged ISA — M Extension for Integer Multiplication and Division](https://docs.riscv.org/reference/isa/v20260120/unpriv/m-st-ext.html)；fulltext_checked。
- 定位：Multiplication；Division；Table 1: Semantics for division by zero and division overflow。
- 支持：低/高乘积的符号组合；除法向零截断；除零商全 1、余数为被除数；INT_MIN/-1 的规定结果。
- 不支持：M 规范不指定乘除单元延迟、面积或功耗，不能由扩展开关凭空得出能效提升。
- 本作使用：M 指令语义与已实现指令表；延迟由 lab 输入给定。

## 04 · 字节寻址与大小端

RV32 地址以字节为单位。LW 读取四字节，LB 读取一个字节并符号扩展，LBU 则零扩展；SW/SH/SB 分别写入 32/16/8 位。这里选择小端执行环境：最低地址放最低有效字节。

写入 0x1234ff78 后，地址 0..3 是 78、ff、34、12。LB 从地址 1 取 ff 并扩展为 -1；LBU 得到 255。本执行环境拒绝非对齐半字/字访问，并提供 64KiB 数据存储。规范允许其它执行环境对非对齐访问采用不同处理方式。

任务：只取地址 1 的无符号字节到 x2，验证没有错误读取整个字，也没有意外改变其它字节。

### 必须观察的结果

- x2 为 255
- 使用 LBU

### 初始输入

```json
{
  "source": "LUI x1,0x12350\nADDI x1,x1,-136\nSW x1,0(x0)\nLB x2,1(x0)\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 参考解

0x12350000-136=0x1234ff78。LBU 读取一个字节再零扩展。

```json
{
  "source": "LUI x1,0x12350\nADDI x1,x1,-136\nSW x1,0(x0)\nLBU x2,1(x0)\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 原文与使用范围

- [The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)；fulltext_checked。
- 定位：Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- 支持：x0 恒为零；32 位整数运算、12 位符号扩展立即数、分支/跳转、大小端与访存语义，FENCE 与环境调用。
- 不支持：本 lab 不实现特权态、执行环境、二进制取指、外设或全部非对齐访存行为，不能宣称完整 RISC-V 合规。
- 本作使用：isa.py 执行语义与 32 位编码的直接规范。HALT 为实验伪指令，不是标准指令。

## 05 · 分支、循环与返回地址

分支比较寄存器并改变 PC，不会把标签地址当作绝对编码立即数：机器编码存的是相对分支 PC 的字节偏移。BNE 在不相等时跳转；BLT 与 BLTU 的符号解释不同。JAL 把 PC+4 写入 rd，JALR 的目标地址清除 bit0，未启用 C 的本实验要求四字节对齐。

循环的正确性需要同时检查初值、更新和终止条件。这里每轮计数增加 1，目标为 5。BEQ 会在第一次计数不相等时直接退出，而 BNE 会继续循环直到计数达到 5。

任务：运行一个恰好五次的循环。观察动态 PC 重复和分支造成的前端等待；本时序器不采用预测器，不能代表现代核心的分支行为。

### 必须观察的结果

- x1 达到 5
- BNE 参与控制流

### 初始输入

```json
{
  "source": "ADDI x1,x0,0\nADDI x2,x0,5\nloop:\nADDI x1,x1,1\nBEQ x1,x2,loop\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 参考解

将 BEQ 改为 BNE，运行轨迹里会出现五次更新。可把目标设为 0 体验循环上限错误。

```json
{
  "source": "ADDI x1,x0,0\nADDI x2,x0,5\nloop:\nADDI x1,x1,1\nBNE x1,x2,loop\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 原文与使用范围

- [The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)；fulltext_checked。
- 定位：Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- 支持：x0 恒为零；32 位整数运算、12 位符号扩展立即数、分支/跳转、大小端与访存语义，FENCE 与环境调用。
- 不支持：本 lab 不实现特权态、执行环境、二进制取指、外设或全部非对齐访存行为，不能宣称完整 RISC-V 合规。
- 本作使用：isa.py 执行语义与 32 位编码的直接规范。HALT 为实验伪指令，不是标准指令。

## 06 · Zbb 位操作与扩展声明

扩展不能只靠名字宣布支持，必须逐条定义指令行为、编码和验证。B 位操作规范包括多个子扩展；本实验实现 RV32 Zbb 的18条指令，包括布尔操作、计数、MIN/MAX、符号扩展、旋转和字节操作；没有进行第三方 ISA 合规认证。

CPOP 返回设置为 1 的位数，不是数值大小；255 的低八位为 1，所以答案为 8。CLZ/CTZ 对零均返回 32。硬件加速能减少某个算法的指令数，但规范不规定具体延迟或能耗。本实验没有自动把扩展开关转成更高 SP 分。

任务：启用RV32 Zbb 子集，并实际用 CPOP 算出 x2=8；关闭开关时应明确报错。

### 必须观察的结果

- CPOP 得到 8
- 实际使用 CPOP

### 初始输入

```json
{
  "source": "ADDI x1,x0,255\nADDI x2,x0,255\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 参考解

启用 RV32 Zbb，再用 CPOP x2,x1。开启未实现的 A/F/D/C/V 不会被接受。

```json
{
  "source": "ADDI x1,x0,255\nCPOP x2,x1\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M",
    "Zbb"
  ]
}
```

### 原文与使用范围

- [RISC-V Unprivileged ISA — RV32 Zbb Basic Bit-manipulation](https://docs.riscv.org/reference/isa/v20260120/unpriv/b-st-ext.html)；fulltext_checked。
- 定位：Zbb: Extension for Basic bit-manipulation；18条RV32指令的各自 Description/Operation；riscv-opcodes rv_zbb/rv32_zbb 的固定位编码。
- 支持：RV32 Zbb 18条指令的行为：ANDN/ORN/XNOR、CLZ/CTZ/CPOP、MIN/MINU/MAX/MAXU、SEXT.B/SEXT.H/ZEXT.H、ROL/ROR/RORI、ORC.B/REV8。
- 不支持：不支持 RV64 专用 W 指令、Zba/Zbs/Zbc 或完整 B；未通过第三方 ISA 合规套件。规范不指定执行延迟和物理面积。
- 本作使用：RV32 Zbb 的执行语义与编码；延迟和面积仍是本作假设。

## 07 · 数据冒险与可用并行度

多发射只决定一个周期最多处理多少指令，不保证程序存在足够并行度。RAW 表示后继需要前驱结果；WAR/WAW 可以通过重命名消除假依赖。ROB 维护按程序顺序提交，乱序执行不能随意改变软件可见结果。

这个程序生成 48 个独立立即数，读取 x0，因此具有较高指令级并行度。把 dispatch/retire 宽度和执行端口从 1 增至 4，会减少周期；但如果改成 ADD x1,x1,x1 的依赖链，单纯增加宽度几乎不加速。

任务：保留 48 条指令，将总周期降至 30 以内；检查每条 dispatch<issue<done≤retire。该模型没有分支推测、物理寄存器容量或真实 issue queue。

### 必须观察的结果

- 保留 48 条动态指令
- 周期 ≤ 30

### 初始输入

```json
{
  "source": "ADDI x2,x0,1\nADDI x3,x0,2\nADDI x4,x0,3\nADDI x5,x0,4\nADDI x6,x0,5\nADDI x7,x0,6\nADDI x8,x0,7\nADDI x9,x0,8\nADDI x10,x0,9\nADDI x11,x0,10\nADDI x12,x0,11\nADDI x13,x0,12\nADDI x14,x0,13\nADDI x15,x0,14\nADDI x16,x0,15\nADDI x17,x0,16\nADDI x18,x0,17\nADDI x19,x0,18\nADDI x20,x0,19\nADDI x21,x0,20\nADDI x22,x0,21\nADDI x23,x0,22\nADDI x24,x0,23\nADDI x25,x0,24\nADDI x26,x0,25\nADDI x27,x0,26\nADDI x28,x0,27\nADDI x29,x0,28\nADDI x30,x0,29\nADDI x1,x0,30\nADDI x2,x0,31\nADDI x3,x0,32\nADDI x4,x0,33\nADDI x5,x0,34\nADDI x6,x0,35\nADDI x7,x0,36\nADDI x8,x0,37\nADDI x9,x0,38\nADDI x10,x0,39\nADDI x11,x0,40\nADDI x12,x0,41\nADDI x13,x0,42\nADDI x14,x0,43\nADDI x15,x0,44\nADDI x16,x0,45\nADDI x17,x0,46\nADDI x18,x0,47\nADDI x19,x0,48\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 1,
  "rob_size": 32,
  "execution_ports": 1,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 参考解

将宽度与执行端口都设为 4。只增加前端宽度而端口仍为 1，瓶颈不会消失。

```json
{
  "source": "ADDI x2,x0,1\nADDI x3,x0,2\nADDI x4,x0,3\nADDI x5,x0,4\nADDI x6,x0,5\nADDI x7,x0,6\nADDI x8,x0,7\nADDI x9,x0,8\nADDI x10,x0,9\nADDI x11,x0,10\nADDI x12,x0,11\nADDI x13,x0,12\nADDI x14,x0,13\nADDI x15,x0,14\nADDI x16,x0,15\nADDI x17,x0,16\nADDI x18,x0,17\nADDI x19,x0,18\nADDI x20,x0,19\nADDI x21,x0,20\nADDI x22,x0,21\nADDI x23,x0,22\nADDI x24,x0,23\nADDI x25,x0,24\nADDI x26,x0,25\nADDI x27,x0,26\nADDI x28,x0,27\nADDI x29,x0,28\nADDI x30,x0,29\nADDI x1,x0,30\nADDI x2,x0,31\nADDI x3,x0,32\nADDI x4,x0,33\nADDI x5,x0,34\nADDI x6,x0,35\nADDI x7,x0,36\nADDI x8,x0,37\nADDI x9,x0,38\nADDI x10,x0,39\nADDI x11,x0,40\nADDI x12,x0,41\nADDI x13,x0,42\nADDI x14,x0,43\nADDI x15,x0,44\nADDI x16,x0,45\nADDI x17,x0,46\nADDI x18,x0,47\nADDI x19,x0,48\nHALT",
  "memory": "",
  "architecture": "riscv32",
  "width": 4,
  "rob_size": 32,
  "execution_ports": 4,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": [
    "M"
  ]
}
```

### 原文与使用范围

- [The gem5 Simulator](https://doi.org/10.1145/2024716.2024718)；fulltext_checked。
- 定位：pp.1–3：Abstract、§2 Overall Goals、CPU Models / Memory System；全文共 7 页。
- 支持：gem5 区分不同 CPU 模型、系统模式和内存模型；支持不同模拟详细度。
- 不支持：本作没有接入 gem5，不实现 gem5 O3CPU；论文不提供任意芯片的 IPC、面积或频率。
- 本作使用：解释功能模型与时序模型边界。CPU lab 是顺序轨迹 + 简化调度，与 gem5 相互独立。

- [The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)；fulltext_checked。
- 定位：Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- 支持：x0 恒为零；32 位整数运算、12 位符号扩展立即数、分支/跳转、大小端与访存语义，FENCE 与环境调用。
- 不支持：本 lab 不实现特权态、执行环境、二进制取指、外设或全部非对齐访存行为，不能宣称完整 RISC-V 合规。
- 本作使用：isa.py 执行语义与 32 位编码的直接规范。HALT 为实验伪指令，不是标准指令。

## 08 · 组相联缓存与冲突

缓存将地址拆成 block、set 和 tag。64B 行、1KiB 容量、direct mapped 时有 16 个 set，地址 0 与 1024 映射到同一个 set。即使工作集只有两行，交替访问也会不断冲突。

两路组相联在相同容量下有八个 set，每个能容纳两行；同样的两个地址可以同时保存。替换采用 LRU 或 FIFO，写命中置 dirty，写 miss 为 write-allocate，dirty 淘汰计一次写回。本页的串行 AMAT 不含多请求并行、预取或协议开销。

任务：保持容量为 1KiB 和六次交替访问，把 miss 降至 2。不要用删掉访问的方法伪装缓存优化。

### 必须观察的结果

- 保持六次访问
- 只发生两次 miss
- 容量为 1KiB

### 初始输入

```json
{
  "addresses": "0 1024 0 1024 0 1024",
  "capacity_kb": 1,
  "line_bytes": 64,
  "ways": 1,
  "policy": "lru",
  "hit_latency": 2,
  "miss_latency": 40
}
```

### 参考解

选择 two-way。容量没增加，只通过相联度减少冲突；CACTI 的物理延迟没有在本页实际运行。

```json
{
  "addresses": "0 1024 0 1024 0 1024",
  "capacity_kb": 1,
  "line_bytes": 64,
  "ways": 2,
  "policy": "lru",
  "hit_latency": 2,
  "miss_latency": 40
}
```

### 原文与使用范围

- [The gem5 Simulator](https://doi.org/10.1145/2024716.2024718)；fulltext_checked。
- 定位：pp.1–3：Abstract、§2 Overall Goals、CPU Models / Memory System；全文共 7 页。
- 支持：gem5 区分不同 CPU 模型、系统模式和内存模型；支持不同模拟详细度。
- 不支持：本作没有接入 gem5，不实现 gem5 O3CPU；论文不提供任意芯片的 IPC、面积或频率。
- 本作使用：解释功能模型与时序模型边界。CPU lab 是顺序轨迹 + 简化调度，与 gem5 相互独立。

- [CACTI 7: New Tools for Interconnect Exploration in Innovative Off-Chip Memories](https://doi.org/10.1145/3085572)；fulltext_checked。
- 定位：作者公开稿 p.1 Abstract；§1 Introduction；CACTI README 的 process-specific values。
- 支持：建模片外内存 I/O 的功率、时序、互连与拓扑；论文在明确系统配置下验证工具，并给出两种内存通道案例。
- 不支持：不是本作 LPDDR5X 控制器仿真，也没有用它计算 3/2nm SRAM 面积；论文中的 18%、22% 和成本收益不能迁移到本作或手机。
- 本作使用：缓存 lab 为标签/LRU 模拟，PPA 未调用 CACTI；本条只解释可提取延迟/能耗的真实工具需要哪些输入。

## 09 · AMAT、cold miss 与访存计数

AMAT=命中延迟+miss率×miss额外代价。这里 miss_latency 输入的是总延迟，所以等价公式为 hit率×hit总延迟+miss率×miss总延迟。不要把总延迟再次加到 hit 上。

地址 0、4、8 在同一个 64B 缓存行，只有第一次 cold miss。地址 64 在下一行，产生第二次 cold miss。hit=2 周期、miss总延迟=40 周期时，四次串行访问需 84 周期，AMAT=21。

任务：保持访问与容量，得到 AMAT=21。真实系统的多个 miss 可重叠，AMAT 不一定等于整个程序每次访存的停顿。统计值仅适用于本次确定性轨迹。

### 必须观察的结果

- 四次访问
- AMAT = 21

### 初始输入

```json
{
  "addresses": "0 4 8 64",
  "capacity_kb": 1,
  "line_bytes": 64,
  "ways": 1,
  "policy": "lru",
  "hit_latency": 2,
  "miss_latency": 80
}
```

### 参考解

将 miss 总延迟设为 40，不能设为 42 再重复计算 hit 部分。

```json
{
  "addresses": "0 4 8 64",
  "capacity_kb": 1,
  "line_bytes": 64,
  "ways": 1,
  "policy": "lru",
  "hit_latency": 2,
  "miss_latency": 40
}
```

### 原文与使用范围

- [The gem5 Simulator](https://doi.org/10.1145/2024716.2024718)；fulltext_checked。
- 定位：pp.1–3：Abstract、§2 Overall Goals、CPU Models / Memory System；全文共 7 页。
- 支持：gem5 区分不同 CPU 模型、系统模式和内存模型；支持不同模拟详细度。
- 不支持：本作没有接入 gem5，不实现 gem5 O3CPU；论文不提供任意芯片的 IPC、面积或频率。
- 本作使用：解释功能模型与时序模型边界。CPU lab 是顺序轨迹 + 简化调度，与 gem5 相互独立。

## 10 · NoC 路径与争用

网络延迟不能只比较平均跳数，还要看链路争用、注入模式和路由规则。这里单 flit 包逐跳存储转发，使用有向链路，链路每周期接收一包；包 ID 决定同周期仲裁。Mesh 采用先 X 再 Y 的确定性路由，Ring 选最短方向。

三个包在周期 0 都从端点 0 到端点 1，会在同一链路排队；平均到达延迟为 2 周期。若三个包分别使用互不相同的链路 0→1、2→3、4→5，则都在 1 周期到达。

任务：保持三个包和 Ring，改为分散流量，平均延迟≤1。本实验没有多 flit、有限 buffer、VC 或 credit，不能验证真实网络死锁。

### 必须观察的结果

- 保留三个包
- 平均延迟 ≤ 1

### 初始输入

```json
{
  "packets": "0 1 0\n0 1 0\n0 1 0",
  "count": 8,
  "topology": "ring",
  "link_latency": 1
}
```

### 参考解

使用不共享同一有向链路的路径。平均跳数相同，排队延迟不同。

```json
{
  "packets": "0 1 0\n2 3 0\n4 5 0",
  "count": 8,
  "topology": "ring",
  "link_latency": 1
}
```

### 原文与使用范围

- [The gem5 Simulator](https://doi.org/10.1145/2024716.2024718)；fulltext_checked。
- 定位：pp.1–3：Abstract、§2 Overall Goals、CPU Models / Memory System；全文共 7 页。
- 支持：gem5 区分不同 CPU 模型、系统模式和内存模型；支持不同模拟详细度。
- 不支持：本作没有接入 gem5，不实现 gem5 O3CPU；论文不提供任意芯片的 IPC、面积或频率。
- 本作使用：解释功能模型与时序模型边界。CPU lab 是顺序轨迹 + 简化调度，与 gem5 相互独立。

## 11 · Setup 时序与流水线分割

setup 检查要求数据在采样沿前稳定。此实验把每级 tCQ+组合路径合并为 delay，并加上 setup 与最坏时钟不确定度。required=delay+setup+uncertainty，slack=Tclock-required；最差 slack 为 WNS。

2GHz 的周期为 500ps。若最长级为 450ps，加40ps setup和20ps不确定度，则 required=510ps，WNS=-10ps，setup 不满足。降低目标时钟或合理切分路径可以修复；切分会增加寄存器、延迟与时钟功耗。

任务：保留2GHz，把最长级缩到400ps，得到WNS=40ps。此计算是给定级延迟的算术实验，没有 STA 网表、hold/OCV/多模式分析。

### 必须观察的结果

- 目标仍为 2GHz
- WNS ≥ 40ps

### 初始输入

```json
{
  "delays": "300 450",
  "clock_ghz": 2,
  "setup_ps": 40.0,
  "skew_ps": 20.0
}
```

### 参考解

500−400−40−20=40ps。这里由定义推导公式，gem5 只用于区分架构模拟与电路 STA；不是 setup 参数来源。

```json
{
  "delays": "300 400",
  "clock_ghz": 2,
  "setup_ps": 40.0,
  "skew_ps": 20.0
}
```

### 原文与使用范围

- [The gem5 Simulator](https://doi.org/10.1145/2024716.2024718)；fulltext_checked。
- 定位：pp.1–3：Abstract、§2 Overall Goals、CPU Models / Memory System；全文共 7 页。
- 支持：gem5 区分不同 CPU 模型、系统模式和内存模型；支持不同模拟详细度。
- 不支持：本作没有接入 gem5，不实现 gem5 O3CPU；论文不提供任意芯片的 IPC、面积或频率。
- 本作使用：解释功能模型与时序模型边界。CPU lab 是顺序轨迹 + 简化调度，与 gem5 相互独立。

## 12 · 电压平方与瞬态热

动态功耗使用 P=αCV²f。输入的 C 为等效开关电容而非热容；pF×10⁻¹²、GHz×10⁹ 必须正确换算。α 是活动因子，漏电另加。降电压会降低动态功耗，但这里没有验证降压后时序仍然成立。

热部分是单节点 RC 的阶跃功耗解析解：ΔT(t)=Ptotal×R×(1−exp(−t/(RC)))，R为K/W，热容C为J/K，时间常数τ=RC。恒定漏电假设下，一个τ后升温达到稳态的约63.2%。

任务：保持α=.2、开关电容1000pF、2GHz，将电压由1V降至.8V，使动态功耗≤.26W。这是功耗/热实验，不能单凭通过就宣称芯片能在低压流片。

### 必须观察的结果

- 动态功耗 ≤ .26W
- 仍为 2GHz

### 初始输入

```json
{
  "capacitance_pf": 1000.0,
  "activity": 0.2,
  "voltage": 1,
  "frequency_ghz": 2.0,
  "leakage_w": 0.2,
  "thermal_r": 5.0,
  "thermal_c": 2.0,
  "ambient": 25.0,
  "duration": 60.0
}
```

### 参考解

.2×1000×10⁻¹²×.8²×2×10⁹=.256W；实际还需要电路延迟对电压的模型。

```json
{
  "capacitance_pf": 1000.0,
  "activity": 0.2,
  "voltage": 0.8,
  "frequency_ghz": 2.0,
  "leakage_w": 0.2,
  "thermal_r": 5.0,
  "thermal_c": 2.0,
  "ambient": 25.0,
  "duration": 60.0
}
```

### 原文与使用范围

- [A Case for Thermal-Aware Floorplanning at the Microarchitectural Level](https://jilp.org/vol7/v7paper15.pdf)；fulltext_checked。
- 定位：p.1 Abstract；§2 Thermal Modeling；§3 Thermal-aware Floorplanning。刊物目录与 PDF 卷号存在差异，保留说明。
- 支持：在论文的工作负载与热模型中，布局通过横向热扩散影响热点和性能；结果依赖具体温度/互连模型。
- 不支持：不支持本作 24°C 功率密度系数或任意手机温度预测；不能从布局颜色推导热可靠性。
- 本作使用：布局热权衡的定性教材；功率密度模糊图不是论文热模型。

## 13 · ALU：进位不等于溢出

固定8位加法器保留低8位。无符号进位表示结果大于255；有符号溢出表示同号操作数得到异号结果。这两种标志回答不同的问题，不能混用。

127+1=128，无符号没有进位，但128作为8位有符号数是-128，因此有符号溢出。255+1则得到低8位0且有进位，按有符号解释是-1+1=0，没有溢出。RISC-V基础整数加法不提供标志寄存器；本页的标志是用于理解门级算术的额外观测。

任务：保留127+1，把位宽从16改为8，观察 signed=-128 与 overflow=true。此实验可执行ALU真值，未生成门级网表。

### 必须观察的结果

- 结果按 signed 为 -128
- 溢出为 true

### 初始输入

```json
{
  "op": "add",
  "a": 127,
  "b": 1,
  "bits": 16
}
```

### 参考解

8位结果0x80；正+正得到负，溢出为真，进位为假。

```json
{
  "op": "add",
  "a": 127,
  "b": 1,
  "bits": 8
}
```

### 原文与使用范围

- [The RISC-V Instruction Set Manual, Volume I — RV32I Base Integer Instruction Set](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html)；fulltext_checked。
- 定位：Integer Register State、Integer Computational Instructions、Control Transfer、Load and Store、Memory Ordering 与 Environment Call/Breakpoints；使用官方章节标题定位。
- 支持：x0 恒为零；32 位整数运算、12 位符号扩展立即数、分支/跳转、大小端与访存语义，FENCE 与环境调用。
- 不支持：本 lab 不实现特权态、执行环境、二进制取指、外设或全部非对齐访存行为，不能宣称完整 RISC-V 合规。
- 本作使用：isa.py 执行语义与 32 位编码的直接规范。HALT 为实验伪指令，不是标准指令。

## 14 · x86 标志与条件跳转

IA-32使用EAX/ECX/EDX/EBX等32位寄存器，ADD/SUB/CMP改变算术标志，MOV保持标志。JE读取ZF，JL比较SF与OF，JB读取CF；有符号和无符号条件不同。这里显示的标志观测值只包含算术位，不是整个EFLAGS状态。

0xffffffff解释为-1，CMP EAX,1之后JL成立，但JB不成立。IMUL双操作数仅定义CF/OF，后面的JE不能假定ZF；本执行器会报告未定义标志使用。x86编码可变长，显示的PC按编码字节长度推进，HALT为实验标记。

任务：按有符号比较跳转，使EDX=3。程序功能是原生x86子集，共同调度器不表示真实Intel uop拆解、解码或缓存层级。

### 必须观察的结果

- EDX得到3
- 使用JL有符号条件

### 初始输入

```json
{
  "source": "MOV EAX,0xffffffff\nMOV EBX,1\nCMP EAX,EBX\nJB signed\nMOV EDX,9\nJMP done\nsigned:\nMOV EDX,3\ndone:\nHALT",
  "memory": "",
  "architecture": "x86_32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": []
}
```

### 参考解

将JB改为JL：SF!=OF表示signed less；CF=0表示unsigned not below。

```json
{
  "source": "MOV EAX,0xffffffff\nMOV EBX,1\nCMP EAX,EBX\nJL signed\nMOV EDX,9\nJMP done\nsigned:\nMOV EDX,3\ndone:\nHALT",
  "memory": "",
  "architecture": "x86_32",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": []
}
```

### 原文与使用范围

- [Intel 64 and IA-32 Architectures Software Developer’s Manual, Volumes 2A/2B](https://cdrdv2.intel.com/v1/dl/getContent/671199)；fulltext_checked。
- 定位：Vol.2A ADD pp.3-14–3-15; CMP、IMUL pp.3-451–3-454; Jcc pp.3-499–3-503. Vol.2B MOV pp.4-27–4-31, Flags Affected: None.
- 支持：IA-32整数运算与标志、MOV不改标志、双操作数IMUL截断与CF/OF、Jcc条件及编码。IMUL后的PF/AF/ZF/SF未定义。
- 不支持：没有实现x86-64、段/页表、x87/SSE/AVX、异常、unaligned通用访存、完整编码取指或真实Intel/AMD微架构；SDM不支持本作PPA数字。
- 本作使用：arch_cpu.py IA-32原生子集，保持E寄存器和算术标志位位置。时序按共同模型，不把指令当真实固定latency/uops。

## 15 · AArch64 W/X与零寄存器

AArch64的W0与X0是同一架构寄存器的不同宽度视图。写W0会把X0高32位清零；不是只改低32位并保留高位。XZR/WZR是零寄存器，但编码31在某些立即数和访存形式表示SP，不能把它们一概替换为零。

MOV寄存器是ORR别名，立即数可以由MOVZ/MOVN/MOVK组合生成；本子集仅接受一条MOVZ/MOVN能表示的值，复杂伪指令会拒绝。CMP是SUBS到零寄存器，更新NZCV，C表示减法无借位，与x86的CF借位含义不同。

任务：先设置X0=-1，再通过写W0=1使X0为1。保持命名一致并观察64位寄存器视图；此任务不证明完整Arm架构符合性。

### 必须观察的结果

- X0为1，高32位清零
- X1为2

### 初始输入

```json
{
  "source": "MOV X0,#-1\nADD X1,X0,#1\nHALT",
  "memory": "",
  "architecture": "aarch64",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": []
}
```

### 参考解

写W0而非X0的局部位修改；架构规范规定W写入清零高位。

```json
{
  "source": "MOV X0,#-1\nMOV W0,#1\nADD X1,X0,#1\nHALT",
  "memory": "",
  "architecture": "aarch64",
  "width": 2,
  "rob_size": 32,
  "execution_ports": 2,
  "pipeline": 8,
  "cache_kb": 16,
  "hit_latency": 2,
  "miss_latency": 40,
  "multiply_latency": 3,
  "extensions": []
}
```

### 原文与使用范围

- [Arm A64 instruction pseudocode and encoding — 2026-03_rel mirror](https://www.scs.stanford.edu/~zyedidia/arm64/add_addsub_imm.html)；fulltext_checked。
- 定位：ADD/SUBS immediate Operation and register31 treatment; MOV register alias of ORR; MOVZ/MOVN encodings; LDR unsigned offset; RET; Shared Pseudocode X accessor and AddWithCarry; B.cond ConditionHolds.
- 支持：A64 W/X位宽、零寄存器与SP在不同形式中的差异、MOVZ/MOVN单指令立即数、NZCV、分支与unsigned-scaled访存编码。
- 不支持：镜像不是完整Arm架构手册；未实现EL/系统寄存器、SIMD/SVE/SME/原子、SP、所有寻址模式、二进制解码或第三方合规认证；不能据此得出核心面积与能耗。
- 本作使用：A64前端拒绝把immediate ADD/LDR的SP当XZR；MOV仅接收一条MOVZ/MOVN可表达立即数，不虚构多条伪指令的PC。

## 16 · GPU SIMT与分歧成本

GPU设计不能只数CU，需要定义线程、warp、执行路径、存储与吞吐。本实验为逐lane FP32计算，分支true路径执行mul/add，false路径执行square。一个warp内两类lane混合时必须按此模型分别执行路径；并没有同时让所有lane完成不同的指令。

CUDA资料说明warp内分歧会影响效率，但本作warp4..64是研究参数，不是NVIDIA支持的所有宽度。这里不模拟PTX、FMA、纹理、光栅、barrier或真实shader缓存；总周期是计算和数据搬运相加，没有假定二者完美重叠。

任务：保持64元素和分支任务，通过分散到更多SIMT处理器降低计算周期。输出每个lane仍与FP32参考一致，性能变化不能来自改变问题规模。

### 必须观察的结果

- 计算周期≤6
- 保持64元素

### 初始输入

```json
{
  "elements": 64,
  "warp_size": 8,
  "processors": 1,
  "task": "branch",
  "pattern": "alternating",
  "bandwidth_gbs": 16.0,
  "frequency_ghz": 1.0
}
```

### 参考解

八个warp各需三周期；四处理器分配后计算六周期。带宽开销没有消失。

```json
{
  "elements": 64,
  "warp_size": 8,
  "processors": 4,
  "task": "branch",
  "pattern": "alternating",
  "bandwidth_gbs": 16.0,
  "frequency_ghz": 1.0
}
```

### 原文与使用范围

- [CUDA Programming Guide — 2.3 Writing SIMT Kernels](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/writing-cuda-kernels.html)；fulltext_checked。
- 定位：Basics of SIMT; Global Memory / coalescing; shared-memory bank conflicts. Source page describes divergent code paths and 32-thread NVIDIA warps.
- 支持：SIMT每线程状态/控制流、warp内分歧、访存事务合并和bank冲突影响吞吐。
- 不支持：本作可调warp4–64是研究假设，不是CUDA支持的warp宽度；未运行CUDA、PTX或真实光栅pipeline，不声称模拟NVIDIA GPU。
- 本作使用：GPU lab计算FP32逐lane任务，并对分歧路径假设串行；两指令AXPY非FMA，传输与计算不重叠。

## 17 · NPU矩阵阵列与填充

NPU的TOPS必须同时定义精度、MAC计数和能达到的吞吐。这里每个PE每周期执行一个有符号整数MAC，一个MAC计两次运算；INT8/16是两种独立宽度设计假设，不按TPUv1的真实复用倍率实现。阵列填充、排空与tile数量影响实测吞吐，峰值不是整个模型速度。

对8×8输出、K=8，4×4阵列要处理四个tile，每tile为K+r+c−2=14周期，共56。8×8阵列只需一个tile22周期，但需要更多PE、local storage和供电。外部传输周期独立计算，scratchpad不足阻止保存为验证IP；wrap溢出会让结果区别于无限精度整数参考。

任务：保持8×8×8矩阵，把计算周期降到22。看准确整数与累加结果是否一致，再保存自定义NPU。

### 必须观察的结果

- 计算周期≤22
- 保持512 MAC

### 初始输入

```json
{
  "m": 8,
  "n": 8,
  "k": 8,
  "rows": 4,
  "cols": 4,
  "precision_bits": 8,
  "accumulator_bits": 32,
  "scratchpad_kb": 4,
  "bandwidth_gbs": 16.0,
  "frequency_ghz": 1.0
}
```

### 参考解

将阵列改为8×8；总周期仍包含传输。论文的256×256真实TPU结构不意味着本作任意阵列已得到校准。

```json
{
  "m": 8,
  "n": 8,
  "k": 8,
  "rows": 8,
  "cols": 8,
  "precision_bits": 8,
  "accumulator_bits": 32,
  "scratchpad_kb": 4,
  "bandwidth_gbs": 16.0,
  "frequency_ghz": 1.0
}
```

### 原文与使用范围

- [In-Datacenter Performance Analysis of a Tensor Processing Unit](https://arxiv.org/abs/1704.04760)；fulltext_checked。
- 定位：Abstract; §2 TPU Architecture / Figure 1–2: 256×256 MAC array, Accumulators, Unified Buffer; §4 roofline analysis.
- 支持：特定TPUv1的稠密矩阵阵列、本地缓冲、数据搬运与算力/带宽限制；原文INT16输入有吞吐降低，非统一同速实现。
- 不支持：本作不实现TPU ISA、92TOPS/28MiB或论文硬件精度时序；假设每PE每周期一个INT8/INT16 MAC，INT16需要独立更宽乘法器PPA估算；无稀疏/量化标定。
- 本作使用：NPU lab为整数GEMM与tile/scratchpad实验，不将论文实际TPU指标映射任意设计。

## 18 · ISP插值与图像流水线

ISP不是一个固定面积方块，而是与传感器采样、曝光和色彩处理相关的流水线。RGGB中green占一半位置，red和blue各占四分之一。missing channel的基础bilinear插值使用相邻同色样本平均；边缘缩小邻域是本作显式规则。

黑电平应在插值前处理，增益与饱和会改变后续颜色；幂gamma并非标准sRGB OETF。引用文章讨论Malvar-He-Cutler的5×5改进，本作仅实现其介绍的bilinear baseline，未实现MHC。这里的functional_check是范围和形状检查，不声称图像质量最好或完整ISP验证。

任务：保持8×8图像，将每周期像素数从1提升到4，计算周期降低而输出图像不应改变。真实流水线还需line buffer、精确固定点位宽、噪声/HDR/AWB/CCM等设计。

### 必须观察的结果

- 计算周期≤35
- 仍为64像素

### 初始输入

```json
{
  "width": 8,
  "height": 8,
  "black_level": 64,
  "gain": 1.0,
  "gamma": 2.2,
  "output_bits": 8,
  "pixels_per_cycle": 1,
  "bandwidth_gbs": 4.0,
  "frequency_ghz": 0.5
}
```

### 参考解

64/4 + 2×8 + 3=35周期；变吞吐不改变功能输出。仍需比较图像的真实误差与视觉表现。

```json
{
  "width": 8,
  "height": 8,
  "black_level": 64,
  "gain": 1.0,
  "gamma": 2.2,
  "output_bits": 8,
  "pixels_per_cycle": 4,
  "bandwidth_gbs": 4.0,
  "frequency_ghz": 0.5
}
```

### 原文与使用范围

- [Malvar-He-Cutler Linear Image Demosaicking](https://doi.org/10.5201/ipol.2011.g_mhcd)；fulltext_checked。
- 定位：§1 Introduction / Figure 2 Bayer pattern; §2 Algorithm, initial bilinear green axial-neighbor and red/blue diagonal-neighbor formulas.
- 支持：Bayer采样与demosaic问题；文章先介绍bilinear baseline再讨论Malvar-He-Cutler的5×5跨通道校正。
- 不支持：本作只实现基础bilinear，未实现论文MHC 5×5改进；边缘缩小邻域与gamma/black-level是本作规则，未由论文验证；不是完整相机ISP。
- 本作使用：ISP lab讲解bilinear插值、black-level、幂gamma与输出量化；原文MHC仅为延伸阅读。
