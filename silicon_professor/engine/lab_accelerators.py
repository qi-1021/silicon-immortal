"""可计算加速器实验。精确功能输出与假设资源调度分开，不拟合某厂商芯片。"""
from __future__ import annotations

import math
import random
import struct


def fp32(x):return struct.unpack('<f',struct.pack('<f',x))[0]


def schedule_warps(warps,processors,resident_warps,alu_latency,issue_interval):
    """每处理器单发射、warp内部依赖串行，驻留warp可交错发射。"""
    estimates=[0]*processors
    queues=[[] for _ in range(processors)]
    for warp in warps:
        unit=min(range(processors),key=lambda j:estimates[j])
        estimates[unit]+=warp['instruction_slots']
        warp.update(processor=unit,start=None,finish=None)
        queues[unit].append(warp)
    for queue in queues:
        active=[];cursor=cycle=0
        while cursor<len(queue) or active:
            active=[entry for entry in active if entry['remaining'] or entry['ready']>cycle]
            while cursor<len(queue) and len(active)<resident_warps:
                active.append(dict(warp=queue[cursor],remaining=queue[cursor]['instruction_slots'],ready=cycle))
                cursor+=1
            ready=[entry for entry in active if entry['remaining'] and entry['ready']<=cycle]
            if not ready:
                if active:cycle=min(entry['ready'] for entry in active)
                continue
            entry=min(ready,key=lambda e:(e['ready'],e['warp']['warp']))
            warp=entry['warp']
            if warp['start'] is None:warp['start']=cycle
            entry.update(remaining=entry['remaining']-1,ready=cycle+alu_latency)
            warp['finish']=entry['ready']
            cycle+=issue_interval
    return max((warp['finish'] for warp in warps),default=0)


def gpu_lab(elements=64,warp_size=8,processors=2,task='axpy',pattern='alternating',
            bandwidth_gbs=16.0,frequency_ghz=1.0,resident_warps=1,alu_latency=1,issue_interval=1):
    if any(type(v)!=int for v in (elements,warp_size,processors)) or not 1<=elements<=4096 or warp_size not in (4,8,16,32,64) or not 1<=processors<=64:
        raise ValueError('元素1..4096，warp4/8/16/32/64，处理器1..64。')
    if task not in ('axpy','branch') or pattern not in ('uniform','alternating'):raise ValueError('任务为axpy/branch，模式为uniform/alternating。')
    if any(type(v) is not int for v in (resident_warps,alu_latency,issue_interval)) or not 1<=resident_warps<=32 or not 1<=alu_latency<=32 or not 1<=issue_interval<=16:
        raise ValueError('驻留warp1..32，ALU延迟1..32，发射间隔1..16。')
    if not all(math.isfinite(v) and v>0 for v in (bandwidth_gbs,frequency_ghz)):raise ValueError('带宽和频率为正数。')
    x=[fp32((i%17-8)/8) for i in range(elements)];y=[fp32((i%13)/13) for i in range(elements)]
    predicates=[True if pattern=='uniform' else i%2==0 for i in range(elements)]
    output=[0.0]*elements;warps=[]
    for first in range(0,elements,warp_size):
        end=min(first+warp_size,elements);true=sum(predicates[first:end]);false=end-first-true
        paths=1 if task=='axpy' else int(true>0)+int(false>0)
        for i in range(first,end):
            output[i]=fp32(fp32(2*x[i])+y[i]) if task=='axpy' or predicates[i] else fp32(x[i]*x[i])
        # 一SIMT路径包含一mul和一add；非FMA，两个明确指令槽。
        duration=2 if task=='axpy' else (2 if true else 0)+(1 if false else 0)
        warps.append(dict(warp=len(warps),first_lane=first,active_lanes=end-first,true_lanes=true,false_lanes=false,
                          paths=paths,instruction_slots=duration))
    compute_cycles=schedule_warps(warps,processors,resident_warps,alu_latency,issue_interval)
    reference=[fp32(fp32(2*v)+y[i]) if task=='axpy' or predicates[i] else fp32(v*v) for i,v in enumerate(x)]
    transferred=elements*12 # 两FP32输入与一FP32输出，未模型化缓存复用。
    transfer_cycles=math.ceil(transferred/(bandwidth_gbs/frequency_ghz))
    operations=elements*2 if task=='axpy' else sum(2 if p else 1 for p in predicates)
    return dict(output=output,input_x=x,input_y=y,warps=warps,functional_check=output==reference,
                compute_cycles=compute_cycles,transfer_cycles=transfer_cycles,cycles=compute_cycles+transfer_cycles,
                operations=operations,bytes_transferred=transferred,precision='FP32, round after each mul/add; no fused operation',
                divergence=sum(w['paths']>1 for w in warps),throughput_gops=operations/(compute_cycles+transfer_cycles)*frequency_ghz,
                assumptions='SIMT分歧路径串行；每处理器单向量发射，驻留warp可隐藏指定ALU延迟；传输与计算不重叠，无shader编译、纹理、光栅或真实GPU机器码。')


def npu_lab(m=8,n=8,k=8,rows=4,cols=4,precision_bits=8,accumulator_bits=32,scratchpad_kb=4,
            bandwidth_gbs=16.0,frequency_ghz=1.0,a=None,b=None):
    integers=(m,n,k,rows,cols,precision_bits,accumulator_bits,scratchpad_kb)
    if any(type(v)!=int for v in integers) or not all(1<=v<=64 for v in (m,n,k,rows,cols)):
        raise ValueError('矩阵和阵列维度为1..64整数。')
    if precision_bits not in (8,16) or accumulator_bits not in (16,32,64) or not 1<=scratchpad_kb<=1024:
        raise ValueError('精度INT8/INT16，累加16/32/64位，scratchpad1..1024KiB。')
    if not all(math.isfinite(v) and v>0 for v in (bandwidth_gbs,frequency_ghz)):raise ValueError('带宽和频率为正数。')
    rng=random.Random(71)
    a=[[rng.randint(-8,8) for _ in range(k)] for _ in range(m)] if a is None else a
    b=[[rng.randint(-8,8) for _ in range(n)] for _ in range(k)] if b is None else b
    def shape(matrix,r,c):
        if not isinstance(matrix,list) or len(matrix)!=r or any(not isinstance(row,list) or len(row)!=c for row in matrix):raise ValueError('矩阵形状与M/N/K不一致。')
        if any(type(x)!=int or not -(1<<(precision_bits-1))<=x<(1<<(precision_bits-1)) for row in matrix for x in row):raise ValueError('矩阵元素超出有符号精度范围。')
    shape(a,m,k);shape(b,k,n)
    exact=[[sum(a[i][t]*b[t][j] for t in range(k)) for j in range(n)] for i in range(m)]
    mask=(1<<accumulator_bits)-1;overflow=0;output=[]
    for line in exact:
        out=[]
        for v in line:
            overflow+=int(not -(1<<(accumulator_bits-1))<=v<(1<<(accumulator_bits-1)))
            wrapped=v&mask;out.append(wrapped if wrapped<(1<<(accumulator_bits-1)) else wrapped-(1<<accumulator_bits))
        output.append(out)
    tiles=[];cycles=traffic=0;max_local=0
    for i in range(0,m,rows):
        for j in range(0,n,cols):
            r,c=min(rows,m-i),min(cols,n-j)
            duration=k+r+c-2
            footprint=(r*k+k*c)*(precision_bits//8)+r*c*(accumulator_bits//8)
            max_local=max(max_local,footprint);traffic+=footprint;cycles+=duration
            tiles.append(dict(row=i,col=j,rows=r,cols=c,compute_cycles=duration,scratchpad_bytes=footprint))
    transfer=math.ceil(traffic/(bandwidth_gbs/frequency_ghz));total=cycles+transfer;macs=m*n*k
    # 一个MAC算两次运算。阵列假设每PE每周期一MAC；tiles 不重叠，含填充/排空。
    return dict(output=output,exact=exact,input_a=a,input_b=b,overflow_count=overflow,
                functional_check=all(output[i][j]==exact[i][j] for i in range(m) for j in range(n)),
                tiles=tiles,scratchpad_bytes=max_local,scratchpad_fits=max_local<=scratchpad_kb*1024,
                compute_cycles=cycles,transfer_cycles=transfer,cycles=total,macs=macs,operations=2*macs,
                precision=f'INT{precision_bits}, signed; INT{accumulator_bits} wrap accumulation',
                throughput_gops=2*macs/total*frequency_ghz,bytes_transferred=traffic,
                assumptions='理想二维systolic阵列；每tile加载A/B、保存C且不跨tile复用，计算传输不重叠；无真实NPU算子/稀疏/量化标定。')


def isp_lab(width=8,height=8,black_level=64,gain=1.0,gamma=2.2,output_bits=8,pixels_per_cycle=1,
            bandwidth_gbs=4.0,frequency_ghz=.5,raw=None,stages=None):
    if any(type(v)!=int for v in (width,height,black_level,output_bits,pixels_per_cycle)) or not 4<=width<=64 or not 4<=height<=64:
        raise ValueError('图像4..64像素边长。')
    if not 0<=black_level<4096 or output_bits not in (8,10) or not 1<=pixels_per_cycle<=16:
        raise ValueError('raw12bit，输出8/10bit，吞吐1..16pixel/cycle。')
    if not all(math.isfinite(v) and v>0 for v in (gain,gamma,bandwidth_gbs,frequency_ghz)):raise ValueError('增益、gamma、带宽和时钟需为正。')
    legacy=stages is None
    stages=['black_level','gain','demosaic','gamma'] if legacy else stages
    order=['black_level','gain','demosaic','gamma']
    if not isinstance(stages,list) or stages!=[stage for stage in order if stage in stages]:
        raise ValueError('ISP模块按black_level/gain/demosaic/gamma的顺序选择，无重复或未知模块。')
    if raw is None:raw=[[min(4095,black_level+((x*313+y*217)%3500)) for x in range(width)] for y in range(height)]
    if len(raw)!=height or any(len(row)!=width for row in raw) or any(type(v)!=int or not 0<=v<=4095 for row in raw for v in row):raise ValueError('raw形状或12bit像素无效。')
    # RGGB CFA。missing channel 使用3x3内有效的同色邻居均值；边界缩小邻域而非镜像。
    colors=lambda y,x:0 if y%2==0 and x%2==0 else 2 if y%2 and x%2 else 1
    effective_black=black_level if 'black_level' in stages else 0
    effective_gain=gain if 'gain' in stages else 1
    effective_gamma=gamma if 'gamma' in stages else 1
    corrected=[[min(4095,max(0,v-effective_black)*effective_gain)/4095 for v in row] for row in raw]
    output=[]
    for y in range(height):
        line=[]
        for x in range(width):
            rgb=[]
            for channel in range(3):
                if 'demosaic' not in stages or colors(y,x)==channel:value=corrected[y][x]
                else:
                    samples=[corrected[yy][xx] for yy in range(max(0,y-1),min(height,y+2)) for xx in range(max(0,x-1),min(width,x+2)) if colors(yy,xx)==channel]
                    value=sum(samples)/len(samples) if samples else 0
                rgb.append(round(max(0,min(1,value))**(1/effective_gamma)*((1<<output_bits)-1)))
            line.append(rgb)
        output.append(line)
    functional=all(len(pixel)==3 and all(0<=v<(1<<output_bits) for v in pixel) for line in output for pixel in line)
    traffic=width*height*(2+6) # raw以16bit存，RGB输出每通道16bit容器。
    fill=2*width if 'demosaic' in stages else 0
    latency=3 if legacy else len(stages)+1 # 量化模块必需；每模块一级为显式假设。
    compute=math.ceil(width*height/pixels_per_cycle)+fill+latency
    transfer=math.ceil(traffic/(bandwidth_gbs/frequency_ghz))
    return dict(output=output,input_raw=raw,corrected=corrected,functional_check=functional,
                line_buffer_bytes=2*width*2 if fill else 0,compute_cycles=compute,transfer_cycles=transfer,cycles=compute+transfer,
                stages=stages,color_mode='rgb' if 'demosaic' in stages else 'raw_mono',
                pixels=width*height,bytes_transferred=traffic,clipped=sum(v==4095 for row in raw for v in row),
                assumptions='raw12 RGGB、黑电平、标量增益、局部bilinear插值、幂gamma；无AWB/CCM/噪声去除/镜头校正/HDR，gamma不是sRGB OETF。')
