"""分开测并行、依赖、缓存与乘法资源；无人为IPC惩罚/奖励。"""
from functools import lru_cache
from copy import deepcopy
import json


def performance_cases(architecture):
    if architecture=='riscv32':
        independent='\n'.join(f'ADDI x{i%30+1},x0,{i}' for i in range(96))
        dependency='ADDI x1,x0,1\n'+'ADD x1,x1,x1\n'*128
        cache='\n'.join('ADDI x2,x0,0\n'+'LW x1,0(x2)\nADDI x2,x2,256\n'*32 for _ in range(4))
        mixed='ADDI x1,x0,3\nADDI x2,x0,7\n'+'\n'.join('MUL x3,x1,x2\nADD x4,x3,x1\nADDI x5,x0,9' for _ in range(24))
    elif architecture=='x86_32':
        regs=['EAX','EBX','ECX','EDX','ESI','EDI']
        independent='\n'.join(f'MOV {regs[i%6]},{i}' for i in range(96))
        dependency='MOV EAX,1\n'+'ADD EAX,EAX\n'*128
        cache='\n'.join(f'MOV EAX,[{i*256}]' for _ in range(4) for i in range(32))
        mixed='MOV EAX,3\nMOV EBX,7\n'+'\n'.join('MOV ECX,EAX\nIMUL ECX,EBX\nADD EDX,ECX\nMOV ESI,9' for _ in range(24))
    elif architecture=='aarch64':
        independent='\n'.join(f'MOV X{i%30},#{i}' for i in range(96))
        dependency='MOV X0,#1\n'+'ADD X0,X0,X0\n'*128
        cache='MOV X0,#0\n'+'\n'.join(f'LDR W1,[X0,#{i*256}]' for _ in range(4) for i in range(32))
        mixed='MOV X0,#3\nMOV X1,#7\n'+'\n'.join('MUL X2,X0,X1\nADD X3,X2,X0\nMOV X4,#9' for _ in range(24))
    else:raise ValueError('当前性能套件只支持RISC-V 32位、x86 32位、Arm 64位整数子集。')
    return [dict(id=key,name=name,bench=dict(source=source+'\nHALT',memory=''),focus=focus)
            for key,name,source,focus in [
                ('independent','独立整数吞吐',independent,'共同宽度、总发射与ALU数量；足够长的独立流'),
                ('dependency','相关运算链',dependency,'RAW依赖约束；加宽不应凭空解除依赖'),
                ('cache','缓存工作集重用',cache,'32条缓存行、四次遍历；容量/相联和命中延迟'),
                ('mixed','乘法与相关整数',mixed,'乘法资源/延迟、依赖与顺序/乱序调度')]]


def cpu_performance_report(hardware):
    from .core_studio import validate_hardware
    h=validate_hardware('cpu',hardware)
    return deepcopy(_run(json.dumps(h,sort_keys=True)))


@lru_cache(maxsize=64)
def _run(hardware_json):
    from .core_studio import run_design
    h=json.loads(hardware_json);cases=[]
    for case in performance_cases(h['architecture']):
        if case['id']=='mixed' and h['architecture']=='riscv32' and not h['enable_m']:continue
        r=run_design('cpu',h,case['bench'])
        cases.append(dict(id=case['id'],name=case['name'],focus=case['focus'],cycles=r['cycles'],
            instructions=r['instructions'],ipc=r['ipc'],cache_hit_rate=r['cache']['hit_rate'],
            stalls=r['stalls'],functional_check=r['functional_check']))
    instructions=sum(c['instructions'] for c in cases);cycles=sum(c['cycles'] for c in cases)
    return dict(hardware=h,cases=cases,instructions=instructions,cycles=cycles,ipc=instructions/max(1,cycles),
        scope='同ISA、同任务比较的资源调度周期；IPC=实际提交指令/全部模型周期，含前端填充与冷cache；不是跨ISA能力排名或真实CPU实测。')
