# 指令编码参照

isa_opcode_masks.json 来自 RISC-V International 的 riscv-opcodes 仓库，2026-11-08 获取，采用 rv_i、rv32_i、rv_m、rv_zbb、rv32_zbb 的固定位定义。提取 canonical 指令，忽略已有 canonical 的缩写 pseudo-op；RV32 特有 ZEXT.H、REV8、RORI 使用对应 RV32 定义。

来源：https://github.com/riscv/riscv-opcodes/tree/master/extensions

许可：仓库 BSD-3-Clause。比对范围为 opcode/funct 等固定字段；另外的手算测试检查寄存器和立即数字段，以及语义边界。这不代替完整 ISA 合规认证。原始文件 SHA-256 记在 data/evidence.json 的规范核验记录中。
