# PicoRV32 真实 RTL 资料包

上游： https://github.com/YosysHQ/picorv32

固定提交：`ef203c2b0a3fb793280f5114941416c425c5b461`。`picorv32.v`、`COPYING`、`README.md`来自此提交，未改动；SHA-256记录在`manifest.json`。

ISC许可允许使用和修改，分发时必须保留版权和许可。原文见`COPYING`。`tb_silicon.v`是本作单独编写的冒烟测试，不属于上游验证集。

真实RTL测试只实例化上游`picorv32`并观察ADDI/ADDI/SW把42写入0x100。它不代表完整RV32I合规、时序签核、CPU测试覆盖或可制造性。上游支持的M/C/IRQ等功能不在此固定测试范围。

游戏中的RV32实验调度器并不是PicoRV32的周期模型；命名IP库不会把其通用解析面积/频率标为此RTL的实际PPA。真实RTL测试的结果在独立入口显示，不参与SP评分。PicoRV32源码可用于学习和外部开源EDA流程。

需要Icarus Verilog（`iverilog`与`vvp`）。可运行：

```bash
.venv/bin/python tools/check_rtl.py
```

没有工具时返回unavailable，不伪报通过。运行过程使用临时目录和固定测试文件，不编译导入文件里附带的任意代码。
