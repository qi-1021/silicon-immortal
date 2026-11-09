"""共享资源的轨迹调度；非完整推测CPU、OS或缓存一致性模拟。"""
from .isa import LOADS,STORES,BRANCHES,M_OPS,write_memory
from .lab_memory import Cache


def schedule_threads(sources,*,width=2,rob_size=32,execution_ports=2,pipeline=8,
        cache_kb=16,hit_latency=2,miss_latency=40,multiply_latency=3,memory=None,
        max_cycles=200000,extensions=('M',),architecture='riscv32',issue_order='out_of_order',
        alu_ports=2,multiply_ports=1,cache_ways=4,cache_line_bytes=64,mshrs=1,branch_predictor='none'):
    from .arch_cpu import execute_architecture
    if len(sources) not in (1,2) or any(not isinstance(s,str) or len(s)>100000 for s in sources):raise ValueError('最多两个、每个不超过100000字符的汇编程序。')
    if any(type(v) is not int or not 1<=v<=12 for v in (width,execution_ports,alu_ports,multiply_ports)):raise ValueError('共享宽度/资源为1..12。')
    if type(rob_size) is not int or not len(sources)<=rob_size<=1024:raise ValueError('ROB容量必须至少容纳每线程一条指令。')
    if not 2<=pipeline<=32 or not 1<=hit_latency<=miss_latency<=1000 or not 1<=multiply_latency<=100:raise ValueError('检查执行延迟。')
    if issue_order not in ('in_order','out_of_order') or branch_predictor not in ('none','two_bit') or type(mshrs) is not int or not 1<=mshrs<=16:raise ValueError('检查调度/预测器/MSHR。')
    refs=[execute_architecture(architecture,s,memory,extensions) for s in sources]
    cache=Cache(int(cache_kb)*1024,cache_line_bytes,cache_ways)
    n=len(refs);quota=rob_size//n;rows=[];done=set();pending={};cycle=uid=turn=0
    ctx=[]
    for r in refs:
        # virtual bench addresses map to separate physical regions; no cross-thread communication.
        pcs=[v['pc'] for v in r['listing']];fallthrough={a:b for a,b in zip(pcs,pcs[1:])}
        ctx.append(dict(ref=r,next=0,rob=[],rat={},barrier=None,fetch=pipeline,
            regs=[0]*len(r['registers']),mem={a:v&0xffffffff for a,v in (memory or {}).items()},
            predictor=[1]*256,fallthrough=fallthrough,retired=0,finish=0))
    stalls=dict(rob_full=0,dependencies=0,branch=0,mshr_full=0);prediction=dict(branches=0,mispredictions=0);merges=0
    while any(c['next']<len(c['ref']['trace']) or c['rob'] for c in ctx):
        cycle+=1
        if cycle>max_cycles:raise ValueError('超过周期上限。')
        pending={k:v for k,v in pending.items() if v>cycle}
        for tid,c in enumerate(ctx):
            for e in c['rob']:
                if e['done']==cycle:
                    done.add(e['id'])
                    if c['barrier']==e['id']:
                        c['barrier']=None;penalty=1
                        if e['instruction'].op in BRANCHES:
                            prediction['branches']+=1
                            if branch_predictor=='none':penalty=pipeline
                            else:
                                wrong=e['predicted']!=e['taken'];prediction['mispredictions']+=int(wrong);penalty=pipeline if wrong else 1
                                idx=(e['pc']//4)%256;old=c['predictor'][idx];c['predictor'][idx]=min(3,old+1) if e['taken'] else max(0,old-1)
                        c['fetch']=cycle+penalty
        # Per-thread in-order retirement, one shared physical retire budget.
        retired=0
        for i in range(n):
            c=ctx[(turn+i)%n]
            while c['rob'] and c['rob'][0]['id'] in done and retired<width:
                e=c['rob'].pop(0);e['retire']=cycle;c['retired']+=1;c['finish']=cycle;retired+=1
                ins=e['instruction'];writes=e.get('writes',{ins.rd:e['value']} if ins.rd not in (None,c['ref']['zero_register']) else {})
                for reg,value in writes.items():c['regs'][reg]=value
                if ins.op in STORES:write_memory(c['mem'],e['address'],e['store_bits'],e['store_value'])
        limits=dict(alu=alu_ports,multiply=multiply_ports,memory=1,branch=1);used={k:0 for k in limits};issued=0
        candidates=[]
        for tid,c in enumerate(ctx):
            older=[]
            for e in c['rob']:
                if e['issue'] is not None:older.append(e);continue
                ins=e['instruction'];mem=ins.op in LOADS|STORES
                ready=e['dispatch']<cycle and all(dep in done for dep in e['deps'])
                if mem:
                    blockers=[v for v in older if v['instruction'].op in LOADS|STORES or v['instruction'].op=='FENCE']
                    if mshrs==1 or ins.op in STORES:ready=ready and all(v['id'] in done for v in blockers)
                    else:ready=ready and all(v['id'] in done for v in blockers if v['instruction'].op in STORES or v['instruction'].op=='FENCE')
                if ready:candidates.append(e)
                older.append(e)
                if issue_order=='in_order':break
        for e in sorted(candidates,key=lambda e:(e['dispatch'],(e['thread']-turn)%n,e['id'])):
            if issued>=execution_ports:break
            unit=e['unit']
            if used[unit]>=limits[unit]:continue
            latency=multiply_latency if unit=='multiply' else 1
            if unit=='memory':
                addr=e['address']+e['thread']*(1<<20);block=addr//cache_line_bytes
                if block in pending:
                    latency=max(1,pending[block]-cycle);e['cache_hit']=False;e['merged_miss']=True;merges+=1
                else:
                    entries=cache.sets[block%cache.set_count];hit=any(v[0]==block//cache.set_count for v in entries)
                    if not hit and len(pending)>=mshrs:stalls['mshr_full']+=1;continue
                    access=cache.access(addr,write=e['instruction'].op in STORES);e['cache_hit']=access['hit'];e['cache_access']=access
                    latency=hit_latency if access['hit'] else miss_latency
                    if not access['hit']:pending[block]=cycle+latency
            e.update(issue=cycle,done=cycle+latency);used[unit]+=1;issued+=1
        if not issued and any(e['issue'] is None for c in ctx for e in c['rob']):stalls['dependencies']+=1
        # Round-robin front end; all contexts together consume at most width.
        dispatched=0
        for i in range(n):
            tid=(turn+i)%n;c=ctx[tid]
            if c['barrier'] is not None or cycle<c['fetch']:
                stalls['branch']+=int(c['barrier'] is not None);continue
            if len(c['rob'])>=quota:stalls['rob_full']+=1
            while c['next']<len(c['ref']['trace']) and len(c['rob'])<quota and dispatched<width:
                tr=c['ref']['trace'];e=dict(tr[c['next']]);ins=e['instruction'];local=c['next']
                reads=e.get('sources',[r for r in (ins.rs1,ins.rs2) if r not in (None,c['ref']['zero_register'])]);deps={c['rat'][r] for r in reads if r in c['rat']}
                if ins.op=='FENCE':deps.update(v['id'] for v in c['rob'] if v['instruction'].op in LOADS|STORES)
                unit='memory' if ins.op in LOADS|STORES else 'multiply' if ins.op in M_OPS else 'branch' if ins.op in BRANCHES or ins.op=='FENCE' else 'alu'
                e.update(id=uid,local_id=local,thread=tid,deps=deps,dispatch=cycle,issue=None,done=None,retire=None,unit=unit)
                dest=e.get('destinations',[ins.rd] if ins.rd not in (None,c['ref']['zero_register']) else [])
                for r in dest:c['rat'][r]=uid
                c['rob'].append(e);rows.append(e);uid+=1;c['next']+=1;dispatched+=1
                if ins.op in BRANCHES or ins.op=='FENCE':
                    c['barrier']=e['id'];e['taken']=local+1<len(tr) and tr[local+1]['pc']!=c['fallthrough'].get(e['pc'])
                    # Unconditional branches do not require a direction table.
                    e['predicted']=True if e['instruction'].text.split()[0].upper() in ('JMP','JAL','JALR','B','BL') else c['predictor'][(e['pc']//4)%256]>=2
                    break
        turn=(turn+1)%n
    threads=[]
    for tid,c in enumerate(ctx):
        if c['regs']!=c['ref']['registers'] or c['mem']!=c['ref']['memory']:raise AssertionError('线程提交状态与功能解释器不同。')
        threads.append(dict(thread=tid,registers=c['regs'],memory=c['mem'],instructions=c['retired'],cycles=c['finish'],ipc=c['retired']/max(1,c['finish']),register_names=c['ref']['register_names'],listing=c['ref']['listing']))
    r=refs[0]
    return dict(cycles=cycle,instructions=len(rows),ipc=len(rows)/max(1,cycle),rows=rows,threads=threads,
        registers=threads[0]['registers'],memory=threads[0]['memory'],initial_memory={a:v&0xffffffff for a,v in (memory or {}).items()},
        listing=r['listing'],register_names=r['register_names'],register_bits=r['register_bits'],zero_register=r['zero_register'],flags=r.get('flags',{}),
        architecture=architecture,issue_order=issue_order,cache=dict(cache.stats(),merged_requests=merges),stalls=stalls,prediction=prediction,functional_check=True,
        assumptions='轨迹驱动；每线程独立寄存器与地址空间，共享缓存/前端/资源，ROB等分。MSHR按缓存行合并；store/FENCE维持线程内顺序。方向预测只影响解析后的恢复开销，无错误路径执行、BTB、RAS、OS或一致性。')


def run_cpu_pair(source,source2,**kwargs):
    from .lab_cpu import simulate_core
    kwargs=dict(kwargs)
    threads=kwargs.pop('smt_threads',2)
    if type(threads) is not int or threads!=2:
        raise ValueError('双线程对比需要两上下文SMT硬件。')
    a=simulate_core(source,**kwargs);b=simulate_core(source2,**kwargs)
    # smt_threads describes the core, not an unconditional score multiplier.
    result=simulate_core(source,source2=source2,smt_threads=2,**kwargs)
    result.update(sequential_cycles=a['cycles']+b['cycles'],speedup=(a['cycles']+b['cycles'])/max(1,result['cycles']),solo=[a,b])
    return result
