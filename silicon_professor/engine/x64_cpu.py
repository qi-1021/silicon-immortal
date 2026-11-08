"""x86-64整数教学子集：16 GPR、32位写零扩展、REX和有限访存。

Intel SDM Vol.2 MOV/算术/IMUL/shift/Jcc对应形式；无OS/分页/SIMD。
汇编执行，编码作学习核对；不从机器码取指。地址空间暂限64KiB且对齐。
"""
import re
from .isa import Instruction,read_memory,write_memory
from .arch_cpu import parse_lines,integer,flag_pack

REGS=['RAX','RCX','RDX','RBX','RSP','RBP','RSI','RDI']+[f'R{i}' for i in range(8,16)]
ALIASES=['EAX','ECX','EDX','EBX','ESP','EBP','ESI','EDI']+[f'R{i}D' for i in range(8,16)]
REGMAP={name:(i,bits) for bits,names in [(64,REGS),(32,ALIASES)] for i,name in enumerate(names)}
JCC={'JE':0x84,'JZ':0x84,'JNE':0x85,'JNZ':0x85,'JL':0x8c,'JGE':0x8d,'JB':0x82,'JAE':0x83,'JG':0x8f,'JLE':0x8e,'JA':0x87,'JBE':0x86}
ARITH={'ADD':(0x01,0),'OR':(0x09,1),'AND':(0x21,4),'SUB':(0x29,5),'XOR':(0x31,6),'CMP':(0x39,7)}


def operand(value):
    s=value.strip().upper()
    if s in REGMAP:return ('reg',*REGMAP[s])
    if s.startswith('[') and s.endswith(']'):
        m=re.fullmatch(r'(RAX|RCX|RDX|RBX|RSP|RBP|RSI|RDI|R(?:[89]|1[0-5]))(?:\s*([+-])\s*(0X[\dA-F]+|\d+))?',s[1:-1].strip())
        if not m:raise ValueError('64位访存写作[RAX+8]，只支持64位基址+disp32；未实现绝对/RIP/索引寻址。')
        disp=integer(m[3] or '0')*(-1 if m[2]=='-' else 1)
        if not -(1<<31)<=disp<(1<<31):raise ValueError('位移须可编码为有符号disp32。')
        return ('mem',REGMAP[m[1]][0],disp)
    return ('imm',integer(s),0)


def rex(bits,r=0,b=0):
    value=0x40|(8 if bits==64 else 0)|(4 if r>=8 else 0)|(1 if b>=8 else 0)
    return bytes([value]) if value!=0x40 else b''


def signed(value,bits):return value-(1<<bits) if value&(1<<(bits-1)) else value


def encode_binary(op,dst,src):
    register=dst if dst[0]=='reg' else src
    if register[0]!='reg':raise ValueError('当前访存需要另一方为寄存器。')
    bits=register[2]
    if dst[0]=='reg' and src[0]=='reg' and dst[2]!=src[2]:raise ValueError('x86操作数位宽须相同。')
    if op=='MOV' and src[0]=='imm':
        if dst[0]!='reg':raise ValueError('当前不支持MOV立即数到内存。')
        value=src[1]
        if not -(1<<(bits-1))<=value<(1<<bits):raise ValueError('MOV立即数超出目标位宽。')
        return rex(bits,b=dst[1])+bytes([0xb8+(dst[1]&7)])+(value&((1<<bits)-1)).to_bytes(bits//8,'little')
    if op=='MOV' and (src[0]=='mem' or dst[0]=='mem'):
        mem=src if src[0]=='mem' else dst;r=register[1];base=mem[1];low=base&7
        return rex(bits,r,base)+bytes([0x8b if src[0]=='mem' else 0x89,0x80|((r&7)<<3)|low])+(b'\x24' if low==4 else b'')+(mem[2]&0xffffffff).to_bytes(4,'little')
    if dst[0]!='reg' or src[0]=='mem':raise ValueError('算术仅实现寄存器目标与寄存器/立即数源。')
    if op in ('SHL','SHR','SAR'):
        if src[0]!='imm' or not 0<=src[1]<=255:raise ValueError('移位只支持imm8计数。')
        return rex(bits,b=dst[1])+bytes([0xc1,0xc0|({'SHL':4,'SHR':5,'SAR':7}[op]<<3)|(dst[1]&7),src[1]])
    if src[0]=='reg':
        if op=='IMUL':return rex(bits,dst[1],src[1])+bytes([0x0f,0xaf,0xc0|((dst[1]&7)<<3)|(src[1]&7)])
        return rex(bits,src[1],dst[1])+bytes([0x89 if op=='MOV' else ARITH[op][0],0xc0|((src[1]&7)<<3)|(dst[1]&7)])
    if op=='IMUL':raise ValueError('当前IMUL只支持两操作数寄存器形式。')
    value=src[1]
    if not -(1<<31)<=value<((1<<31) if bits==64 else (1<<32)):
        raise ValueError('64位算术立即数必须能由imm32符号扩展表示。')
    return rex(bits,b=dst[1])+bytes([0x81,0xc0|(ARITH[op][1]<<3)|(dst[1]&7)])+(value&0xffffffff).to_bytes(4,'little')


def execute_x64(source,memory=None,max_instructions=4096):
    labels,lines=parse_lines(source);parsed=[];listing=[];addresses=[];pc=0
    for line in lines:
        parts=line.split(None,1);op=parts[0].upper();args=[a.strip() for a in parts[1].split(',')] if len(parts)>1 else []
        if op=='HALT' and not args:ops=[];raw=b''
        elif (op=='JMP' or op in JCC) and len(args)==1:
            if args[0] not in labels:raise ValueError('找不到分支标签。')
            ops=[labels[args[0]]];raw=(b'\xe9' if op=='JMP' else bytes([0x0f,JCC[op]]))+b'\0'*4
        elif op in set(ARITH)|{'MOV','IMUL','SHL','SHR','SAR'} and len(args)==2:
            ops=[operand(a) for a in args];raw=encode_binary(op,*ops)
        else:raise ValueError('未实现x86-64指令或形式：'+line)
        parsed.append((op,ops));addresses.append(pc);listing.append(dict(pc=pc,text=line,op=op,word=None,bytes=raw.hex()));pc+=len(raw) or 1
    for i,(op,ops) in enumerate(parsed):
        if op=='JMP' or op in JCC:
            raw=bytes.fromhex(listing[i]['bytes']);offset=addresses[ops[0]]-addresses[i]-len(raw)
            listing[i]['bytes']=(raw[:-4]+(offset&0xffffffff).to_bytes(4,'little')).hex()
    registers=[0]*17;mem=dict(memory or {});flags={k:False for k in ('CF','PF','AF','ZF','SF','OF')};trace=[];ip=0
    while 0<=ip<len(parsed):
        if len(trace)>=max_instructions:raise ValueError('动态指令超过上限。')
        op,ops=parsed[ip]
        if op=='HALT':break
        sources=[];writes={};address=None;store_value=None;store_bits=None;rd=None;norm='ADD';next_ip=ip+1
        def read(o,bits):
            if o[0]=='imm':return o[1]&((1<<bits)-1)
            sources.append(o[1])
            if o[0]=='reg':return registers[o[1]]&((1<<bits)-1)
            return read_memory(mem,(registers[o[1]]+o[2])&((1<<64)-1),bits)
        if op=='JMP' or op in JCC:
            norm='JAL'
            required={'JE':('ZF',),'JZ':('ZF',),'JNE':('ZF',),'JNZ':('ZF',),'JL':('SF','OF'),'JGE':('SF','OF'),'JB':('CF',),'JAE':('CF',),'JG':('ZF','SF','OF'),'JLE':('ZF','SF','OF'),'JA':('CF','ZF'),'JBE':('CF','ZF')}.get(op,())
            if required:
                sources.append(16)
                if any(flags[k] is None for k in required):raise ValueError('分支使用了未定义标志；先CMP或有效算术。')
            f=flags
            taken={'JMP':True,'JE':f['ZF'],'JZ':f['ZF'],'JNE':not f['ZF'],'JNZ':not f['ZF'],'JL':f['SF']!=f['OF'],'JGE':f['SF']==f['OF'],'JB':f['CF'],'JAE':not f['CF'],'JG':not f['ZF'] and f['SF']==f['OF'],'JLE':f['ZF'] or f['SF']!=f['OF'],'JA':not f['CF'] and not f['ZF'],'JBE':f['CF'] or f['ZF']}[op]
            if taken:next_ip=ops[0]
        else:
            dst,src=ops;bits=(dst if dst[0]=='reg' else src)[2];mask=(1<<bits)-1;sign=1<<(bits-1)
            right=read(src,bits);left=read(dst,bits) if op!='MOV' else 0
            full=right if op=='MOV' else left+right if op=='ADD' else left-right if op in ('SUB','CMP') else left&right if op=='AND' else left|right if op=='OR' else left^right if op=='XOR' else signed(left,bits)*signed(right,bits) if op=='IMUL' else 0
            result=full&mask;flags_changed=True
            if op in ('SHL','SHR','SAR'):
                count=right&(63 if bits==64 else 31)
                if not count:flags_changed=False;result=left
                else:
                    result=((left<<count) if op=='SHL' else (left>>count) if op=='SHR' else (signed(left,bits)>>count))&mask
                    flags['CF']=bool((left>>(bits-count))&1) if op=='SHL' else bool((left>>(count-1))&1)
                    flags['OF']=(bool(result&sign)^flags['CF'] if op=='SHL' else bool(left&sign) if op=='SHR' else False) if count==1 else None
                    flags.update(AF=None,ZF=result==0,SF=bool(result&sign),PF=(result&255).bit_count()%2==0)
            elif op=='IMUL':
                flags.update(CF=signed(result,bits)!=full,OF=signed(result,bits)!=full,PF=None,AF=None,ZF=None,SF=None);norm='MUL'
            elif op!='MOV':
                sub=op in ('SUB','CMP');arithmetic=op in ('ADD','SUB','CMP')
                flags.update(CF=left<right if sub else full>mask if op=='ADD' else False,
                    OF=bool((left^right)&(left^result)&sign) if sub else bool(~(left^right)&(left^result)&sign) if op=='ADD' else False,
                    AF=bool((left^right^result)&16) if arithmetic else None,ZF=result==0,SF=bool(result&sign),PF=(result&255).bit_count()%2==0)
            if op!='MOV' and flags_changed:writes[16]=flag_pack(flags,('CF','PF','AF','ZF','SF','OF'))
            if op!='CMP':
                if dst[0]=='reg':rd=dst[1];writes[rd]=result # E/RnD writes always zero-extend.
                else:sources.append(dst[1]);address=(registers[dst[1]]+dst[2])&((1<<64)-1);store_value=result;store_bits=bits;write_memory(mem,address,bits,result);norm='SW'
            if src[0]=='mem':address=(registers[src[1]]+src[2])&((1<<64)-1);norm='LW'
        for register,value in writes.items():registers[register]=value
        trace.append(dict(id=len(trace),pc=addresses[ip],instruction=Instruction(norm,rd=rd,text=lines[ip]),value=writes.get(rd),address=address,
            store_value=store_value,store_bits=store_bits,writes=writes,sources=sources,destinations=list(writes),encoding=None))
        ip=next_ip
    return dict(registers=registers,memory=mem,trace=trace,listing=listing,flags=flags,register_names=REGS+['RFLAGS观测'],register_bits=64,zero_register=None,architecture='x86_64')
