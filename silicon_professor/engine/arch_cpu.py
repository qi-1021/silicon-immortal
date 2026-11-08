"""原生 IA-32/AArch64 功能前端。语义独立，向共同资源模型提供动态轨迹。

IA-32：8个32位寄存器，算术标志，MOV/ADD/SUB/CMP/AND/OR/XOR/IMUL 与 Jcc/JMP。
A64：W/X寄存器、NZCV，整数/MUL/CMP与B/BL/BR/RET、LDR/STR子集。
没有模式切换、段/页表、异常、浮点/SIMD。汇编对象执行，不从机器码取指。
"""
from __future__ import annotations

import re
from .isa import Instruction, execute, assemble, encode, read_memory, write_memory

X86_REGS=['EAX','ECX','EDX','EBX','ESP','EBP','ESI','EDI']


def parse_lines(source):
    if not isinstance(source,str) or len(source)>100000:raise ValueError('程序文本过长。')
    labels,rows={},[]
    for raw in source.splitlines():
        line=raw.split(';',1)[0].strip()
        if not line:continue
        if ':' in line:
            label,line=line.split(':',1);label=label.strip()
            if not re.fullmatch(r'[A-Za-z_]\w*',label) or label in labels:raise ValueError('标签重复或不合法。')
            labels[label]=len(rows);line=line.strip()
        if line:rows.append(line)
    if not rows or len(rows)>1024:raise ValueError('程序需包含1..1024条指令。')
    return labels,rows


def flag_pack(flags, names):
    positions={'CF':0,'PF':2,'AF':4,'ZF':6,'SF':7,'OF':11,'N':31,'Z':30,'C':29,'V':28}
    # 只表示定义的算术标志；不是完整EFLAGS/PSTATE，也不填系统或保留位。
    return sum(int(bool(flags.get(k,False)))<<positions[k] for k in names)


def integer(s):
    try:return int(s.strip().lstrip('#'),0)
    except ValueError as ex:raise ValueError(f'整数操作数无效：{s}') from ex


def execute_x86(source,memory=None,max_instructions=4096):
    labels,lines=parse_lines(source)
    parsed,listing,addresses=[],[],[]
    pc=0
    def reg(s):
        s=s.upper()
        if s not in X86_REGS:raise ValueError('仅支持32位 EAX/ECX/EDX/EBX/ESP/EBP/ESI/EDI。')
        return X86_REGS.index(s)
    def operand(s):
        s=s.strip().upper()
        if s.startswith('[') and s.endswith(']'):
            inner=s[1:-1].strip();m=re.fullmatch(r'(EAX|ECX|EDX|EBX|ESP|EBP|ESI|EDI)(?:\s*([+-])\s*(\w+))?',inner)
            if m:return ('mem',reg(m[1]),(integer(m[3]) if m[3] else 0)*(-1 if m[2]=='-' else 1))
            return ('mem',None,integer(inner))
        return ('reg',reg(s),0) if s in X86_REGS else ('imm',None,integer(s))
    branches={'JMP','JE','JZ','JNE','JNZ','JL','JGE','JB','JAE','JG','JLE','JA','JBE'}
    for i,line in enumerate(lines):
        parts=line.split(None,1);op=parts[0].upper();args=[s.strip() for s in parts[1].split(',')] if len(parts)>1 else []
        raw=None;ops=[]
        if op=='HALT' and not args:raw=b''
        elif op in branches and len(args)==1:
            if args[0] not in labels:raise ValueError('找不到跳转标签。')
            ops=[labels[args[0]]];raw=(b'\xe9'+b'\0'*4) if op=='JMP' else bytes([0x0f,{'JE':0x84,'JZ':0x84,'JNE':0x85,'JNZ':0x85,'JL':0x8c,'JGE':0x8d,'JB':0x82,'JAE':0x83,'JG':0x8f,'JLE':0x8e,'JA':0x87,'JBE':0x86}[op]])+b'\0'*4
        elif op in {'MOV','ADD','SUB','CMP','AND','OR','XOR','IMUL'} and len(args)==2:
            ops=[operand(a) for a in args]
            dst,src=ops
            if dst[0]=='imm' or (dst[0]=='mem' and src[0]=='mem'):raise ValueError('目标不可为立即数；不支持 memory-to-memory。')
            if op!='MOV' and (dst[0]!='reg' or src[0]=='mem'):raise ValueError('此子集算术仅支持寄存器目标和寄存器/立即数源。')
            if op=='MOV' and dst[0]=='reg' and src[0]=='imm':raw=bytes([0xb8+dst[1]])+(src[2]&0xffffffff).to_bytes(4,'little')
            elif op=='MOV' and dst[0]=='reg' and src[0]=='reg':raw=bytes([0x89,0xc0|(src[1]<<3)|dst[1]])
            elif op!='MOV' and src[0]=='reg':
                raw=bytes([{'ADD':0x01,'SUB':0x29,'CMP':0x39,'AND':0x21,'OR':0x09,'XOR':0x31}.get(op,0x0f),0xc0|(src[1]<<3)|dst[1]]) if op!='IMUL' else bytes([0x0f,0xaf,0xc0|(dst[1]<<3)|src[1]])
            elif op!='MOV' and src[0]=='imm' and op!='IMUL':raw=bytes([0x81,0xc0|({'ADD':0,'OR':1,'AND':4,'SUB':5,'XOR':6,'CMP':7}[op]<<3)|dst[1]])+(src[2]&0xffffffff).to_bytes(4,'little')
            elif op=='MOV':
                mem=src if src[0]=='mem' else dst;register=dst[1] if src[0]=='mem' else src[1]
                if (src if dst[0]=='mem' else dst)[0]!='reg':raise ValueError('MOV 访存必须有寄存器操作数。')
                opcode=0x8b if src[0]=='mem' else 0x89
                if mem[1] is None:raw=bytes([opcode,(register<<3)|5])+(mem[2]&0xffffffff).to_bytes(4,'little')
                else:
                    base=mem[1];raw=bytes([opcode,0x80|(register<<3)|(4 if base==4 else base)])+(b'\x24' if base==4 else b'')+(mem[2]&0xffffffff).to_bytes(4,'little')
            else:raise ValueError('本子集不支持此 IMUL 立即数形式。')
        else:raise ValueError(f'未实现 x86 指令/形式：{line}')
        addresses.append(pc);listing.append(dict(pc=pc,text=line,op=op,word=None,bytes=raw.hex()));parsed.append((op,ops))
        pc+=len(raw) if raw else 1  # HALT 是实验标记，不是 HLT 指令。
    for i,(op,ops) in enumerate(parsed):
        if op in branches:
            data=bytes.fromhex(listing[i]['bytes']);offset=addresses[ops[0]]-(addresses[i]+len(data))
            listing[i]['bytes']=(data[:-4]+(offset&0xffffffff).to_bytes(4,'little')).hex()
    regs=[0]*9;mem=dict(memory or {});flags={k:False for k in ('CF','PF','AF','ZF','SF','OF')};rows=[];ip=0
    while 0<=ip<len(parsed):
        if len(rows)>=max_instructions:raise ValueError('动态指令超过上限。')
        op,ops=parsed[ip];next_ip=ip+1;writes={};sources=[];address=None;store_value=None
        if op=='HALT':break
        def read(o):
            if o[0]=='imm':return o[2]&0xffffffff
            if o[0]=='reg':sources.append(o[1]);return regs[o[1]]
            if o[1] is not None:sources.append(o[1])
            addr=((regs[o[1]] if o[1] is not None else 0)+o[2])&0xffffffff
            return read_memory(mem,addr,32)
        norm='ADD';rd=None
        if op in branches:
            norm='JAL'
            if op!='JMP':sources.append(8)
            f=flags
            required={'JE':('ZF',),'JZ':('ZF',),'JNE':('ZF',),'JNZ':('ZF',),'JL':('SF','OF'),'JGE':('SF','OF'),'JB':('CF',),'JAE':('CF',),'JG':('ZF','SF','OF'),'JLE':('ZF','SF','OF'),'JA':('CF','ZF'),'JBE':('CF','ZF')}.get(op,())
            if any(f[k] is None for k in required):raise ValueError('条件分支使用了IMUL后未定义的标志；先CMP/有效算术。')
            taken={'JMP':True,'JE':f['ZF'],'JZ':f['ZF'],'JNE':not f['ZF'],'JNZ':not f['ZF'],'JL':f['SF']!=f['OF'],'JGE':f['SF']==f['OF'],'JB':f['CF'],'JAE':not f['CF'],'JG':not f['ZF'] and f['SF']==f['OF'],'JLE':f['ZF'] or f['SF']!=f['OF'],'JA':not f['CF'] and not f['ZF'],'JBE':f['CF'] or f['ZF']}[op]
            if taken:next_ip=ops[0]
        else:
            dst,src=ops;right=read(src);left=read(dst) if op!='MOV' else 0
            value=right if op=='MOV' else left+right if op=='ADD' else left-right if op in {'SUB','CMP'} else left&right if op=='AND' else left|right if op=='OR' else left^right if op=='XOR' else ((left if left<0x80000000 else left-0x100000000)*(right if right<0x80000000 else right-0x100000000))
            result=value&0xffffffff
            if op!='MOV':
                if op=='IMUL':
                    truncated=result if result<0x80000000 else result-0x100000000
                    flags['CF']=flags['OF']=truncated!=value
                    for flag in ('PF','AF','ZF','SF'):flags[flag]=None
                    # PF/AF/ZF/SF 未定义，不声称产生确定值。
                else:
                    flags['CF']=left<right if op in {'SUB','CMP'} else value>0xffffffff if op=='ADD' else False
                    flags['OF']=bool(((left^right)&(left^result)&0x80000000) if op in {'SUB','CMP'} else (~(left^right)&(left^result)&0x80000000) if op=='ADD' else 0)
                    flags['ZF']=result==0;flags['SF']=bool(result&0x80000000);flags['PF']=(result&255).bit_count()%2==0
                    flags['AF']=bool((left^right^result)&16) if op in {'ADD','SUB','CMP'} else False
                writes[8]=flag_pack(flags,('CF','PF','AF','ZF','SF','OF'))
            if op!='CMP':
                if dst[0]=='reg':rd=dst[1];writes[rd]=result
                else:
                    if dst[1] is not None:sources.append(dst[1])
                    address=((regs[dst[1]] if dst[1] is not None else 0)+dst[2])&0xffffffff
                    store_value=result;write_memory(mem,address,32,result);norm='SW'
            if src[0]=='mem':
                address=((regs[src[1]] if src[1] is not None else 0)+src[2])&0xffffffff;norm='LW'
            if op=='IMUL':norm='MUL'
        for register,value in writes.items():regs[register]=value
        ins=Instruction(norm,rd=rd,text=lines[ip])
        rows.append(dict(id=len(rows),pc=addresses[ip],instruction=ins,value=writes.get(rd),address=address,store_value=store_value,
                         store_bits=32 if norm=='SW' else None,writes=writes,sources=sources,destinations=list(writes),encoding=None))
        ip=next_ip
    return dict(registers=regs,memory=mem,trace=rows,listing=listing,flags=flags,
                register_names=X86_REGS+['EFLAGS观测'],register_bits=32,zero_register=None,architecture='x86_32')


def execute_a64(source,memory=None,max_instructions=4096):
    labels,lines=parse_lines(source);parsed=[];listing=[]
    def reg(s):
        s=s.upper().strip()
        if s in ('XZR','WZR'):return 31,64 if s=='XZR' else 32
        m=re.fullmatch(r'([XW])([0-9]|[12][0-9]|30)',s)
        if not m:raise ValueError('支持 X0..X30/W0..W30/XZR/WZR；本子集不使用 SP。')
        return int(m[2]),64 if m[1]=='X' else 32
    def opnd(s):
        try:r,bits=reg(s);return ('reg',r,bits)
        except ValueError:
            return ('imm',integer(s),0)
    branch_ops={'B','BL','B.EQ','B.NE','B.LT','B.GE','B.LO','B.HS','B.GT','B.LE'}
    for i,line in enumerate(lines):
        parts=line.split(None,1);op=parts[0].upper();tail=parts[1] if len(parts)>1 else '';args=[a.strip() for a in tail.split(',')] if tail else []
        operands=[];word=None
        if op=='HALT' and not args:pass
        elif op in branch_ops and len(args)==1:
            if args[0] not in labels:raise ValueError('找不到分支标签。')
            operands=[labels[args[0]]];off=labels[args[0]]-i
            word=(0x94000000 if op=='BL' else 0x14000000)|(off&0x3ffffff) if op in {'B','BL'} else 0x54000000|((off&0x7ffff)<<5)|{'B.EQ':0,'B.NE':1,'B.LO':3,'B.HS':2,'B.LT':11,'B.GE':10,'B.GT':12,'B.LE':13}[op]
        elif op in {'BR','RET'}:
            r,bits=reg(args[0] if args else 'X30')
            if bits!=64:raise ValueError('BR/RET使用X寄存器。')
            operands=[r];word=(0xd65f0000 if op=='RET' else 0xd61f0000)|(r<<5)
        elif op in {'LDR','STR'}:
            m=re.fullmatch(r'([XW]\d+|[XW]ZR)\s*,\s*\[(X\d+|XZR)(?:\s*,\s*#?(-?(?:0x[\da-fA-F]+|\d+)))?\]',tail,re.I)
            if not m:raise ValueError('LDR/STR 形式：LDR X1, [X2, #8]；不支持writeback。')
            r,bits=reg(m[1]);base,_=reg(m[2]);imm=integer(m[3] or '0')
            if base==31:raise ValueError('A64访存base31表示SP，不是XZR；本子集未实现SP。')
            operands=[r,bits,base,imm]
            if imm<0 or imm%(bits//8) or imm//(bits//8)>=4096:raise ValueError('LDR/STR只支持unsigned-scaled offset；其它形式未实现。')
            # 原生编码中 base31 是 SP，不是 XZR，因此此形式不伪造编码。
            if base!=31 and imm>=0 and imm%(bits//8)==0 and imm//(bits//8)<4096:
                word=({('LDR',64):0xf9400000,('STR',64):0xf9000000,('LDR',32):0xb9400000,('STR',32):0xb9000000}[(op,bits)])|((imm//(bits//8))<<10)|(base<<5)|r
        elif op=='MOV' and len(args)==2:
            dst,bits=reg(args[0]);src=opnd(args[1]);operands=[dst,bits,src]
            if src[0]=='reg' and src[2]!=bits:raise ValueError('MOV源/目标位宽应一致。')
            if src[0]=='reg':word=(0xaa0003e0 if bits==64 else 0x2a0003e0)|(src[1]<<16)|dst
            else:
                mask=(1<<bits)-1;value=src[1]&mask
                chosen=None
                for inverted in (False,True):
                    pattern=(~value)&mask if inverted else value
                    for shift in range(0,bits,16):
                        if pattern & ~(0xffff<<shift)==0:
                            chosen=((0x92800000 if bits==64 else 0x12800000) if inverted else (0xd2800000 if bits==64 else 0x52800000))|((shift//16)<<21)|(((pattern>>shift)&0xffff)<<5)|dst
                            break
                    if chosen is not None:break
                if chosen is None:raise ValueError('MOV立即数需单条MOVZ/MOVN能表达；多条MOVK伪指令尚未实现。')
                word=chosen
        elif op in {'ADD','ADDS','SUB','SUBS','AND','ORR','EOR','MUL','CMP'}:
            if len(args)!=(2 if op=='CMP' else 3):raise ValueError('算术操作数数量错误。')
            dst,bits=(31,reg(args[0])[1]) if op=='CMP' else reg(args[0]);left=reg(args[0] if op=='CMP' else args[1]);right=opnd(args[-1]);operands=[dst,bits,left[0],right]
            if left[1]!=bits or (right[0]=='reg' and right[2]!=bits):raise ValueError('操作数位宽不一致。')
            baseop='SUBS' if op=='CMP' else op
            if right[0]=='imm' and (left[0]==31 or (dst==31 and baseop in ('ADD','SUB'))):
                raise ValueError('A64此立即数形式中的寄存器31表示SP；不能当XZR，SP未实现。')
            if right[0]=='reg':
                table={'ADD':0x0b000000,'ADDS':0x2b000000,'SUB':0x4b000000,'SUBS':0x6b000000,'AND':0x0a000000,'ORR':0x2a000000,'EOR':0x4a000000,'MUL':0x1b007c00}
                word=table[baseop]|(0x80000000 if bits==64 else 0)|(right[1]<<16)|(left[0]<<5)|dst
            elif baseop in {'ADD','ADDS','SUB','SUBS'} and 0<=right[1]<=4095:
                word={'ADD':0x11000000,'ADDS':0x31000000,'SUB':0x51000000,'SUBS':0x71000000}[baseop]|(0x80000000 if bits==64 else 0)|(right[1]<<10)|(left[0]<<5)|dst
            else:raise ValueError('只支持ADD/SUB类0..4095立即数或寄存器算术。')
        else:raise ValueError(f'未实现A64指令/形式：{line}')
        parsed.append((op,operands));listing.append(dict(pc=i*4,text=line,op=op,word=word,bytes='' if word is None else word.to_bytes(4,'little').hex()))
    regs=[0]*33;mem=dict(memory or {});flags={k:False for k in ('N','Z','C','V')};trace=[];ip=0
    while 0<=ip<len(parsed):
        if len(trace)>=max_instructions:raise ValueError('动态指令超过上限。')
        op,o=parsed[ip];next_ip=ip+1;sources=[];writes={};address=None;store_value=None;store_bits=None;rd=None;norm='ADD'
        if op=='HALT':break
        def read(r,bits=64):
            if r==31:return 0
            sources.append(r);return regs[r]&((1<<bits)-1)
        if op in branch_ops:
            norm='JAL'
            if op not in {'B','BL'}:sources.append(32)
            f=flags;taken={'B':True,'BL':True,'B.EQ':f['Z'],'B.NE':not f['Z'],'B.LO':not f['C'],'B.HS':f['C'],'B.LT':f['N']!=f['V'],'B.GE':f['N']==f['V'],'B.GT':not f['Z'] and f['N']==f['V'],'B.LE':f['Z'] or f['N']!=f['V']}[op]
            if taken:next_ip=o[0]
            if op=='BL':rd=30;writes[30]=ip*4+4
        elif op in {'BR','RET'}:
            norm='JALR';target=read(o[0])
            if target%4 or target>=len(parsed)*4:raise ValueError('跳转目标非对齐或越界。')
            next_ip=target//4
        elif op in {'LDR','STR'}:
            r,bits,base,imm=o;address=(read(base)+imm)&((1<<64)-1)
            if op=='LDR':norm='LW';rd=r;value=read_memory(mem,address,bits);writes[r]=value if r!=31 else 0
            else:norm='SW';store_value=read(r,bits);store_bits=bits;write_memory(mem,address,bits,store_value)
        elif op=='MOV':
            rd,bits,src=o;value=read(src[1],bits) if src[0]=='reg' else src[1]
            if rd!=31:writes[rd]=value&((1<<bits)-1)
        else:
            rd,bits,left,right=o;a=read(left,bits);b=read(right[1],bits) if right[0]=='reg' else right[1];mask=(1<<bits)-1
            sub=op in {'SUB','SUBS','CMP'}
            full=a-b if sub else a+b if op in {'ADD','ADDS'} else a&b if op=='AND' else a|b if op=='ORR' else a^b if op=='EOR' else a*b
            value=full&mask
            if op in {'ADDS','SUBS','CMP'}:
                sign=1<<(bits-1);flags.update(N=bool(value&sign),Z=value==0,C=a>=b if sub else full>mask,V=bool(((a^b)&(a^value)&sign) if sub else (~(a^b)&(a^value)&sign)))
                writes[32]=flag_pack(flags,('N','Z','C','V'))
            if rd!=31:writes[rd]=value
            if op=='MUL':norm='MUL'
        writes.pop(31,None)
        for register,value in writes.items():regs[register]=value
        regs[31]=0
        ins=Instruction(norm,rd=rd if rd!=31 else None,text=lines[ip])
        trace.append(dict(id=len(trace),pc=ip*4,instruction=ins,value=writes.get(rd),address=address,store_value=store_value,
                          store_bits=store_bits,writes=writes,sources=sources,destinations=list(writes),encoding=listing[ip]['word']))
        ip=next_ip
    return dict(registers=regs,memory=mem,trace=trace,listing=listing,flags=flags,
                register_names=[f'X{i}' for i in range(31)]+['XZR','NZCV观测'],register_bits=64,zero_register=31,architecture='aarch64')


def execute_architecture(architecture,source,memory=None,extensions=(),max_instructions=4096):
    if architecture=='riscv32':
        program=assemble(source,extensions);r=execute(program,memory,max_instructions)
        return dict(r,listing=[dict(pc=i*4,text=ins.text,op=ins.op,word=encode(ins,i*4),bytes='') for i,ins in enumerate(program)],
                    register_names=[f'x{i}' for i in range(32)],register_bits=32,zero_register=0,architecture=architecture)
    if extensions:raise ValueError('x86/A64子集没有实现额外扩展；不能启用AVX/NEON等开关。')
    if architecture=='x86_32':return execute_x86(source,memory,max_instructions)
    if architecture=='x86_64':
        from .x64_cpu import execute_x64
        return execute_x64(source,memory,max_instructions)
    if architecture=='aarch64':return execute_a64(source,memory,max_instructions)
    raise ValueError(f'未实现该架构执行器：{architecture}')
