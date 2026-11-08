# 可直接导入的教学设计

所有例子由 `tools/export_examples.py` 生成并重新导入，使用0.1.0-alpha.4与当前模型标识。修改硬件后在LAB重新验证发布；名称/硬件决定新设计资产身份，测试输入不参与身份。

| 文件 | 内容 | 观察目标 |
| --- | --- | --- |
| [studio-compute.sil](studio-compute.sil) | 2个设计台RV32实例、GPU、NPU、ISP，内嵌4个硬件设计与保留的模板选择 | 不传.cor也能恢复，并可编辑内嵌设计 |
| [template-soc.sil](template-soc.sil) | 全模板沙盒SoC，3种CPU与GPU/NPU/ISP模板 | 完整模板名称、模型与参考制程随文件保存 |
| [x86-workstation.sil](x86-workstation.sil) | x86工作站，使用可执行双发射顺序教学核心 | 模板含完整硬件，可在LAB编辑，尚无x86-64/OS |
| [studio-cpu.cor](studio-cpu.cor) | 参数化RV32核心 | 选择ISA/扩展、端口、队列和cache；固定多类验证 |
| [studio-gpu.cor](studio-gpu.cor) | 参数化SIMT计算核心 | 驻留warp、ALU延迟、发射间隔与lane宽度 |
| [studio-npu.cor](studio-npu.cor) | 参数化整数MAC阵列 | 阵列、精度、累加与本地容量 |
| [studio-isp.cor](studio-isp.cor) | 参数化ISP流水线 | 可旁路模块、量化、并行度与行缓冲 |
| [isqi-compute.sil](isqi-compute.sil) | 完整研究沙盒SoC，2个RV32 CPU实例、SIMT GPU、整数NPU与RGGB ISP | 无本地IP库也能还原，内嵌4项IP定义；本例通过游戏教学签核 |
| [rv32.cor](rv32.cor) | RV32I/M整数核 | 6×7=42，存储到地址0，再加载至x4 |
| [ia32.cor](ia32.cor) | x86 IA-32整数核 | IMUL结果42，MOV存储/加载后CMP产生ZF |
| [a64.cor](a64.cor) | AArch64整数核 | 64位MUL与STR/LDR，X4=42 |
| [gpu.cor](gpu.cor) | 64元素、8-lane warp、2个SIMT处理器 | FP32 AXPY逐lane结果与资源周期 |
| [npu.cor](npu.cor) | 8×8×8整数GEMM，4×4阵列 | 输出矩阵、累加器位宽与scratchpad占用 |
| [isp.cor](isp.cor) | 8×8 RGGB raw12图像流水线 | 原始帧、黑电平/增益、双线性去马赛克与输出量化 |

首页的“导入SoC”打开`.sil`。LAB设计台“导入.cor”建立草稿；验证/测试台查看时序或图像。旧资产会转换为可编辑硬件草稿，原身份保留。已发布IP页也显示当前SoC内嵌核心，双击编辑或导出。不同ISA的CPU例子分别使用，不混入同一应用集群。

GPU是计算模型，不包含图形API/驱动；ISP图像是可解释的测试输入，不是真实相机图像质量基准。通过教学签核与固定功能向量不代表真实RTL/PDK签核或完整ISA认证。

重新生成并检查：

```bash
.venv/bin/python tools/export_examples.py
```

结构、版本与摘要规则见[格式说明](../FORMAT.md)；逐课解释见[实验手册](../LAB_MANUAL.md)。

## 12份挑战参考方案

以下均在当前引擎导入后重新验收，通过项目目标与教学签核。完整攻略见[玩家手册](../guide/challenges.md)。

- [01 · 不赌频率档位](challenges/challenge_bin.sil)
- [02 · 把热预算还给机身](challenges/challenge_thermal.sil)
- [03 · 内存墙前的编译农场](challenges/challenge_bandwidth.sil)
- [04 · 串行代码的逆袭](challenges/challenge_serial.sil)
- [05 · 开放指令集的迁移账单](challenges/challenge_open.sil)
- [06 · 自己的顺序核心](challenges/challenge_lab_cpu.sil)
- [07 · 相机里的两种算力](challenges/challenge_camera.sil)
- [08 · 用驻留隐藏等待](challenges/challenge_simt.sil)
- [09 · 给封装留一毫米](challenges/challenge_compact.sil)
- [10 · 两颗Die的一张账单](challenges/challenge_chiplet.sil)
- [11 · 先进节点没有产能](challenges/challenge_supply.sil)
- [12 · 售价不替你省成本](challenges/challenge_margin.sil)
