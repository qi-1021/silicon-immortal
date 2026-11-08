"""RV32I 汇编语义、32 位编码及 RV32M/RV32 Zbb 指令。

单 hart、32 位寄存器、固定 4 字节指令、64KiB 小端数据存储。
ECALL/EBREAK 产生实验异常，无特权态/OS。HALT 是实验伪指令。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MASK = 0xffffffff
LOADS = {"LB": 8, "LH": 16, "LW": 32, "LBU": 8, "LHU": 16}
STORES = {"SB": 8, "SH": 16, "SW": 32}
BRANCHES = {"BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU", "JAL", "JALR"}
R_OPS = {"ADD", "SUB", "SLL", "SLT", "SLTU", "XOR", "SRL", "SRA", "OR", "AND"}
I_OPS = {"ADDI", "SLTI", "SLTIU", "XORI", "ORI", "ANDI", "SLLI", "SRLI", "SRAI"}
M_OPS = {"MUL", "MULH", "MULHSU", "MULHU", "DIV", "DIVU", "REM", "REMU"}
ZBB_OPS = {"ANDN", "ORN", "XNOR", "CLZ", "CTZ", "CPOP", "MIN", "MINU", "MAX", "MAXU",
           "SEXT.B", "SEXT.H", "ZEXT.H", "ROL", "ROR", "RORI", "ORC.B", "REV8"}
ZBB_R = {"ANDN", "ORN", "XNOR", "MIN", "MINU", "MAX", "MAXU", "ROL", "ROR"}
ZBB_UNARY = {"CLZ", "CTZ", "CPOP", "SEXT.B", "SEXT.H", "ZEXT.H", "ORC.B", "REV8"}


def instruction_catalog():
    base=R_OPS | I_OPS | set(LOADS) | set(STORES) | BRANCHES | {"LUI","AUIPC","FENCE","ECALL","EBREAK"}
    return {"RV32I":sorted(base),"M":sorted(M_OPS),"Zbb":sorted(ZBB_OPS)}


@dataclass(frozen=True)
class Instruction:
    op: str
    rd: int | None = None
    rs1: int | None = None
    rs2: int | None = None
    imm: int = 0
    text: str = ""


def signed(v):
    v &= MASK
    return v if v < 0x80000000 else v - 0x100000000


def write_memory(mem, address, bits, value):
    if bits not in (8,16,32,64):raise ValueError('访存位宽为8/16/32/64。')
    if address % (bits // 8):
        raise ValueError(f"非对齐 {bits} 位访存：{address:#x}")
    if not 0 <= address <= 65536 - bits // 8:
        raise ValueError("本实验数据内存地址范围为 0..65535。")
    for offset in range(bits//8):
        current=address+offset;word,shift=current&~3,(current&3)*8
        mask=255<<shift
        mem[word]=((mem.get(word,0)&~mask)|(((value>>(offset*8))&255)<<shift))&MASK


def read_memory(mem, address, bits):
    if bits not in (8,16,32,64):raise ValueError('访存位宽为8/16/32/64。')
    if address % (bits // 8) or not 0 <= address <= 65536 - bits // 8:
        raise ValueError(f"越界或非对齐 {bits} 位访存：{address:#x}")
    return sum(((mem.get((address+o)&~3,0)>>(((address+o)&3)*8))&255)<<(o*8) for o in range(bits//8))


def assemble(source, extensions=("M",)):
    if any(e not in ("M", "Zbb") for e in extensions):
        raise ValueError("执行器只支持 M 与RV32 Zbb 指令；A/F/D/C/V 尚未实现。")
    labels, lines = {}, []
    for raw in source.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line: continue
        if ":" in line:
            label, line = line.split(":", 1)
            label = label.strip()
            if not re.fullmatch(r"[A-Za-z_]\w*", label) or label in labels:
                raise ValueError(f"标签无效或重复：{label}")
            labels[label] = len(lines)
            line = line.strip()
        if line: lines.append(line)
    if not lines or len(lines) > 1024:
        raise ValueError("程序须为 1..1024 条静态指令。")

    def reg(s):
        if s == "zero": return 0
        if not re.fullmatch(r"x(?:[0-9]|[12][0-9]|3[01])", s):
            raise ValueError(f"寄存器必须为 x0..x31：{s}")
        return int(s[1:])

    def immediate(s, shift=False):
        v = int(s, 0)
        if not (0 <= v <= 31 if shift else -2048 <= v <= 2047):
            raise ValueError("移位立即数为 0..31；其他 I/S 立即数为 -2048..2047。")
        return v

    def memory_operand(s):
        m = re.fullmatch(r"(-?(?:0x[0-9a-fA-F]+|\d+))\((x\d+|zero)\)", s)
        if not m: raise ValueError("访存写法示例：LW x1, 0(x2)")
        return reg(m[2]), immediate(m[1])

    output = []
    for line in lines:
        words = re.split(r"[\s,]+", line)
        op, args = words[0].upper(), words[1:]
        if op in M_OPS and "M" not in extensions: raise ValueError(f"{op} 需要 M 扩展。")
        if op in ZBB_OPS and "Zbb" not in extensions: raise ValueError(f"{op} 需要 Zbb 开关。")
        kw = dict(op=op, text=line)
        if op in R_OPS | M_OPS | ZBB_R and len(args) == 3:
            kw.update(rd=reg(args[0]), rs1=reg(args[1]), rs2=reg(args[2]))
        elif op in I_OPS | {"RORI"} and len(args) == 3:
            kw.update(rd=reg(args[0]), rs1=reg(args[1]), imm=immediate(args[2], op in {"SLLI", "SRLI", "SRAI", "RORI"}))
        elif op in ZBB_UNARY and len(args) == 2:
            kw.update(rd=reg(args[0]), rs1=reg(args[1]))
        elif op in LOADS.keys() | STORES.keys() | {"JALR"} and len(args) == 2:
            r, imm = memory_operand(args[1])
            kw.update(rs1=r, imm=imm)
            kw["rs2" if op in STORES else "rd"] = reg(args[0])
        elif op in BRANCHES - {"JAL", "JALR"} and len(args) == 3:
            if args[2] not in labels: raise ValueError(f"未定义标签：{args[2]}")
            kw.update(rs1=reg(args[0]), rs2=reg(args[1]), imm=labels[args[2]])
        elif op == "JAL" and len(args) == 2:
            if args[1] not in labels: raise ValueError(f"未定义标签：{args[1]}")
            kw.update(rd=reg(args[0]), imm=labels[args[1]])
        elif op in {"LUI", "AUIPC"} and len(args) == 2:
            v = int(args[1], 0)
            if not -524288 <= v <= 1048575: raise ValueError("U 型立即数须能表示为 20 位。")
            kw.update(rd=reg(args[0]), imm=v)
        elif op == "FENCE" and len(args) == 2:
            def flags(s):
                if not s or any(c not in 'iorw' for c in s): raise ValueError("FENCE 域使用 i/o/r/w。")
                return sum(bit for c, bit in zip('iorw', (8, 4, 2, 1)) if c in s)
            kw.update(imm=flags(args[0]) << 4 | flags(args[1]))
        elif op in {"HALT", "ECALL", "EBREAK"} and not args:
            pass
        else:
            raise ValueError(f"不支持的指令或操作数：{line}")
        output.append(Instruction(**kw))
    return output


def encode(ins, pc=0):
    """真实 32 位编码；HALT 无 RISC-V 编码。分支标签转换为 PC 相对字节偏移。"""
    op, rd, a, b = ins.op, ins.rd or 0, ins.rs1 or 0, ins.rs2 or 0
    if op == "HALT": return None
    if op in ("LUI", "AUIPC"): return ((ins.imm & 0xfffff) << 12) | rd << 7 | (0x37 if op == "LUI" else 0x17)
    rmap = {"ADD": (0, 0), "SUB": (0, 32), "SLL": (1, 0), "SLT": (2, 0), "SLTU": (3, 0), "XOR": (4, 0), "SRL": (5, 0), "SRA": (5, 32), "OR": (6, 0), "AND": (7, 0), "ANDN": (7, 32), "ORN": (6, 32), "XNOR": (4, 32)}
    if op in M_OPS: rmap[op] = (("MUL", "MULH", "MULHSU", "MULHU", "DIV", "DIVU", "REM", "REMU").index(op), 1)
    rmap.update({"MIN":(4,5),"MINU":(5,5),"MAX":(6,5),"MAXU":(7,5),"ROL":(1,48),"ROR":(5,48),"ZEXT.H":(4,4)})
    if op in rmap:
        f3, f7 = rmap[op]
        return f7 << 25 | b << 20 | a << 15 | f3 << 12 | rd << 7 | 0x33
    if op in I_OPS | set(LOADS) | ZBB_UNARY | {"JALR", "RORI"}:
        f3 = {"ADDI": 0, "SLLI": 1, "SLTI": 2, "SLTIU": 3, "XORI": 4, "SRLI": 5, "SRAI": 5, "ORI": 6, "ANDI": 7, "LB": 0, "LH": 1, "LW": 2, "LBU": 4, "LHU": 5, "JALR": 0, "CLZ": 1, "CTZ": 1, "CPOP": 1,
              "SEXT.B":1,"SEXT.H":1,"ORC.B":5,"REV8":5,"RORI":5}[op]
        imm = ins.imm
        if op == "SRAI": imm |= 0x400
        if op in {"CLZ", "CTZ", "CPOP"}: imm = 0x600 + ("CLZ", "CTZ", "CPOP").index(op)
        if op in {"SEXT.B","SEXT.H","ORC.B","REV8"}:imm={"SEXT.B":0x604,"SEXT.H":0x605,"ORC.B":0x287,"REV8":0x698}[op]
        if op=="RORI":imm|=0x600
        opcode = 0x03 if op in LOADS else 0x67 if op == "JALR" else 0x13
        return (imm & 0xfff) << 20 | a << 15 | f3 << 12 | rd << 7 | opcode
    if op in STORES:
        imm = ins.imm & 0xfff
        return (imm >> 5) << 25 | b << 20 | a << 15 | {"SB": 0, "SH": 1, "SW": 2}[op] << 12 | (imm & 31) << 7 | 0x23
    if op in BRANCHES - {"JALR"}:
        off = ins.imm * 4 - pc
        if op == "JAL":
            v = off & 0x1fffff
            return ((v >> 20) & 1) << 31 | ((v >> 1) & 0x3ff) << 21 | ((v >> 11) & 1) << 20 | ((v >> 12) & 255) << 12 | rd << 7 | 0x6f
        if not -4096 <= off <= 4094: raise ValueError("B 型分支偏移超出编码范围。")
        v = off & 0x1fff
        f3 = {"BEQ": 0, "BNE": 1, "BLT": 4, "BGE": 5, "BLTU": 6, "BGEU": 7}[op]
        return ((v >> 12) & 1) << 31 | ((v >> 5) & 63) << 25 | b << 20 | a << 15 | f3 << 12 | ((v >> 1) & 15) << 8 | ((v >> 11) & 1) << 7 | 0x63
    if op == "FENCE": return ins.imm << 20 | 0x0f
    if op == "ECALL": return 0x00000073
    if op == "EBREAK": return 0x00100073
    raise ValueError(f"未实现编码：{op}")


def execute(program, memory=None, max_instructions=4096):
    regs, mem = [0] * 32, dict(memory or {})
    if any(not isinstance(a, int) or a % 4 or not 0 <= a < 65536 or not isinstance(v, int) for a, v in mem.items()):
        raise ValueError("初始内存用对齐的 32 位字地址与整数值。")
    mem = {a: v & MASK for a, v in mem.items()}
    trace, pc = [], 0
    while 0 <= pc < len(program):
        if len(trace) >= max_instructions: raise ValueError("超过动态指令上限；检查循环。")
        ins = program[pc]
        op = ins.op
        if op == "HALT": break
        a, b, imm = regs[ins.rs1 or 0], regs[ins.rs2 or 0], ins.imm
        value, address, next_pc = None, None, pc + 1
        if op in {"ADD", "ADDI"}: value = a + (imm if op == "ADDI" else b)
        elif op == "SUB": value = a - b
        elif op in {"SLL", "SLLI"}: value = a << ((imm if op == "SLLI" else b) & 31)
        elif op in {"SRL", "SRLI"}: value = a >> ((imm if op == "SRLI" else b) & 31)
        elif op in {"SRA", "SRAI"}: value = signed(a) >> ((imm if op == "SRAI" else b) & 31)
        elif op in {"SLT", "SLTI"}: value = int(signed(a) < (imm if op == "SLTI" else signed(b)))
        elif op in {"SLTU", "SLTIU"}: value = int(a < (imm & MASK if op == "SLTIU" else b))
        elif op in {"XOR", "XORI", "XNOR"}: value = a ^ (imm if op == "XORI" else b); value = ~value if op == "XNOR" else value
        elif op in {"AND", "ANDI", "ANDN"}: value = a & (imm if op == "ANDI" else ~b if op == "ANDN" else b)
        elif op in {"OR", "ORI", "ORN"}: value = a | (imm if op == "ORI" else ~b if op == "ORN" else b)
        elif op == "CLZ": value = 32 - a.bit_length()
        elif op == "CTZ": value = (a & -a).bit_length() - 1 if a else 32
        elif op == "CPOP": value = a.bit_count()
        elif op in {"MIN","MAX","MINU","MAXU"}:
            left,right=(a,b) if op.endswith('U') else (signed(a),signed(b))
            value=(min if op.startswith('MIN') else max)(left,right)
        elif op in {"SEXT.B","SEXT.H","ZEXT.H"}:
            bits=8 if op=='SEXT.B' else 16
            value=a&((1<<bits)-1)
            if op!='ZEXT.H' and value & (1<<(bits-1)):value-=1<<bits
        elif op in {"ROL","ROR","RORI"}:
            amount=(imm if op=='RORI' else b)&31
            value=(a<<amount)|(a>>((32-amount)&31)) if op=='ROL' else (a>>amount)|(a<<((32-amount)&31))
        elif op=='ORC.B':value=sum(255<<(i*8) for i in range(4) if (a>>(i*8))&255)
        elif op=='REV8':value=int.from_bytes(a.to_bytes(4,'little'),'big')
        elif op == "LUI": value = imm << 12
        elif op == "AUIPC": value = pc * 4 + (imm << 12)
        elif op in M_OPS:
            if op == "MUL": value = a * b
            elif op == "MULH": value = (signed(a) * signed(b)) >> 32
            elif op == "MULHSU": value = (signed(a) * b) >> 32
            elif op == "MULHU": value = (a * b) >> 32
            else:
                sa, sb = (signed(a), signed(b)) if op in {"DIV", "REM"} else (a, b)
                quotient = MASK if sb == 0 else abs(sa) // abs(sb) * (-1 if (sa < 0) != (sb < 0) else 1)
                remainder = sa if sb == 0 else sa - quotient * sb
                value = quotient if op in {"DIV", "DIVU"} else remainder
        elif op in LOADS:
            address = (a + imm) & MASK
            bits = LOADS[op]
            value = read_memory(mem, address, bits)
            if op in {"LB", "LH"} and value & (1 << (bits - 1)): value -= 1 << bits
        elif op in STORES:
            address = (a + imm) & MASK
            write_memory(mem, address, STORES[op], b)
        elif op in {"BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"}:
            taken = {"BEQ": a == b, "BNE": a != b, "BLT": signed(a) < signed(b), "BGE": signed(a) >= signed(b), "BLTU": a < b, "BGEU": a >= b}[op]
            if taken: next_pc = imm
        elif op == "JAL": value, next_pc = pc * 4 + 4, imm
        elif op == "JALR":
            value = pc * 4 + 4
            target = ((a + imm) & MASK) & ~1
            if target % 4: raise ValueError("未启用 C：JALR 目标必须 4 字节对齐。")
            if target >= len(program) * 4:
                raise ValueError("JALR 目标超出本实验的代码范围。")
            next_pc = target // 4
        elif op == "FENCE": pass  # 单 hart 顺序数据语义下，没有未完成的内存访问。
        elif op in {"ECALL", "EBREAK"}: raise ValueError(f"PC {pc * 4:#x}：{op} 触发异常；本实验没有执行环境/异常入口。")
        else: raise ValueError(f"未知指令：{op}")
        if ins.rd not in (None, 0): regs[ins.rd] = value & MASK
        regs[0] = 0
        trace.append(dict(id=len(trace), pc=pc * 4, instruction=ins, value=None if value is None else value & MASK,
                          address=address, store_value=b if op in STORES else None,
                          store_bits=STORES.get(op), encoding=encode(ins, pc * 4)))
        pc = next_pc
    return dict(registers=regs, memory=mem, trace=trace)
