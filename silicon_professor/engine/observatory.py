"""已运行模型的确定性回放；加速器计算轴与汇总传输账本分开。"""
from .isa import LOADS, STORES, BRANCHES, M_OPS
from .lab_cpu import architectural_state_at


def _phase(result,cycle):
    if cycle==result['cycles']:return '完成'
    return '计算' if cycle<result['compute_cycles'] else '传输账本'


def execution_snapshot(result,cycle,thread=0):
    if type(cycle) is not int or not 0<=cycle<=result['cycles']:
        raise ValueError('回放周期须在0与总周期之间。')
    kind=result['kind']
    if kind=='cpu':return _cpu(result,cycle,thread)
    if kind=='gpu':return _gpu(result,cycle)
    if kind=='npu':return _npu(result,cycle)
    if kind=='isp':return _isp(result,cycle)
    raise ValueError('观测台只接受CPU/GPU/NPU/ISP结果。')


def _cpu(result,cycle,thread):
    state=architectural_state_at(result,cycle,thread);active=[]
    for row in result['rows']:
        if not row['dispatch']<=cycle<row['retire']:continue
        ins=row['instruction'];op=ins.op
        unit=row.get('unit','memory' if op in LOADS|STORES else 'multiply' if op in M_OPS else 'branch' if op in BRANCHES or op=='FENCE' else 'alu')
        stage='等待' if cycle<row['issue'] else '执行' if cycle<row['done'] else '待提交'
        active.append(dict(id=row['id'],thread=row.get('thread',0),unit=unit,stage=stage,
            text=ins.text,dispatch=row['dispatch'],issue=row['issue'],done=row['done'],retire=row['retire'],
            cache='合并未命中' if row.get('merged_miss') else '命中' if row.get('cache_hit') else '未命中' if 'cache_hit' in row else ''))
    return dict(state,kind='cpu',cycle=cycle,thread=thread,active=active,
        phase='完成' if cycle==result['cycles'] else '运行',
        rob_occupancy=len(active),retired_total=sum(r['retire']<=cycle for r in result['rows']))


def _gpu(result,cycle):
    active=[];output=[None]*len(result['output'])
    for w in result['warps']:
        if w['finish']<=cycle:
            start=w['first_lane'];end=start+w['active_lanes'];output[start:end]=result['output'][start:end]
        for event in w['issues']:
            if event['cycle']<=cycle<event['done']:
                slot=w['slots'][event['slot']]
                active.append(dict(warp=w['warp'],processor=w['processor'],op=slot['op'],lanes=slot['lanes'],
                    issue=event['cycle'],done=event['done']))
    return dict(kind='gpu',cycle=cycle,phase=_phase(result,cycle),active=active,output=output,
        completed=sum(v is not None for v in output))


def _wrap(value,bits):
    value%=1<<bits
    return value-(1<<bits) if value>=1<<(bits-1) else value


def _npu(result,cycle):
    a,b=result['input_a'],result['input_b'];k=len(b);bits=result['accumulator_bits']
    output=[[None]*len(result['output'][0]) for _ in result['output']]
    accumulators=[[0]*result['array_cols'] for _ in range(result['array_rows'])]
    active=[];start=0;tile_index=None
    for index,tile in enumerate(result['tiles']):
        end=start+tile['compute_cycles'];elapsed=min(tile['compute_cycles'],max(0,cycle-start))
        current=start<=cycle<end
        if current:tile_index=index
        for i in range(tile['rows']):
            for j in range(tile['cols']):
                terms=min(k,max(0,elapsed-i-j))
                y,x=tile['row']+i,tile['col']+j
                value=_wrap(sum(a[y][t]*b[t][x] for t in range(terms)),bits)
                if terms:output[y][x]=value
                if current:
                    accumulators[i][j]=value;t=cycle-start-i-j
                    if 0<=t<k:active.append(dict(row=i,col=j,k=t,a=a[y][t],b=b[t][x],accumulator=value))
        start=end
    if cycle>=result['compute_cycles']:output=[list(row) for row in result['output']]
    return dict(kind='npu',cycle=cycle,phase=_phase(result,cycle),active=active,output=output,
        accumulators=accumulators,tile=tile_index)


def _isp(result,cycle):
    stages=list(result['stage_outputs']);pixels=result['pixels'];ppc=result['pixels_per_cycle']
    emitted=min(pixels,max(0,cycle-result['fill_cycles']-result['stage_latency'])*ppc)
    width=len(result['output'][0]);output=[[None]*width for _ in result['output']]
    for i in range(emitted):output[i//width][i%width]=list(result['output'][i//width][i%width])
    counts={key:min(pixels,max(0,cycle-result['fill_cycles']-index)*ppc) for index,key in enumerate(stages)}
    counts['quantize']=emitted
    return dict(kind='isp',cycle=cycle,phase=_phase(result,cycle),active=[],output=output,
        emitted_pixels=emitted,stages=counts)
