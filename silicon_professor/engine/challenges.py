"""确定性项目验收与可运行参考方案；随机市场评分不决定通关。"""
from ..data.challenges import CHALLENGES


def challenge_design(sid,solution=False):
    from .types import empty_design,CoreGroup
    from ..data.core_designs import default_hardware
    from .ip_library import make_design_asset,attach_asset
    c=CHALLENGES[sid];d=empty_design(c['base']);d.scenario_id=sid
    d.name=c['name']+' / '+('参考方案' if solution else '我的方案')
    if c['base']=='sandbox':d.cooling_id='laptop';d.package_id='imc25d'
    if sid=='challenge_bin':
        d.cores[0].clock=3.9;d.pvt_corner='tt'
        if solution:
            d.pvt_corner='ss'
            for g in d.cores:g.clock=min(g.clock,2.1)
    if sid=='challenge_thermal':
        d.ambient_c=30
        if solution:
            d.cores=[CoreGroup('a715',2,.512,False,2.),CoreGroup('a510',4,.256,False,1.6)]
            d.gpu_units=8;d.cooling_id='vcPro';d.npu_id='npu8'
    if sid=='challenge_bandwidth':
        d.workload_parallel=.99;d.workload_intensity=.1;d.memory_channels=8 if solution else 1
    if sid=='challenge_serial':
        d.workload_parallel=.2
        if solution:d.cores=[CoreGroup('x925',2,2.,False,3.4)]
    if sid=='challenge_open' and solution:
        d.cores=[CoreGroup('p670',4,1.,False,2.5)];d.eco_invest=.8
    if sid=='challenge_lab_cpu' and solution:
        d.cores=[];h=default_hardware('cpu');h['issue_order']='in_order'
        attach_asset(d,make_design_asset('cpu','isqi / 顺序核',h))
    if sid=='challenge_camera' and solution:
        h=default_hardware('npu');h.update(rows=8,cols=8,scratchpad_kb=8)
        attach_asset(d,make_design_asset('npu','isqi / 影像阵列',h))
        attach_asset(d,make_design_asset('isp','isqi / RAW流水线',default_hardware('isp')))
    if sid=='challenge_simt' and solution:
        h=default_hardware('gpu');h['alu_latency']=8
        attach_asset(d,make_design_asset('gpu','isqi / Warp交错',h))
    if sid=='challenge_compact' and solution:
        d.cores=[CoreGroup('a725',2,.512,False,2.7),CoreGroup('a520',4,.256,False,1.8)]
        d.gpu_units=10;d.l3_mb=4;d.npu_id='npu16'
    if sid=='challenge_chiplet' and solution:d.chiplet=True
    if sid=='challenge_supply' and solution:
        d.node_id='n4p';d.cores=[CoreGroup('a725',2,1.,False,2.4),CoreGroup('a520',4,.256,False,1.8)]
        d.gpu_units=10;d.l3_mb=6
    if sid=='challenge_margin':
        d.price=38
        if not solution:d.cores[0].clock=3.3
        else:d.cores[0].clock=2.4
    if solution:d.pdn_quality=1.;d.verification_effort=1.
    return d


def challenge_report(design,result):
    from ..data.cores import get_ip
    from .core_studio import run_design
    case=CHALLENGES.get(design.scenario_id)
    if case is None:return None
    active=[g for g in design.cores if g.count>0]
    cpu=[design.embedded_ips[g.core_id[3:]] for g in active if g.core_id.startswith('ip:')]
    def bound(kind):return design.embedded_ips.get(design.ip_blocks.get(kind),{})
    gpu=bound('gpu');npu=bound('npu');isp=bound('isp')
    gh=gpu.get('design',{}).get('hardware',{})
    ih=isp.get('design',{}).get('hardware',{})
    values=dict(corner=design.pvt_corner,bin=result['bin']['fraction'],peak=result['power']['peak'],
        sustain=result['perf']['sustain_ratio'],st=result['perf']['st_burst'],ambient=design.ambient_c,
        achievable=result['engineering']['workload']['achievable'],intensity=design.workload_intensity,
        parallel=design.workload_parallel,core_count=sum(g.count for g in active),
        all_riscv=bool(active) and all(get_ip(design,g.core_id)['isa']=='riscv' for g in active),eco=design.eco_invest,
        custom_cpu=sum(g.count for g in active if g.core_id.startswith('ip:')),
        cpu_in_order=bool(cpu) and all(a.get('design',{}).get('hardware',{}).get('issue_order')=='in_order' and a['config']['architecture']=='riscv32' for a in cpu),
        verification=result['engineering']['verification_completion'],custom_isp=bool(isp),custom_npu=bool(npu),
        npu_peak=result['plan'].metrics['npu']['tops'],isp_demosaic=ih.get('demosaic_enabled',False),
        custom_gpu=bool(gpu),gpu_fixed_resources=gh.get('processors')==2 and gh.get('warp_size')==8 and gh.get('alu_latency')==8,
        gpu_cycles=run_design('gpu',gh)['compute_cycles'] if gh else 1_000_000,
        die=result['die_area'],gpu=result['perf']['gpu'],chiplet=design.chiplet,package=design.package_id,
        node=design.node_id,margin=(design.price-result['cost']['total'])/design.price,price=design.price,
        no_tuning=design.bench_tuning==0 and design.bench_isa==0)
    checks=[]
    for rule in case['rules']:
        value=values[rule['metric']];target=rule['target']
        ok={'eq':lambda:value==target,'ge':lambda:value>=target,'le':lambda:value<=target}[rule['op']]()
        checks.append(dict(**rule,value=value,ok=bool(ok)))
    return dict(id=case['id'],ready=all(r['ok'] for r in checks),checks=checks,
                scope='虚构委托的确定性验收；不是实物基准、商业授权或EDA签核')
