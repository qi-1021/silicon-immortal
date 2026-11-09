"""参数化硬件设计、结构与独立测试台；没有生成RTL或真实PDK数据。"""
from copy import deepcopy
from functools import lru_cache
import json

from ..data.core_designs import FIELDS, BENCH_FIELDS, default_hardware, default_bench
from ..data.architectures import ISA_FAMILIES
from .labs import run_experiment
from .lab_accelerators import npu_lab, isp_lab, fp32

SCHEMA='parameterized-core-v1'
from .core_performance import cpu_performance_report


def validate_hardware(kind,hardware):
    if kind not in FIELDS or not isinstance(hardware,dict):
        raise ValueError('无法识别的核心类别或硬件定义。')
    unknown=set(hardware)-{field['key'] for field in FIELDS[kind]}
    if unknown:raise ValueError('本版未实现硬件字段：'+', '.join(sorted(unknown)))
    h=default_hardware(kind);h.update(deepcopy(hardware))
    for field in FIELDS[kind]:
        key=field['key'];value=h[key]
        if 'options' in field:
            valid=type(value) is type(field['default']) and value in [v for v,_ in field['options']]
        elif type(field['default']) is bool:
            valid=type(value) is bool
        else:
            valid=(type(value) is int if type(field['default']) is int else type(value) in (int,float))
            valid=valid and field['min']<=value<=field['max']
        if not valid:raise ValueError(f'hardware.{key} 无效：{value!r}')
    if kind=='cpu':
        if h['hit_latency']>h['miss_latency']:raise ValueError('hit_latency不能大于miss_latency。')
        if h['rob_size']<h['smt_threads']:raise ValueError('ROB须至少容纳每上下文一条指令。')
        if h['cache_kb']*1024 % (h['cache_ways']*h['cache_line_bytes']):raise ValueError('Cache容量须为行长×路数的整数倍。')
    if kind=='npu':
        minimum=(h['rows']+h['cols'])*(h['precision_bits']//8)+h['rows']*h['cols']*(h['accumulator_bits']//8)
        if minimum>h['scratchpad_kb']*1024:raise ValueError(f'scratchpad不足以存放完整阵列一次K=1的输入与累加：至少{minimum}B。')
    return h


def mapped_config(kind,hardware,bench=None):
    h=validate_hardware(kind,hardware)
    b=default_bench(kind,h)
    if bench is not None:
        if not isinstance(bench,dict) or set(bench)-{f['key'] for f in BENCH_FIELDS[kind]}:
            raise ValueError('测试台不能覆盖硬件资源定义。')
        b.update(deepcopy(bench))
    if kind=='cpu':
        keys=[f['key'] for f in FIELDS[kind] if f['key'] not in ('enable_m','enable_zbb')]
        p={key:h[key] for key in keys}
        p['extensions']=[ext for ext,key in [('M','enable_m'),('Zbb','enable_zbb')] if h[key]] if h['architecture']=='riscv32' else []
    elif kind=='isp':
        p={key:h[key] for key in ('output_bits','pixels_per_cycle','frequency_ghz','bandwidth_gbs')}
        p['stages']=[key for key in ('black_level','gain','demosaic','gamma') if h[key+'_enabled']]
    else:p=dict(h)
    return dict(p,**b)


def run_design(kind,hardware,bench=None):
    h=validate_hardware(kind,hardware)
    p=mapped_config(kind,h,bench)
    if kind=='isp' and p['width']>h['max_width']:raise ValueError('测试行宽超出核心max_width定义。')
    result=run_experiment(kind,p)
    if kind=='isp':result['allocated_line_buffer_bytes']=h['max_width']*4 if h['demosaic_enabled'] else 0
    result['hardware']=h
    return result


def _cpu_vectors(arch):
    if arch=='riscv32':
        vectors=[('加法与存储加载','ADDI x1,x0,6\nADDI x2,x0,7\nADD x3,x1,x2\nSW x3,0(x0)\nLW x4,0(x0)\nHALT',{'x4':13}),
                 ('相关运算链','ADDI x1,x0,1\n'+'ADD x1,x1,x1\n'*8+'HALT',{'x1':256}),
                 ('独立整数运算','\n'.join(f'ADDI x{i},x0,{i}' for i in range(1,25))+'\nHALT',{'x24':24}),
                 ('分支控制','ADDI x1,x0,3\nloop:\nADDI x1,x1,-1\nBNE x1,x0,loop\nHALT',{'x1':0})]
    elif arch in ('x86_32','x86_64'):
        vectors=[('加法与存储加载','MOV EAX,6\nMOV EBX,7\nADD EAX,EBX\nMOV [0],EAX\nMOV ECX,[0]\nHALT',{'ECX':13}),
                 ('相关运算链','MOV EAX,1\n'+'ADD EAX,EAX\n'*8+'HALT',{'EAX':256}),
                 ('独立整数运算','\n'.join(f'MOV {reg},{i}' for i in range(1,5) for reg in ('EAX','EBX','ECX','EDX'))+'\nHALT',{'EDX':4}),
                 ('标志与分支','MOV EAX,3\nloop:\nSUB EAX,1\nCMP EAX,0\nJNE loop\nHALT',{'EAX':0})]
        if arch=='x86_64':
            converted=[]
            for name,source,expected in vectors:
                source=source.replace('[0]','[R8]')
                for e,r in [('EAX','RAX'),('EBX','RBX'),('ECX','RCX'),('EDX','RDX')]:source=source.replace(e,r)
                source='MOV R8,0\n'+source
                converted.append((name,source,{k.replace('E','R',1):v for k,v in expected.items()}))
            vectors=converted
    else:
        vectors=[('加法与存储加载','MOV X0,#6\nMOV X1,#7\nADD X2,X0,X1\nSTR X2,[X3]\nLDR X4,[X3]\nHALT',{'X4':13}),
                 ('相关运算链','MOV X0,#1\n'+'ADD X0,X0,X0\n'*8+'HALT',{'X0':256}),
                 ('独立整数运算','\n'.join(f'MOV X{i},#{i}' for i in range(24))+'\nHALT',{'X23':23}),
                 ('标志与分支','MOV X0,#3\nloop:\nSUB X0,X0,#1\nCMP X0,#0\nB.NE loop\nHALT',{'X0':0})]
    return vectors


def verify_design(kind,hardware):
    h=validate_hardware(kind,hardware)
    return deepcopy(_verify_cached(kind,json.dumps(h,sort_keys=True)))


@lru_cache(maxsize=128)
def _verify_cached(kind,hardware_json):
    h=json.loads(hardware_json);cases=[]
    def add(name,result,ok,observation):
        cases.append(dict(name=name,passed=bool(ok),cycles=result['cycles'],
                          instructions=result.get('instructions'),ipc=result.get('ipc'),
                          compute_cycles=result.get('compute_cycles'),transfer_cycles=result.get('transfer_cycles'),
                          observation=observation))
    if kind=='cpu':
        for name,source,expected in _cpu_vectors(h['architecture']):
            r=run_design(kind,h,dict(source=source,memory=''))
            registers=dict(zip(r['register_names'],r['registers']))
            ok=all(registers.get(key)==value for key,value in expected.items())
            if name=='加法与存储加载':ok=ok and r['memory'].get(0)==13
            add(name,r,ok,', '.join(f'{key}={registers.get(key)}（预期{value}）' for key,value in expected.items()))
        if h['architecture']=='riscv32' and h['enable_m']:
            r=run_design(kind,h,dict(source='ADDI x1,x0,-7\nADDI x2,x0,3\nDIV x3,x1,x2\nREM x4,x1,x2\nHALT',memory=''))
            add('M 除法边界',r,r['registers'][3]==0xfffffffe and r['registers'][4]==0xffffffff,'DIV(-7,3)=-2；REM=-1')
        if h['architecture']=='riscv32' and h['enable_zbb']:
            r=run_design(kind,h,dict(source='ADDI x1,x0,255\nCPOP x2,x1\nHALT',memory=''))
            add('Zbb 位计数',r,r['registers'][2]==8,'CPOP(255)=8')
        if h['architecture']=='x86_64':
            r=run_design(kind,h,dict(source='MOV R8,0x1122334455667788\nMOV R9,R8\nMOV R8D,7\nMOV R10,256\nMOV [R10],R9\nMOV R11,[R10]\nHALT',memory=''))
            add('64位状态 / 32位零扩展',r,r['registers'][8]==7 and r['registers'][11]==0x1122334455667788,'R8D写7清除高32位；R11保留64位qword')
        if h['smt_threads']==2:
            vectors=_cpu_vectors(h['architecture']);a=vectors[0];b=vectors[2]
            r=run_design(kind,h,dict(source=a[1],source2=b[1],memory=''))
            ok=all(all(dict(zip(t['register_names'],t['registers'])).get(key)==value for key,value in expected.items()) for t,expected in zip(r['threads'],(a[2],b[2])))
            add('双上下文隔离',r,ok,'寄存器与地址空间独立；共享前端/发射/缓存，ROB均分；不证明OS或一致性')
    elif kind=='gpu':
        for task,pattern,elements in [('axpy','uniform',128),('branch','uniform',128),('branch','alternating',129)]:
            r=run_design(kind,h,dict(task=task,pattern=pattern,elements=elements))
            expected=[fp32(fp32(2*r['input_x'][i])+r['input_y'][i]) if task=='axpy' or pattern=='uniform' or i%2==0 else fp32(r['input_x'][i]**2) for i in range(elements)]
            add(f'{task}/{pattern} · {elements}',r,r['output']==expected,f"{r['operations']} ops；分歧warp {r['divergence']}；逐lane FP32参考")
    elif kind=='npu':
        p=mapped_config(kind,h,dict(m=2,n=2,k=2))
        r=npu_lab(**p,a=[[1,2],[3,4]],b=[[5,6],[7,8]])
        add('2×2 手算矩阵',r,r['output']==[[19,22],[43,50]] and r['scratchpad_fits'],'预期 [[19,22],[43,50]]')
        r=run_design(kind,h)
        add('8×8 资源与矩阵',r,r['functional_check'] and r['scratchpad_fits'],f"{r['macs']} MAC；本地占用{r['scratchpad_bytes']}B；容量匹配{r['scratchpad_fits']}")
        p=mapped_config(kind,h,dict(m=1,n=1,k=4));r=npu_lab(**p,a=[[127]*4],b=[[127] for _ in range(4)])
        value=64516;bits=h['accumulator_bits'];wrapped=value % (1<<bits)
        if wrapped>=(1<<(bits-1)):wrapped-=1<<bits
        add('有限累加器边界',r,r['output']==[[wrapped]],f'精确64516 → INT{bits}结果{wrapped}；溢出按wrap语义检查')
    else:
        width=min(8,h['max_width'])
        for name,value in [('黑电平常量帧',64),('非零常量帧',1088)]:
            p=mapped_config(kind,h,dict(width=width,height=4,black_level=64,gain=1.,gamma=1.))
            r=isp_lab(**p,raw=[[value]*width for _ in range(4)])
            scalar=max(0,value-(64 if h['black_level_enabled'] else 0))/4095
            expected=round(scalar*((1<<h['output_bits'])-1))
            ok=all(pixel==[expected]*3 for row in r['output'] for pixel in row)
            add(name,r,ok,f'预期每通道{expected}；{r["color_mode"]}；常量帧不证明画质')
        r=run_design(kind,h,dict(width=width,height=4))
        add('RGGB 渐变与范围',r,r['functional_check'],f'{r["pixels"]} pixels；范围/形状检查')
    total_cycles=sum(c['cycles'] for c in cases)
    instructions=sum(c['instructions'] or 0 for c in cases)
    return dict(passed=all(c['passed'] for c in cases),cases=cases,checks=[c['name'] for c in cases],
                scope='fixed functional vectors and resource scheduling; not full ISA/RTL/PDK certification',
                model=SCHEMA,cycles=total_cycles,observed_ipc=instructions/max(1,total_cycles) if kind=='cpu' else None)


def structure(kind,hardware):
    h=validate_hardware(kind,hardware);nodes=[];edges=[]
    def node(key,title,detail,group=None):nodes.append(dict(id=key,title=title,detail=detail,group=group or key))
    def edge(a,b,label='data'):edges.append(dict(source=a,target=b,label=label))
    if kind=='cpu':
        from ..data.architectures import isa_name
        node('contract',isa_name(h['architecture']),f"整数子集；{h['smt_threads']} 个上下文；独立地址空间")
        node('frontend','取指 / 分派',f"共享{h['width']}宽 · 填充{h['pipeline']}cycle · {'二位方向预测' if h['branch_predictor']=='two_bit' else '无预测'}")
        node('scheduler','ROB / 发射' if h['issue_order']=='out_of_order' else '顺序发射队列',f"{h['rob_size']}在途 · 总发射{h['execution_ports']}宽")
        node('alu','整数 ALU',f"{h['alu_ports']}个 · 1cycle")
        node('retire','顺序提交',f"{h['width']}宽；架构寄存器",'scheduler')
        node('cache','L1 数据缓存',f"{h['cache_kb']}KiB · {h['cache_ways']}路 · {h['cache_line_bytes']}B/line")
        node('memory','访存单元 / 外部内存',f"{h['mshrs']} MSHR · miss {h['miss_latency']}cycle · store有序",'cache')
        edge('contract','frontend');edge('frontend','scheduler');edge('scheduler','alu');edge('alu','retire');edge('scheduler','cache');edge('cache','memory','memory')
        if h['architecture']!='riscv32' or h['enable_m']:
            node('multiply','乘除资源',f"{h['multiply_ports']}个 · 延迟{h['multiply_latency']}cycle")
            edge('scheduler','multiply');edge('multiply','retire')
    elif kind=='gpu':
        node('interface','外部输入/输出',f"{h['bandwidth_gbs']:g}GB/s · {h['frequency_ghz']:g}GHz")
        node('scheduler','warp 驻留 / 单发射',f"每处理器{h['resident_warps']}warp · 间隔{h['issue_interval']}cycle")
        node('processors','SIMT 处理器',f"{h['processors']}个 × {h['warp_size']}lane")
        node('alu','FP32 mul / add',f"延迟{h['alu_latency']}cycle；非FMA")
        node('output','分歧重汇合 / 输出','路径串行；每lane输出','processors')
        for a,b in [('interface','scheduler'),('scheduler','processors'),('processors','alu'),('alu','output')]:edge(a,b)
    elif kind=='npu':
        node('interface','DMA / 外部存储',f"{h['bandwidth_gbs']:g}GB/s · 计算传输不重叠")
        node('scratchpad','本地 scratchpad',f"{h['scratchpad_kb']}KiB · A/B/C单tile存储")
        node('array','systolic MAC 阵列',f"{h['rows']}×{h['cols']}PE · INT{h['precision_bits']}")
        node('accumulator','累加 / 输出',f"INT{h['accumulator_bits']} wrap · 每PE每cycle一MAC")
        for a,b in [('interface','scratchpad'),('scratchpad','array'),('array','accumulator')]:edge(a,b)
    else:
        node('interface','RAW12 / RGGB 输入',f"{h['pixels_per_cycle']}pixel/cycle · {h['bandwidth_gbs']:g}GB/s")
        last='interface'
        for key,title in [('black_level','黑电平减法'),('gain','标量增益'),('demosaic','双线性去马赛克'),('gamma','幂 gamma')]:
            if h[key+'_enabled']:
                node(key,title,'校准参数由测试台提供' if key!='demosaic' else '3×3邻域 · 边界缩小')
                edge(last,key);last=key
        node('quantize','量化 / 输出',f"{h['output_bits']}bit · {'RGB' if h['demosaic_enabled'] else 'RAW灰度'}")
        edge(last,'quantize')
        if h['demosaic_enabled']:
            node('line_buffer','两行缓冲',f"{4*h['max_width']}B · 最大行宽{h['max_width']}")
            edge('line_buffer','demosaic','memory')
    return dict(nodes=nodes,edges=edges,scope='由硬件定义生成的逻辑结构；非网表或布局')


def design_model(kind,name,hardware):
    """资源相关PPA教学映射；功能周期不转换成厂商IPC。"""
    h=validate_hardware(kind,hardware)
    common=dict(name=name,parameter_basis='game_assumption',evidence=[],confidence='assumption',license_cost_m=0.)
    if kind=='cpu':
        checks=verify_design(kind,h)
        mult=h['architecture']!='riscv32' or h['enable_m']
        area=1.4+.20*h['width']+.20*h['alu_ports']+.0015*h['rob_size']+.006*h['cache_kb']
        if mult:area+=.25*h['multiply_ports']
        if h['architecture']=='riscv32' and h['enable_zbb']:area+=.10
        if h['issue_order']=='out_of_order':area+=.30+.001*h['rob_size']
        area+=.08*(h['smt_threads']-1)+.012*(h['mshrs']-1)+(.05 if h['branch_predictor']=='two_bit' else 0)
        delay=2200+50*h['width']+35*h['alu_ports']+.3*h['rob_size']
        return dict(common,id='studio_cpu',vendor='STUDIO',arch=h['architecture'],
                    isa=ISA_FAMILIES[h['architecture']],
                    year=2026,tier='big',license='custom',ref_node='n3e',ipc=max(.15,min(2.5,checks['observed_ipc']*3)),
                    measured_ipc=checks['observed_ipc'],fmax_ref=1000/(delay/h['pipeline']+70),logic_area=area,
                    l2_default=1.,l2_max=8.,power_ref=.4+.10*h['width']+.12*h['alu_ports']+.03*area,
                    leak_frac=.16,eng_weeks=24,decode=h['width'],rob=h['rob_size'],
                    note='多类固定验证任务IPC映射；没有真实PPA校准或完整微架构。')
    if kind=='gpu':
        return dict(common,id='studio_gpu',vendor='STUDIO',year=2026,ref_node='n3e',unit_name='SIMT处理器',
                    min_units=h['processors'],max_units=h['processors'],default_units=h['processors'],
                    perf_per_unit=30*h['warp_size']/8/h['issue_interval']*h['frequency_ghz'],
                    area_per_unit=.5+.05*h['warp_size']+.002*h['warp_size']*h['resident_warps']+.005*h['warp_size']*h['alu_latency'],
                    power_per_unit=.1*h['frequency_ghz']*(h['warp_size']/8),compat=.8,cu_per_unit=1,
                    note='SIMT计算核心；非完整图形GPU，驻留资源/PPA为假设。')
    if kind=='npu':
        pes=h['rows']*h['cols'];precision=h['precision_bits']/8;acc=h['accumulator_bits']/32
        return dict(common,id='studio_npu',tops=2*pes*h['frequency_ghz']/1000,
                    precision=f"INT{h['precision_bits']}",area=.2+.004*pes*precision**2+.001*pes*acc+.002*h['scratchpad_kb'],
                    power=.1+.002*pes*h['frequency_ghz']*precision,
                    note=f"稠密INT{h['precision_bits']}阵列峰值，每MAC两op；PPA未校准。")
    stages=sum(h[key+'_enabled'] for key in ('black_level','gain','demosaic','gamma'))
    return dict(common,id='isp',area=.15+.08*(stages+1)*h['pixels_per_cycle']+(.0001*h['max_width'] if h['demosaic_enabled'] else 0),
                power=.03*(stages+1)*h['pixels_per_cycle']*h['frequency_ghz'],edge=False,color='#799683')


def hardware_from_legacy(kind,config):
    """旧实验资产转为可编辑草稿，保留旧记录本身的身份。"""
    h=default_hardware(kind)
    for key in h:
        if key in config:h[key]=config[key]
    if kind=='cpu':
        h['enable_m']='M' in config.get('extensions',['M'])
        h['enable_zbb']='Zbb' in config.get('extensions',[])
        h['alu_ports']=config.get('execution_ports',h['alu_ports'])
    if kind=='isp' and 'stages' in config:
        for key in ('black_level','gain','demosaic','gamma'):h[key+'_enabled']=key in config['stages']
    return validate_hardware(kind,h)


def hardware_from_template(model):
    """仅转换带明确硬件定义的教学模板；不猜测商业CPU的RTL。"""
    if not isinstance(model,dict) or not isinstance(model.get('hardware'),dict):
        raise ValueError('该模板只有SoC参数，未提供可执行硬件定义；可在LAB新建自己的核心。')
    return validate_hardware('cpu',model['hardware'])
