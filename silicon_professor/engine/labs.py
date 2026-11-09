"""实验输入与结果统一接口；任何文本均解析为数据，不执行 Python。"""
from __future__ import annotations

from .isa import assemble, encode
from .lab_cpu import simulate_core
from .lab_memory import run_cache_trace
from .lab_system import logic_lab, power_lab, simulate_network, timing_lab
from .lab_accelerators import gpu_lab,npu_lab,isp_lab

KINDS = {"cpu": "核心与指令", "gpu":"GPU / SIMT", "npu":"NPU / 矩阵阵列", "isp":"ISP / 图像流水线", "cache": "缓存", "network": "互连", "timing": "时序", "power": "功耗与热", "logic": "数字逻辑"}
DEFAULTS = {
    "cpu": dict(source="ADDI x1,x0,42\nADDI x2,x0,1\nADD x3,x1,x2\nHALT", memory="",architecture='riscv32',
                width=2, rob_size=32, execution_ports=2, pipeline=8, cache_kb=16,
                hit_latency=2, miss_latency=40, multiply_latency=3, extensions=["M"]),
    'gpu':dict(elements=64,warp_size=8,processors=2,task='axpy',pattern='alternating',bandwidth_gbs=16.0,frequency_ghz=1.0),
    'npu':dict(m=8,n=8,k=8,rows=4,cols=4,precision_bits=8,accumulator_bits=32,scratchpad_kb=4,bandwidth_gbs=16.0,frequency_ghz=1.0),
    'isp':dict(width=8,height=8,black_level=64,gain=1.0,gamma=2.2,output_bits=8,pixels_per_cycle=1,bandwidth_gbs=4.0,frequency_ghz=.5),
    "cache": dict(addresses="0 4 8 64 0 64", capacity_kb=1, line_bytes=64, ways=4,
                  policy="lru", hit_latency=2, miss_latency=40),
    "network": dict(packets="0 15 0\n1 15 0\n2 15 0\n3 15 0", count=16, topology="mesh", link_latency=1),
    "timing": dict(delays="300 450", clock_ghz=2.0, setup_ps=40.0, skew_ps=20.0),
    "power": dict(capacitance_pf=1000.0, activity=.2, voltage=.9, frequency_ghz=2.0,
                  leakage_w=.2, thermal_r=5.0, thermal_c=2.0, ambient=25.0, duration=60.0),
    "logic": dict(op="add", a=127, b=1, bits=8),
}


def integers(text):
    if len(str(text)) > 100000:
        raise ValueError("输入文本太长。")
    return [int(x, 0) for x in str(text).replace(",", " ").split()]


def run_experiment(kind, inputs):
    if kind not in KINDS: raise ValueError("未知实验类型。")
    p = dict(DEFAULTS[kind], **inputs)
    if kind == "cpu":
        if len(p["source"]) > 100000 or len(p["memory"]) > 100000:
            raise ValueError("程序或初始内存文本过长。")
        memory = {}
        for line in p.pop("memory").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line: continue
            pair = integers(line)
            if len(pair) != 2: raise ValueError("初始内存每行：对齐地址 32位整数值。")
            if pair[0] in memory: raise ValueError("初始内存地址重复。")
            memory[pair[0]] = pair[1]
        source2=p.pop('source2','')
        if source2:
            from .cpu_features import run_cpu_pair
            result=run_cpu_pair(p.pop('source'),source2,memory=memory,**p)
        else:result = simulate_core(memory=memory, **p)
        result["used_ops"] = sorted({entry['op'] for thread in result.get('threads',[result]) for entry in thread['listing']})
    elif kind=='gpu':result=gpu_lab(**p)
    elif kind=='npu':result=npu_lab(**p)
    elif kind=='isp':result=isp_lab(**p)
    elif kind == "cache":
        addresses = integers(p.pop("addresses"))
        capacity = int(p.pop("capacity_kb")) * 1024
        result = run_cache_trace(addresses, capacity_bytes=capacity, **p)
    elif kind == "network":
        if len(p["packets"]) > 100000: raise ValueError("包列表过长。")
        packets = []
        for line in p.pop("packets").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line: continue
            values = integers(line)
            if len(values) != 3: raise ValueError("每行：源端点 目标端点 注入周期。")
            packets.append(tuple(values))
        result = simulate_network(packets, **p)
    elif kind == "timing":
        text = str(p.pop("delays"))
        if len(text) > 10000: raise ValueError("时序级列表过长。")
        delays = [float(v) for v in text.replace(",", " ").split()]
        result = timing_lab(delays, **p)
    elif kind == "power": result = power_lab(**p)
    else: result = logic_lab(**p)
    return dict(result, kind=kind)


def json_result(result):
    """不输出 Python instruction/set 对象；导出完整动态时序与参数。"""
    out = dict(result)
    if result["kind"] == "cpu":
        out["rows"] = [dict(row, instruction=row["instruction"].text, deps=sorted(row["deps"])) for row in result["rows"]]
        if 'solo' in result:out['solo']=[json_result(dict(r,kind='cpu')) for r in result['solo']]
    return out
