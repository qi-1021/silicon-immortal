"""可直接载入LAB的资源实验；每次返回独立可编辑草稿。"""
from .core_designs import default_hardware,default_bench

EXPERIMENTS={'smt':'SMT · 共享与等待','mshr':'MSHR · 重叠缓存未命中','predictor':'方向预测 · 循环训练',
             'gpu':'GPU · 驻留与分歧','npu':'NPU · 阵列填充','isp':'ISP · 行缓冲与阶段'}


def experiment_preset(key):
    if key not in EXPERIMENTS:raise ValueError('未知资源实验。')
    kind=key if key in ('gpu','npu','isp') else 'cpu'
    h=default_hardware(kind);b=default_bench(kind,h)
    if key=='smt':
        h.update(smt_threads=2,width=2,execution_ports=2,alu_ports=1,multiply_ports=1,multiply_latency=8,pipeline=2)
        b.update(source='ADDI x1,x0,1\n'+'MUL x1,x1,x1\n'*20+'HALT',
                 source2='ADDI x1,x0,9\n'+'ADDI x2,x0,7\n'*20+'HALT')
    elif key=='mshr':
        h.update(mshrs=4,pipeline=2)
        b.update(source='LW x1,0(x0)\nLW x2,64(x0)\nLW x3,128(x0)\nLW x4,192(x0)\nHALT',memory='0 1\n64 2\n128 3\n192 4')
    elif key=='predictor':
        h.update(branch_predictor='two_bit',pipeline=12)
        b['source']='ADDI x1,x0,16\nloop:\nADDI x1,x1,-1\nBNE x1,x0,loop\nHALT'
    elif key=='gpu':h.update(alu_latency=8,resident_warps=4);b.update(task='branch',pattern='alternating')
    elif key=='npu':h.update(rows=8,cols=8);b.update(m=9,n=9,k=8)
    elif key=='isp':b.update(width=16,height=8)
    return dict(kind=kind,name=EXPERIMENTS[key],hardware=h,bench=b)
