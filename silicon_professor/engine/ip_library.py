"""版本化实验 IP 资产。导入重新运行固定向量，分数/验证标志不作为可信输入。"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

from .labs import DEFAULTS,run_experiment
from ..version import producer,compatibility_notes,diagnostic
from ..data.architectures import ISA_FAMILIES

FORMAT='silicon-professor/ip'
ASSET_KINDS={'cpu','gpu','npu','isp'}
EXAMPLES={
    'riscv32':('ADDI x1,x0,6\nADDI x2,x0,7\nADD x3,x1,x2\nSW x3,0(x0)\nLW x3,0(x0)\nHALT',3,13),
    'x86_32':('MOV EAX,6\nMOV EBX,7\nADD EAX,EBX\nMOV [0],EAX\nMOV EAX,[0]\nHALT',0,13),
    'x86_64':('MOV RAX,6\nMOV RBX,7\nADD RAX,RBX\nMOV R8,0\nMOV [R8],RAX\nMOV RAX,[R8]\nHALT',0,13),
    'aarch64':('MOV X0,#6\nMOV X1,#7\nADD X2,X0,X1\nMOV X3,#0\nSTR W2,[X3]\nLDR W2,[X3]\nHALT',2,13),
}


def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def validate_config(kind,config):
    if kind not in ASSET_KINDS or not isinstance(config,dict) or set(config)-set(DEFAULTS[kind]):
        raise ValueError('IP类别或配置字段不支持。')
    merged=copy.deepcopy(DEFAULTS[kind]);merged.update(config)
    for key,value in merged.items():
        expected=DEFAULTS[kind][key]
        if isinstance(expected,str):
            if not isinstance(value,str) or len(value)>100000:raise ValueError('IP文本字段无效或过长。')
        elif isinstance(expected,list):
            if not isinstance(value,list) or any(v not in ('M','Zbb') for v in value) or len(value)!=len(set(value)):raise ValueError('扩展列表无效。')
        elif type(expected)==int:
            if type(value)!=int or abs(value)>1000000:raise ValueError('整数字段无效。')
        elif type(expected)==float:
            if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1000000:raise ValueError('数值字段无效。')
    if kind=='cpu' and merged['architecture'] not in EXAMPLES:raise ValueError('不支持此ISA执行器。')
    return merged


def verify(kind,config):
    r=run_experiment(kind,config)
    if not r.get('functional_check',False):raise ValueError('功能检查未通过（可能发生累加器溢出）。')
    if kind=='npu' and not r['scratchpad_fits']:raise ValueError('NPU tile超出本地scratchpad容量。')
    checks=['user-input-model-completed']
    if kind=='cpu':
        source,register,value=EXAMPLES[config['architecture']]
        p=dict(config,source=source,memory='')
        tested=run_experiment(kind,p)
        if tested['registers'][register]!=value or tested['memory'].get(0)!=value:raise ValueError('固定加法/访存向量未通过。')
        checks+=['fixed-add-store-load-vector']
    elif kind=='npu':
        p=dict(config,m=2,n=2,k=2)
        from .lab_accelerators import npu_lab
        tested=npu_lab(**p,a=[[1,2],[3,4]],b=[[5,6],[7,8]])
        if tested['output']!=[[19,22],[43,50]]:raise ValueError('GEMM固定向量失败。')
        checks+=['2x2-gemm-hand-reference']
    elif kind=='isp':
        from .lab_accelerators import isp_lab
        p=dict(config,width=4,height=4,black_level=64,gain=1,gamma=1)
        tested=isp_lab(**p,raw=[[64]*4 for _ in range(4)])
        if any(channel for row in tested['output'] for pixel in row for channel in pixel):raise ValueError('黑电平固定向量失败。')
        checks+=['black-level-zero-frame']
    else:checks+=['fp32-per-lane-reference']
    return dict(passed=True,checks=checks,model='lab-ip-v1',scope='functional-model-self-tests; not RTL/ISA compliance',
                cycles=r['cycles'],observed_ipc=r.get('ipc'))


def make_asset(kind,name,config):
    if not isinstance(name,str) or not name.strip() or len(name)>64:raise ValueError('IP名称为1..64字符。')
    config=validate_config(kind,config)
    verification=verify(kind,config)
    digest=hashlib.sha256(canonical(dict(kind=kind,name=name.strip(),config=config)).encode()).hexdigest()
    return dict(format=FORMAT,version=1,id=digest[:32],digest=digest,name=name.strip(),kind=kind,
                producer=producer(),
                config=config,verification=verification,parameter_basis='game_assumption')


def make_design_asset(kind,name,hardware):
    from .core_studio import SCHEMA,validate_hardware,verify_design,mapped_config
    if not isinstance(name,str) or not name.strip() or len(name)>64:raise ValueError('IP名称为1..64字符。')
    design=dict(schema=SCHEMA,hardware=validate_hardware(kind,hardware))
    verification=verify_design(kind,design['hardware'])
    if not verification['passed']:raise ValueError('核心固定验证未通过：'+', '.join(c['name'] for c in verification['cases'] if not c['passed']))
    digest=hashlib.sha256(canonical(dict(kind=kind,name=name.strip(),design=design)).encode()).hexdigest()
    return dict(format=FORMAT,version=1,id=digest[:32],digest=digest,name=name.strip(),kind=kind,
                identity_basis='kind/name/design',design=design,producer=producer(),
                config=mapped_config(kind,design['hardware']),verification=verification,parameter_basis='game_assumption')


def validate_asset(record):
    if not isinstance(record,dict) or record.get('format')!=FORMAT:
        raise ValueError('不支持的IP文件格式或版本。')
    if record.get('identity_basis')=='kind/name/design':
        from .core_studio import SCHEMA
        design=record.get('design')
        if not isinstance(design,dict) or design.get('schema')!=SCHEMA or set(design)-{'schema','hardware'}:
            raise ValueError('本版无法解释此核心硬件结构。')
        asset=make_design_asset(record.get('kind'),record.get('name'),design.get('hardware'))
        digest=hashlib.sha256(canonical(dict(kind=record['kind'],name=record['name'].strip(),design=design)).encode()).hexdigest()
        if record.get('digest')!=digest or record.get('id')!=digest[:32]:raise ValueError('硬件定义的内容摘要不匹配。')
        preserved=copy.deepcopy(record)
        preserved.update(design=copy.deepcopy(design),config=asset['config'],verification=asset['verification'],parameter_basis='game_assumption')
        preserved['compatibility_notes']=compatibility_notes(record,1)
        return preserved
    if 'identity_basis' in record or 'design' in record:raise ValueError('无法识别核心资产的身份结构；不能忽略硬件定义。')
    kind=record.get('kind');config=record.get('config')
    if kind not in ASSET_KINDS or not isinstance(config,dict):raise ValueError('IP类别或配置无效。')
    known={key:value for key,value in config.items() if key in DEFAULTS[kind]}
    asset=make_asset(kind,record.get('name'),known)
    raw_digest=hashlib.sha256(canonical(dict(kind=kind,name=record['name'].strip(),config=config)).encode()).hexdigest()
    if record.get('digest') not in (asset['digest'],raw_digest) or record.get('id')!=record.get('digest','')[:32]:raise ValueError('IP内容摘要不匹配；文件被修改或损坏。')
    preserved=copy.deepcopy(record)
    preserved.update(verification=asset['verification'],parameter_basis='game_assumption')
    preserved['compatibility_notes']=compatibility_notes(record,1)
    if set(config)-set(DEFAULTS[kind]):preserved['compatibility_notes'].append('保留未识别的附加配置字段，但本版不会使用这些字段计算结果。')
    return preserved


def read_asset(path):
    p=Path(path)
    if p.stat().st_size>2_000_000:raise ValueError('IP文件超过2MB。')
    try:record=json.loads(p.read_text('utf-8'))
    except (UnicodeError,json.JSONDecodeError,RecursionError) as ex:raise ValueError('IP文件不是有效UTF-8 JSON，或嵌套过深。') from ex
    try:return validate_asset(record)
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError) as ex:raise ValueError(f'{ex}\n{diagnostic(record)}') from ex


def write_asset(path,record):
    asset=validate_asset(record);p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if not p.suffix:p=p.with_suffix('.cor')
    asset['producer']=producer()
    p.write_text(json.dumps(asset,ensure_ascii=False,indent=2,allow_nan=False)+'\n','utf-8');return p


def attach_asset(design,record):
    from .types import CoreGroup
    asset=validate_asset(record)
    from ..data.segments import SEGMENTS
    if 'custom' not in SEGMENTS[design.scenario_id]['allowed_licenses']:raise ValueError('定制IP当前仅在研究沙盒和开放核心挑战使用，非真实采购授权。')
    if asset['kind']=='cpu':
        isa=asset['config'].get('architecture','riscv32')
        from ..data.cores import get_ip
        family=ISA_FAMILIES[isa]
        active=[get_ip(design,g.core_id) for g in design.cores if g.count>0]
        if design.scenario_id!='sandbox' and any(ip and ip['isa']!=family and not (family.startswith('arm') and ip['isa'].startswith('arm')) for ip in active):
            raise ValueError('应用核集群的ISA不同；先在架构页清空原CPU组，或使用相同架构IP。')
        design.cores.append(CoreGroup('ip:'+asset['id'],1,1.0,False,0.0))
    else:
        design.ip_blocks[asset['kind']]=asset['id']
        if asset['kind']=='gpu':design.gpu_units=asset['config']['processors']
        if asset['kind']=='isp':design.isp=True
    design.embedded_ips[asset['id']]=copy.deepcopy(asset)
    design.placements.clear()


@lru_cache(maxsize=128)
def _model(kind,name,config_json):
    p=json.loads(config_json)
    if kind=='cpu':
        source,_,_=EXAMPLES[p['architecture']]
        # 固定验证任务用于本模型性能标尺；任务IPC不可当跨架构能力排名。
        r=run_experiment('cpu',dict(p,source=source,memory=''))
        logic=1.6+.28*p['width']+.0025*p['rob_size']+.006*p['cache_kb']+.18*p['execution_ports']
        delay=2600+60*(p['width']-6)+50*(p['execution_ports']-6)+.25*(p['rob_size']-320)
        fmax=1000/(delay/p['pipeline']+70)
        return dict(id='custom_ip',name=name,vendor='LAB',arch=p['architecture'],isa=ISA_FAMILIES[p['architecture']],
            year=2026,tier='big',license='custom',ref_node='n3e',ipc=max(.15,min(2.5,r['ipc']*3)),
            fmax_ref=fmax,logic_area=logic,l2_default=1.0,l2_max=8.0,power_ref=.8+.12*p['width']+.001*p['rob_size']+.1*p['execution_ports'],
            leak_frac=.16,license_cost_m=0.0,eng_weeks=24,decode=p['width'],rob=p['rob_size'],measured_ipc=r['ipc'],
            evidence=[],confidence='assumption',parameter_basis='game_assumption',note='固定实验任务IPC；PPA未校准，不作跨ISA能力排名。')
    if kind=='gpu':
        return dict(id='labgpu',name=name,vendor='LAB',year=2026,ref_node='n3e',unit_name='SIMT处理器',
            min_units=p['processors'],max_units=p['processors'],default_units=p['processors'],
            perf_per_unit=30*p['warp_size']/8,area_per_unit=.5+.05*p['warp_size'],power_per_unit=.1*p['frequency_ghz'],license_cost_m=0.,compat=.8,cu_per_unit=1,
            evidence=[],confidence='assumption',parameter_basis='game_assumption',note='SIMT计算实验，不代表完整图形GPU或驱动。')
    if kind=='npu':
        return dict(id='labnpu',name=name,tops=2*p['rows']*p['cols']*p['frequency_ghz']/1000,
            area=.2+.004*p['rows']*p['cols']+.002*p['scratchpad_kb'],power=.1+.002*p['rows']*p['cols']*p['frequency_ghz'],license_cost_m=0.,
            evidence=[],confidence='assumption',parameter_basis='game_assumption',note='稠密整数阵列峰值：每MAC两次op，不混用模型TOPS。')
    return dict(id='isp',name=name,area=.5+.3*p['pixels_per_cycle'],power=.1*p['pixels_per_cycle']*p['frequency_ghz'],
        license_cost_m=0.,edge=False,color='#799683',parameter_basis='game_assumption')


def asset_model(record):
    if record.get('identity_basis')=='kind/name/design':
        from .core_studio import design_model
        return design_model(record['kind'],record['name'],record['design']['hardware'])
    kind=record['kind'];config=dict(DEFAULTS[kind],**{k:v for k,v in record['config'].items() if k in DEFAULTS[kind]})
    return copy.deepcopy(_model(kind,record['name'],canonical(config)))


def block_model(design,kind,default):
    asset_id=design.ip_blocks.get(kind)
    record=design.embedded_ips.get(asset_id)
    return asset_model(record) if record and record['kind']==kind else default
