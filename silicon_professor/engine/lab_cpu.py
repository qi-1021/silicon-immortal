"""可执行 RV32I/M 教学子集 + 无分支推测的动态轨迹/ROB 时序模型。

不是完整 RISC-V 实现：不支持特权态、异常入口或二进制取指；提供编码显示。
功能解释器先产生动态轨迹；时序模型基于该轨迹调度，分支解析前禁止获取后继。
延迟与端口是显式教学输入，不能推导真实 Cortex/工艺 PPA。
"""
from __future__ import annotations

from functools import lru_cache
from .isa import assemble, execute, encode, write_memory, LOADS, STORES, BRANCHES, M_OPS

MASK = 0xffffffff
def simulate_core(source, *, width=2, rob_size=32, execution_ports=2,
                  pipeline=8, cache_kb=16, hit_latency=2, miss_latency=40,
                  multiply_latency=3, memory=None, max_cycles=200000, extensions=("M",),architecture='riscv32',
                  issue_order='out_of_order', alu_ports=None, multiply_ports=1,
                  cache_ways=4, cache_line_bytes=64):
    from .lab_memory import Cache
    width, rob_size, execution_ports = int(width), int(rob_size), int(execution_ports)
    if not (1 <= width <= 12 and 1 <= rob_size <= 1024 and 1 <= execution_ports <= 12):
        raise ValueError("宽度为 1..12，ROB 为 1..1024。")
    if not (2 <= pipeline <= 32 and 1 <= hit_latency <= miss_latency <= 1000 and 1 <= multiply_latency <= 100):
        raise ValueError("检查流水线和执行延迟范围。")
    alu_ports=execution_ports if alu_ports is None else alu_ports
    if issue_order not in ('in_order','out_of_order'):
        raise ValueError('发射次序仅支持in_order/out_of_order；没有分支推测。')
    if any(type(v) is not int or not 1<=v<=12 for v in (alu_ports,multiply_ports)):
        raise ValueError('ALU与乘法端口数必须为1..12整数。')
    if type(cache_ways) is not int or cache_ways not in (1,2,4,8) or cache_line_bytes not in (16,32,64,128):
        raise ValueError('Cache ways为1/2/4/8，line为16/32/64/128字节。')
    from .arch_cpu import execute_architecture
    reference = execute_architecture(architecture,source,memory,extensions)
    trace = reference["trace"]
    cache = Cache(capacity_bytes=int(cache_kb) * 1024, line_bytes=cache_line_bytes, ways=cache_ways)
    rob, rat, completed, rows = [], {}, set(), []
    next_id, cycle, barrier_until, branch_barrier = 0, 0, pipeline, None
    retired_regs, retired_mem = [0] * len(reference['registers']), {a: v & MASK for a, v in (memory or {}).items()}
    stalls = dict(rob_full=0, dependencies=0, branch=0)
    while next_id < len(trace) or rob:
        cycle += 1
        if cycle > max_cycles:
            raise ValueError("超过周期上限。")
        for entry in rob:
            if entry["done"] == cycle:
                completed.add(entry["id"])
                if entry["id"] == branch_barrier:
                    branch_barrier = None
                    barrier_until = cycle + (pipeline if entry["instruction"].op in BRANCHES else 1)
        for _ in range(width):
            if not rob or rob[0]["id"] not in completed:
                break
            entry = rob.pop(0)
            entry["retire"] = cycle
            ins = entry["instruction"]
            writes=entry.get('writes',{ins.rd:entry['value']} if ins.rd not in (None,reference['zero_register']) else {})
            for register,value in writes.items():retired_regs[register]=value
            if ins.op in STORES:
                write_memory(retired_mem, entry["address"], entry["store_bits"], entry["store_value"])
        # 无推测、非推测内存序列化；RAW 由重命名依赖标签控制，WAR/WAW 不阻塞执行。
        issued, unit_used = 0, dict(alu=0,multiply=0,memory=0,branch=0)
        unit_limits=dict(alu=alu_ports,multiply=multiply_ports,memory=1,branch=1)
        older_memory = []
        for entry in rob:
            ins = entry["instruction"]
            is_memory = ins.op in LOADS or ins.op in STORES
            ready = all(dep in completed for dep in entry["deps"])
            if is_memory and any(m["id"] not in completed for m in older_memory):
                ready = False
            unit = "memory" if is_memory else "multiply" if ins.op in M_OPS else "branch" if ins.op in BRANCHES or ins.op == "FENCE" else "alu"
            if entry["issue"] is None and entry["dispatch"] < cycle and ready and issued < execution_ports and unit_used[unit]<unit_limits[unit]:
                latency = 1
                if is_memory:
                    hit = cache.access(entry["address"], write=ins.op in STORES)["hit"]
                    latency = hit_latency if hit else miss_latency
                    entry["cache_hit"] = hit
                elif ins.op in M_OPS: latency = multiply_latency
                entry.update(issue=cycle, done=cycle + latency)
                issued += 1
                unit_used[unit]+=1
            if issue_order=='in_order' and entry['issue'] is None:
                break
            if is_memory:
                older_memory.append(entry)
        if rob and issued == 0 and any(e["issue"] is None for e in rob):
            stalls["dependencies"] += 1
        if branch_barrier is not None or cycle < barrier_until:
            stalls["branch"] += int(branch_barrier is not None)
            continue
        if len(rob) >= rob_size:
            stalls["rob_full"] += 1
        for _ in range(width):
            if next_id >= len(trace) or len(rob) >= rob_size:
                break
            entry = dict(trace[next_id])
            ins = entry["instruction"]
            sources=entry.get('sources',[r for r in (ins.rs1,ins.rs2) if r not in (None,reference['zero_register'])])
            deps = {rat[reg] for reg in sources if reg in rat}
            if ins.op == "FENCE":
                deps.update(e["id"] for e in rob if e["instruction"].op in LOADS or e["instruction"].op in STORES)
            entry.update(deps=deps, dispatch=cycle, issue=None, done=None, retire=None)
            destinations=entry.get('destinations',[ins.rd] if ins.rd not in (None,reference['zero_register']) else [])
            for register in destinations:rat[register]=next_id
            rob.append(entry)
            rows.append(entry)
            next_id += 1
            if ins.op in BRANCHES or ins.op == "FENCE":
                branch_barrier = entry["id"]
                break
    if retired_regs != reference["registers"] or retired_mem != reference["memory"]:
        raise AssertionError("提交状态与顺序解释器不一致。")
    return dict(cycles=cycle, instructions=len(trace), ipc=len(trace) / max(1, cycle),
                registers=retired_regs, memory=retired_mem, rows=rows, stalls=stalls,
                initial_memory={a: v & MASK for a,v in (memory or {}).items()},
                listing=reference['listing'],register_names=reference['register_names'],register_bits=reference['register_bits'],
                architecture=architecture,flags=reference.get('flags',{}),zero_register=reference['zero_register'],
                cache=cache.stats(), functional_check=True,issue_order=issue_order,
                assumptions="轨迹驱动、无分支推测、内存操作串行；ALU 1 周期、乘法和缓存延迟由输入指定。")


PROGRAMS = {
    "independent": dict(name="独立运算", source="\n".join(f"ADDI x{i % 30 + 1}, x0, {i}" for i in range(1, 49)) + "\nHALT", memory={}),
    "dependency": dict(name="数据依赖链", source="ADDI x1, x0, 1\n" + "\n".join("ADD x1, x1, x1" for _ in range(24)) + "\nHALT", memory={}),
    "sum": dict(name="数组求和", source="ADDI x1, x0, 0\nADDI x2, x0, 64\nADDI x3, x0, 0\nloop:\nLW x4, 0(x1)\nADD x3, x3, x4\nADDI x1, x1, 4\nBNE x1, x2, loop\nSW x3, 128(x0)\nHALT", memory={i * 4: i + 1 for i in range(16)}),
}


def architectural_state_at(result, cycle):
    """回放已完成模拟的提交轨迹；不是暂停后继续推测执行。"""
    if not isinstance(cycle,int) or not 0<=cycle<=result['cycles']:
        raise ValueError("回放周期超出范围。")
    regs=[0]*len(result['registers'])
    memory=dict(result.get('initial_memory',{}))
    retired=0
    for row in result['rows']:
        if row['retire']>cycle:break
        ins=row['instruction']
        writes=row.get('writes',{ins.rd:row['value']} if ins.rd not in (None,result.get('zero_register',0)) else {})
        for register,value in writes.items():regs[register]=value
        if ins.op in STORES:write_memory(memory,row['address'],row['store_bits'],row['store_value'])
        retired+=1
    return dict(registers=regs,memory=memory,retired=retired)


@lru_cache(maxsize=128)
def profile_ipc(decode, rob, backend, pipeline, l1_kb):
    cycles, instructions = 0, 0
    for program in PROGRAMS.values():
        result = simulate_core(program["source"], memory=program["memory"],
            width=max(1, min(12, decode)), rob_size=max(1, min(1024, rob)),
            execution_ports=max(1, min(12, backend)), pipeline=max(2, min(24, pipeline)),
            cache_kb=max(1, l1_kb))
        cycles += result["cycles"]
        instructions += result["instructions"]
    return instructions / max(1, cycles)
