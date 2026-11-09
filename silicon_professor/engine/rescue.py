"""历史故障的反事实教学实验；验收基于可计算结果，不基于名气。"""
from copy import deepcopy
import json
import math
from pathlib import Path

from ..data.rescue import RESCUE_CASES,FIELDS,default_controls
MODEL='rescue-chip-evidence-v2'


def validate_controls(cid,controls=None):
    if not isinstance(cid,str) or cid not in RESCUE_CASES:raise ValueError('未知拯救芯片案例。')
    fields=FIELDS[RESCUE_CASES[cid]['kind']];p=default_controls(cid)
    if controls is not None:
        if not isinstance(controls,dict) or set(controls)-set(p):raise ValueError('无法识别的试验参数。')
        p.update(deepcopy(controls))
    for f in fields:
        value=p[f['key']]
        if 'options' in f:ok=type(value) is type(f['default']) and value in [v for v,_ in f['options']]
        elif type(f['default']) is bool:ok=type(value) is bool
        else:ok=type(value) in (int,float) and math.isfinite(value) and f['min']<=value<=f['max']
        if not ok:raise ValueError(f"参数 {f['key']} 超出本实验范围。")
    return p


def check(cid,title,ok,value):return dict(id=cid,title=title,ok=bool(ok),value=value)


def _divider(p):
    from fractions import Fraction
    # The documented five divisor columns and +2-to-0 omission, checked locally.
    states=[(Fraction(1),Fraction(1)),(Fraction(1,2),Fraction(3,2))]
    if p['coverage']=='boundary':states += [(Fraction(8,3)*Fraction(d,16)-Fraction(1,1024),Fraction(d,16)) for d in (17,20,23,26,29)]
    rows=[]
    for partial,d in states:
        allowed=[q for q in (-2,-1,0,1,2) if abs(4*(partial-q*d))<=Fraction(8,3)*d]
        reference=min(allowed,key=lambda q:abs(partial-q*d))
        observed=0 if p['divider']=='missing_entry' and d in [Fraction(v,16) for v in (17,20,23,26,29)] and reference==2 else reference
        nxt=4*(partial-observed*d);valid=abs(nxt)<=Fraction(8,3)*d
        rows.append((str(d),str(partial),reference,observed,str(nxt),valid))
    okay=all(row[-1] for row in rows)
    steps=53 if p['divider']=='software' else 27;retention=27/steps
    return dict(columns=('D','部分余数p','合法商位','返回商位','下一部分余数','边界通过'),rows=rows,
        metrics=dict(passed=sum(row[-1] for row in rows),vectors=len(rows),quotient_steps=steps,performance_retention=retention),
        checks=[check('coverage','检查五个文献记录的漏项D列',p['coverage']=='boundary',p['coverage']),
                check('functional','下一部分余数保持SRT收敛边界',okay,f'{sum(row[-1] for row in rows)}/{len(rows)}'),
                check('performance_retention','同精度商位吞吐保留至少85%（教学）',retention>=.85,retention)],
        consequence='五个错误+2→0表项是芯片问题；修正边界不证明完整carry-save或IEEE754符合性。53位精度下radix4约27商位步骤、串行逐bit53步骤，仅为算法工作量对照，不是Pentium实测延迟。')


def _tlb(p):
    bad=p['stress'] and p['policy']=='unchecked';walks=64 if p['policy']=='serialize' else 16
    cycles=walks*20+(64-walks)*2;baseline=16*20+48*2;retention=baseline/cycles
    rows=[('1','读取PTE到L2','A=0 / D=0'),('2','开始更新A/D位','读改写窗口'),
          ('3','缓存驱逐','旧PTE进入L3' if bad else '缓存旁路' if p['policy']=='serialize' else '原子修订序列'),
          ('4','外部探测','触及不原子窗口' if p['stress'] else '没有压力探测'),
          ('5','A/D与一致性检查','更新丢失/潜在一致性错误' if bad else '保持更新与一致性')]
    return dict(columns=('事件','动作','状态'),rows=rows,
        metrics=dict(cycles=cycles,baseline_cycles=baseline,pte_walks=walks,performance_retention=retention),
        checks=[check('coverage','覆盖PTE A/D更新-驱逐-探测窗口',p['stress'],p['stress']),
                check('coherency','PTE更新与一致性保持',not bad,not bad),
                check('performance_retention','页表工作集吞吐保留至少85%（教学）',retention>=.85,retention)],
        consequence='对应AMD勘误298的事件不变量；规避模式对应禁用TLB相关缓存路径，而非所有load强制串行。16页×4遍、walk20周期/cache2周期是教学输入；不能声称AMD真实规避损失该百分比。')


def _sata(p):
    revised=p['ports']=='revised';isolated=p['ports']=='disable_3g'
    native=2 if isolated else 6;external=2 if isolated and p['external'] else 0
    rows=[(i,'6Gb/s组' if i<2 else '3Gb/s组','隔离' if isolated and i>=2 else '可用',
           '教学风险' if i>=2 and not revised and not isolated else '无注入风险') for i in range(6)]
    if external:rows.append(('外部','控制器','2个设备','额外延迟与集成'))
    safe=revised or isolated
    # Four-device saturated workload: two 6 Gb/s + two 3 Gb/s links.
    # Link rates and bridge bandwidth are a task contract, not observed disk throughput.
    bandwidth=12+min(6,p['external_bandwidth_gbps']) if external else 12 if isolated else 18
    retention=bandwidth/18
    return dict(columns=('端口','分组','状态','可靠性'),rows=rows,
        metrics=dict(usable_devices=native+external,required_devices=4,external_devices=external,bridge_cycles=16 if external else 0,
                     baseline_bandwidth_gbps=18,aggregate_bandwidth_gbps=bandwidth,performance_retention=retention),
        checks=[check('isolation','不使用原版风险端口',safe,safe),
                check('devices','保持四个设备可连接',native+external>=4,native+external),
                check('performance_retention','四设备饱和吞吐保留至少85%（教学）',retention>=.85,retention)],
        consequence='隔离不等于恢复原能力；两外部设备共享控制器带宽。合同按两6Gb/s+两3Gb/s链路推导原始18Gb/s，不是磁盘实测吞吐，不含协议开销。端口分组/桥接周期仍为教学假设，不模拟电气老化。')


def run_rescue(cid,controls=None):
    p=validate_controls(cid,controls);case=RESCUE_CASES[cid]
    if case.get('experiment_status')=='model_pending':
        from ..data.rescue_measurements import chip_record
        chip=chip_record(cid)
        from .rescue_performance import performance_contract
        rows=[(o['test'],str(o['value']),o['unit'],o['version'] or '未披露/不适用') for o in chip['observations']]
        return dict(id=cid,model=MODEL,parameters=p,ready=False,parameter_basis='source_record',calibrated=False,
            scope=case['scope'],conditions=case['conditions'],confidence='documented_baseline_unmodelled_counterfactual',sources=case['sources'],
            columns=('实测工作负载','结果','单位','版本'),rows=rows,metrics={},chip=chip,performance_contract=performance_contract(cid),
            checks=[check('chip_model','原始测量已录入；芯片级反事实求解尚未校准',False,'不使用通用模型授予通关')],
            consequence='没有足够芯片级性能/电压/功率数据，当前仅显示原始测量；不能通过任意降压/降频使这颗芯片被判修复。待接入分负载估计后，单核≥90%、多核/GPU≥85%，持续绝对性能不退步；门槛是游戏合同，不是厂商规格。')
    result={'divider':_divider,'tlb':_tlb,'sata':_sata}[case['kind']](p)
    return dict(result,id=cid,model=MODEL,parameters=p,ready=all(c['ok'] for c in result['checks']),
        parameter_basis='game_assumption',calibrated=False,scope=case['scope'],conditions=deepcopy(case['conditions']),
        confidence=case['confidence'],sources=list(case['sources']))


def export_rescue(path,cid,controls):
    from ..data.sources import SOURCES
    result=run_rescue(cid,controls);case=RESCUE_CASES[cid]
    payload=dict(format='silicon-rescue',model=MODEL,id=cid,parameters=result['parameters'],
        case=case,sources={sid:SOURCES[sid] for sid in case['sources']},result=result)
    path=Path(path);path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return path


def read_rescue(path):
    path=Path(path)
    if path.stat().st_size>2_000_000:raise ValueError('实验记录超过2MB。')
    try:record=json.loads(path.read_text(encoding='utf-8'))
    except (ValueError,UnicodeError) as ex:raise ValueError('无法读取实验JSON。') from ex
    if not isinstance(record,dict) or record.get('format')!='silicon-rescue' or record.get('model') not in (MODEL,'rescue-teaching-v1'):
        raise ValueError('不是本版支持的拯救芯片实验记录。')
    result=run_rescue(record.get('id'),record.get('parameters'))
    if record['model']!=MODEL:result['migration_note']='旧通用模型已停用，重算不继承旧通关或性能数值。'
    return result
