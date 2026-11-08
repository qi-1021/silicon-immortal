"""核心设计参数：硬件定义与测试台字段分别存放。"""
from copy import deepcopy
from .architectures import ISA_OPTIONS

KINDS={'cpu':'CPU 核心','gpu':'GPU 计算核心','npu':'NPU 阵列','isp':'ISP 流水线'}


def number(key,label,default,lo,hi,group,level=0,hint=''):
    return dict(key=key,label=label,default=default,min=lo,max=hi,group=group,level=level,hint=hint)


def choice(key,label,default,options,group,level=0,hint=''):
    return dict(key=key,label=label,default=default,options=options,group=group,level=level,hint=hint)


def switch(key,label,default,group,level=0,hint=''):
    return dict(key=key,label=label,default=default,group=group,level=level,hint=hint)


FIELDS={
    'cpu':[
        choice('architecture','指令家族','riscv32',ISA_OPTIONS,'contract',hint='RV32是32位RISC-V；IA-32是32位x86；AMD64/Intel64是64位x86；AArch64是64位Arm。都是明确整数子集，无OS/SIMD。'),
        switch('enable_m','实现 M 乘除',True,'contract',hint='仅RV32的可选扩展；x86/A64乘法属于当前原生子集。'),
        switch('enable_zbb','实现 Zbb 位操作',False,'contract',1),
        choice('issue_order','发射次序','out_of_order',[('in_order','顺序发射'),('out_of_order','乱序发射')],'scheduler',hint='两种均顺序提交且无分支推测；乱序使用动态依赖标签。'),
        number('width','取指/分派/提交宽度',2,1,12,'frontend',hint='三处采用同一宽度，不宣称独立前端设计。'),
        number('pipeline','前端填充周期',8,2,24,'frontend',1),
        number('rob_size','在途队列容量',32,1,1024,'scheduler',1,hint='乱序时作为ROB，顺序时为提交队列；物理寄存器未有限建模。'),
        number('execution_ports','总发射宽度',2,1,12,'scheduler'),
        number('alu_ports','整数 ALU 数量',2,1,12,'alu'),
        number('multiply_ports','流水乘除资源数',1,1,12,'multiply',1),
        number('multiply_latency','乘除结果延迟',3,1,100,'multiply',1,hint='当前全部M指令共享延迟、资源可流水发射；不是实际除法器。'),
        number('cache_kb','L1 数据容量 / KiB',16,1,256,'cache'),
        choice('cache_ways','组相联路数',4,[(i,f'{i} 路') for i in (1,2,4,8)],'cache',1),
        choice('cache_line_bytes','缓存行 / B',64,[(i,f'{i} B') for i in (16,32,64,128)],'cache',1),
        number('hit_latency','命中延迟 / cycle',2,1,1000,'cache',1),
        number('miss_latency','未命中总延迟 / cycle',40,1,1000,'cache',1),
    ],
    'gpu':[
        number('processors','SIMT 处理器数量',2,1,64,'processors'),
        choice('warp_size','SIMT 宽度 / lane',8,[(i,f'{i} lane') for i in (4,8,16,32,64)],'processors'),
        number('resident_warps','每处理器驻留 warp',4,1,32,'scheduler',hint='独立warp交错发射可隐藏ALU延迟；不含完整寄存器分配。'),
        number('alu_latency','FP32 ALU 延迟',4,1,32,'alu',1),
        number('issue_interval','向量发射间隔',1,1,16,'scheduler',1),
        number('frequency_ghz','目标时钟 / GHz',1.,.1,5.,'interface'),
        number('bandwidth_gbs','外部带宽 / GB/s',16.,.1,1024.,'interface',1),
    ],
    'npu':[
        number('rows','阵列行数',4,1,64,'array'),
        number('cols','阵列列数',4,1,64,'array'),
        choice('precision_bits','乘法器整数精度',8,[(8,'INT8'),(16,'INT16')],'array'),
        choice('accumulator_bits','累加器位宽',32,[(i,f'INT{i}') for i in (16,32,64)],'accumulator'),
        number('scratchpad_kb','本地 scratchpad / KiB',4,1,1024,'scratchpad'),
        number('frequency_ghz','目标时钟 / GHz',1.,.1,5.,'interface'),
        number('bandwidth_gbs','外部带宽 / GB/s',16.,.1,1024.,'interface',1),
    ],
    'isp':[
        switch('black_level_enabled','黑电平模块',True,'black_level'),
        switch('gain_enabled','标量增益模块',True,'gain'),
        switch('demosaic_enabled','双线性去马赛克',True,'demosaic',hint='关闭时输出raw灰度预览，不伪装成正确RGB。'),
        switch('gamma_enabled','幂 gamma 模块',True,'gamma',hint='不是完整sRGB OETF。校准值由测试台提供。'),
        choice('output_bits','必要输出量化位宽',8,[(8,'8 bit'),(10,'10 bit')],'quantize'),
        number('pixels_per_cycle','像素并行度',1,1,16,'interface'),
        number('max_width','支持行宽 / pixel',64,4,4096,'line_buffer',1,hint='仅定义容量；运行图像暂限64×64，数据缓存按该行宽分配。'),
        number('frequency_ghz','目标时钟 / GHz',.5,.1,5.,'interface'),
        number('bandwidth_gbs','外部带宽 / GB/s',4.,.1,1024.,'interface',1),
    ],
}

BENCH_FIELDS={
    'cpu':[dict(key='source',label='测试汇编',text=True),dict(key='memory',label='初始内存：字节地址 32bit值',text=True)],
    'gpu':[number('elements','输入元素数',128,1,4096,'bench'),
           choice('task','测试内核','axpy',[('axpy','AXPY / FP32'),('branch','条件分支')],'bench'),
           choice('pattern','分支输入','alternating',[('uniform','全部为真'),('alternating','交替真假')],'bench')],
    'npu':[number('m','M / 输出行数',8,1,64,'bench'),number('n','N / 输出列数',8,1,64,'bench'),number('k','K / 点积长度',8,1,64,'bench')],
    'isp':[number('width','测试帧宽',8,4,64,'bench'),number('height','测试帧高',8,4,64,'bench'),
           number('black_level','黑电平校准值',64,0,4095,'bench'),number('gain','增益校准值',1.,.1,8.,'bench'),
           number('gamma','gamma校准值',2.2,.1,4.,'bench')],
}


def default_hardware(kind):
    return {field['key']:deepcopy(field['default']) for field in FIELDS[kind]}


def default_bench(kind,hardware):
    if kind=='cpu':
        programs={'riscv32':'ADDI x1,x0,6\nADDI x2,x0,7\nADD x3,x1,x2\nSW x3,0(x0)\nLW x4,0(x0)\nHALT',
                  'x86_32':'MOV EAX,6\nMOV EBX,7\nADD EAX,EBX\nMOV [0],EAX\nMOV ECX,[0]\nHALT',
                  'x86_64':'MOV RAX,6\nMOV RBX,7\nADD RAX,RBX\nMOV R8,256\nMOV [R8],RAX\nMOV RCX,[R8]\nHALT',
                  'aarch64':'MOV X0,#6\nMOV X1,#7\nADD X2,X0,X1\nSTR X2,[X3]\nLDR X4,[X3]\nHALT'}
        return dict(source=programs[hardware['architecture']],memory='')
    return {field['key']:deepcopy(field['default']) for field in BENCH_FIELDS[kind]}
