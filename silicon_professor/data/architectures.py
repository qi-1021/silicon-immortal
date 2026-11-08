"""历史 ISA 家族注册表。列举不等于全集，未实现的执行器必须明确标注。"""
ISA_OPTIONS=[('riscv32','RISC-V · 32位（RV32）'),('x86_32','x86 · Intel/AMD 指令家族 · 32位（IA-32）'),('aarch64','Arm · 64位（AArch64）')]

def isa_name(isa):
    names=dict(ISA_OPTIONS)
    return names.get(isa,{'riscv':'RISC-V','armv8':'Arm · ARMv8','armv9':'Arm · ARMv9','x86_64':'x86 · 64位（AMD64 / Intel 64）'}.get(isa,isa))

ARCHITECTURES = {
    'riscv32':dict(name=isa_name('riscv32'),width='32',execution='implemented_subset',sources=['riscv_isa','riscv_m','riscv_zbb'],
        scope='RV32I整数/编码、M、18条RV32 Zbb；无特权/OS/二进制取指/浮点/向量。'),
    'x86_32':dict(name=isa_name('x86_32'),width='32',execution='implemented_subset',sources=['intel_ia32'],
        scope='8个E寄存器，MOV、ADD/SUB/CMP、布尔、双操作数IMUL、Jcc/JMP与32位MOV访存。无x87/SSE/AVX、段/页表、长模式或异常。'),
    'aarch64':dict(name=isa_name('aarch64'),width='32/64',execution='implemented_subset',sources=['arm_a64_isa'],
        scope='W/X整数、零寄存器/NZCV、MOV/ADD/SUB/布尔/MUL、B/BL/RET、LDR/STR子集；无SIMD/SVE/SME/EL/系统寄存器。'),
}
HISTORICAL = [
    ('x86_16','Intel 8086 / x86-16','16','段寻址、16位寄存器、兼容模式'),
    ('x86_64','AMD64 / Intel 64','64','长模式、REX、64位寄存器/地址、ABI'),
    ('arm32','Arm A32 / Thumb / T32','32','条件执行、Thumb混合长度、CPSR'),
    ('riscv64','RISC-V RV64','64','XLEN64、W指令与地址扩展'),
    ('mips','MIPS I–V / MIPS32 / MIPS64','32/64','分支延迟槽、HI/LO、CP0、浮点'),
    ('power','POWER / PowerPC / Power ISA','32/64','条件寄存器、link寄存器、端序与向量'),
    ('sparc','SPARC V8 / V9','32/64','寄存器窗口、延迟槽、trap'),
    ('alpha','DEC Alpha','64','整数/浮点寄存器、内存排序'),
    ('m68k','Motorola 68000 / 68k','16/32','D/A寄存器、有效地址与异常'),
    ('mos6502','MOS 6502','8','A/X/Y、零页、status、stack与decimal mode'),
    ('z80','Zilog Z80','8','双寄存器组、前缀、标志、I/O'),
    ('i8080','Intel 8080 / 8085','8','累加器、寄存器对、端口I/O'),
    ('pdp11','DEC PDP-11','16','通用寄存器、双操作数、寻址模式'),
    ('vax','DEC VAX','32','复杂寻址、可变长指令、特权'),
    ('s360','IBM System/360–370','32','PSW、通道I/O、浮点格式'),
    ('zarch','IBM z/Architecture','64','长历史兼容链、PSW、decimal与vector'),
    ('hppa','HP PA-RISC','32/64','延迟分支、nullification、space寄存器'),
    ('ia64','Intel IA-64 / Itanium','64','EPIC bundle、predication、寄存器栈'),
    ('m88000','Motorola 88000','32','RISC整数/浮点、流水线异常'),
    ('i960','Intel i960','32','嵌入式RISC、寄存器窗口'),
    ('i860','Intel i860','32/64','整数与向量/浮点双执行模型'),
    ('loongarch','LoongArch','32/64','整数/浮点/向量与系统寄存器'),
    ('avr','AVR','8','Harvard存储、寄存器与I/O'),
    ('pic','PIC','8/16/32','不同PIC家族ISA并不相同；bank/Harvard'),
    ('8051','Intel MCS-51 / 8051','8','内部/外部存储、SFR、位寻址'),
    ('msp430','TI MSP430','16/20','低功耗MCU、20位扩展'),
    ('superh','Renesas SuperH','32','定长指令、delay slot、浮点/媒体扩展'),
    ('riscv_e','RISC-V RV32E / RV64E','32/64','16个基础寄存器，与I寄存器集合不同'),
    ('transputer','INMOS Transputer','32','栈机器、通信链路'),
    ('cray','Cray vector families','64','向量寄存器、向量长度与链式执行'),
    ('tms320','TI TMS320 DSP families','varies','不同DSP ISA、定点/浮点、饱和与循环'),
    ('b5000','Burroughs B5000/B5500','word/stack','栈与标记存储模型'),
]
for key,name,width,scope in HISTORICAL:
    ARCHITECTURES[key]=dict(name=name,width=width,execution='catalog_only',sources=[],scope=scope+'；仅历史目录，未核验每代手册，不能用于执行/已验证IP。')

MODES={
    'beginner':dict(name='初级',level=0,description='先做功能实验，提示逐步完成；复杂资源参数折叠。'),
    'intermediate':dict(name='中级',level=1,description='展开缓存、并行与带宽，对照实验结果。'),
    'advanced':dict(name='高级',level=2,description='展开ISA、微架构、时序与加速器资源。'),
    'professional':dict(name='专业',level=3,description='完整输入、轨迹、原文和模型边界；不宣称真实PDK签核。'),
}
