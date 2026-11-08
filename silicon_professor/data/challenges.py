"""虚构设计委托；指标是游戏验收值，来源只支持相应工程概念。"""

def rule(metric,op,target,title):return dict(metric=metric,op=op,target=target,title=title)

def case(key,name,base,category,brief,steps,sources,rules):
    return dict(id='challenge_'+key,name=name,base=base,category=category,brief=brief,
                steps=steps,sources=sources,rules=rules,parameter_basis='game_assumption')

_CASES=[
case('bin','01 · 不赌频率档位','xring2025','工程挑战',
     '客户要能量产的频率档位。研发样机很快，但慢角落余量和可出售比例不足；在SS情景下保住档位，同时降低峰值负担。',
     ['工程验证切换SS，查看相对频率余量。','降低大核目标时钟；观察bin可用率和成本变化。','提高PDN投入，按签核与关卡检查同时验收。'],['sankaranarayanan2005'],
     [rule('corner','eq','ss','选择SS角落'),rule('bin','ge',.80,'频率档位可用率≥80%'),rule('peak','le',12,'峰值≤12W')]),
case('thermal','02 · 把热预算还给机身','flagship2022','产品挑战',
     '一部无风扇手机在30°C环境运行长任务。初始设计能跑峰值，却无法保持速度；目标是保住单核能力和持续比例，不能换上笔记本风扇。',
     ['固定环境温度30°C，观察持续多核/峰值比例。','减少大核或GPU规模，降低时钟而非只堆散热。','在手机可用散热器中比较，检查机身温度与签核。'],['sankaranarayanan2005','sankaranarayanan2005'],
     [rule('sustain','ge',.70,'持续/峰值多核≥70%'),rule('st','ge',1000,'单核模型分≥1000'),rule('ambient','eq',30,'环境温度固定30°C')]),
case('bandwidth','03 · 内存墙前的编译农场','laptop2025','工程挑战',
     '任务并行度99%，算术强度仅0.1抽象op/byte。CPU在等待数据：先改善内存通道，别把更大的核数误当成有效吞吐。',
     ['保持并行度99%与强度0.1，检查Roofline内存上限。','增加x16通道，观察有效GB/s与可达吞吐。','比较通道成本和PHY面积，达到吞吐后停止堆核。'],['roofline2008','amdahl1967'],
     [rule('achievable','ge',8,'工作负载可达吞吐≥8模型Gop/s'),rule('intensity','eq',.1,'强度保持0.1'),rule('parallel','eq',.99,'并行比例保持99%')]),
case('serial','04 · 串行代码的逆袭','laptop2025','工程挑战',
     '20%代码可并行。十二核版本增加面积，交互响应仍由串行路径决定；交付不超过四颗应用核的方案。',
     ['保持并行比例20%，看Amdahl上限。','用较少快核替代大量中小核，比较单核与成本。','保持可达吞吐≥3，核数≤4并完成签核。'],['amdahl1967'],
     [rule('core_count','le',4,'应用核总数≤4'),rule('achievable','ge',3,'可达吞吐≥3模型Gop/s'),rule('parallel','eq',.2,'并行比例保持20%')]),
case('open','05 · 开放指令集的迁移账单','laptop2025','产品挑战',
     '产品转向RISC-V应用核心。硬件换核只是第一步，软件适配也要预算；禁止混入Arm应用核掩盖迁移问题。',
     ['清空应用CPU组，选择RISC-V模板。','给应用和驱动适配明确投入，观察NRE。','检查应用核ISA统一，比较持续吞吐与封装成本。'],['riscv_isa','sifive_p670'],
     [rule('all_riscv','eq',True,'全部应用CPU采用RISC-V'),rule('eco','ge',.7,'生态适配投入≥70%'),rule('core_count','ge',2,'至少2颗应用核')]),
case('lab_cpu','06 · 自己的顺序核心','sandbox','核心挑战',
     '为可解释控制任务设计一个RV32顺序核。必须发布你的硬件定义并在SoC里实际使用；模板核无法满足这项交付。',
     ['LAB新建CPU，选择RV32与顺序发射，命名。','运行固定验证，发布到IP库。','替换原应用集群加入SoC，完成PDN/验证投入并导出.sil。'],['riscv_isa','riscv_m'],
     [rule('custom_cpu','ge',1,'至少1颗定制CPU实例'),rule('cpu_in_order','eq',True,'使用定制RV32顺序核心'),rule('verification','ge',.9,'验证规划≥90%')]),
case('camera','07 · 相机里的两种算力','sandbox','核心挑战',
     '成像流水线与稠密整数识别阵列共同交付。ISP负责RAW处理，NPU负责MAC，不能用AI综合分代替硬件定义。',
     ['LAB设计启用双线性去马赛克的ISP，运行常量帧和渐变。','设计8×8或更大INT8 NPU，给足scratchpad，验证GEMM。','发布两类IP并绑定SoC，检查导出.sil包含二者。'],['demosaic2011','tpu2017'],
     [rule('custom_isp','eq',True,'绑定定制ISP'),rule('custom_npu','eq',True,'绑定定制NPU'),rule('npu_peak','ge',.128,'NPU稠密整数峰值≥0.128TOPS'),rule('isp_demosaic','eq',True,'ISP包含双线性去马赛克')]),
case('simt','08 · 用驻留隐藏等待','sandbox','核心挑战',
     '两颗8-lane SIMT处理器的FP32单元延迟8周期。你不能增加处理器或缩短ALU延迟，要通过驻留与交错发射缩短128元素AXPY计算。',
     ['LAB GPU固定2处理器、8-lane、ALU延迟8。','比较驻留1/4个warp的计算周期与传输周期。','保持资源限制，发布并用于SoC；固定任务计算≤40周期。'],['cuda_simt'],
     [rule('custom_gpu','eq',True,'绑定定制GPU'),rule('gpu_fixed_resources','eq',True,'固定2处理器/8-lane/8周期延迟'),rule('gpu_cycles','le',40,'128元素AXPY计算≤40周期')]),
case('compact','09 · 给封装留一毫米','xring2025','产品挑战',
     '客户缩小封装占地，die预算75mm²。用有限核数、缓存和GPU规模保住基本能力；空白布局和昂贵频率档位都要付钱。',
     ['查看逻辑块和SRAM面积，减少不必要缓存与核数。','重新自动布局，检查封装尺寸和拥塞。','满足面积和能力门槛后检查单颗成本。'],['cacti7'],
     [rule('die','le',75,'Die面积≤75mm²'),rule('st','ge',1400,'单核模型分≥1400'),rule('gpu','ge',500,'GPU模型分≥500')]),
case('chiplet','10 · 两颗Die的一张账单','laptop2025','工程挑战',
     '把加速器与CPU拆成两颗同节点教学chiplet。交付2.5D封装，分别计裸die成本；不能把逻辑总图当实际多die布线。',
     ['封装页选择本作2.5D方案，再开启Chiplet。','检查两颗裸die成本与额外组装费用。','持续比例≥80%，保住供电裕量；展示页读清逻辑总图标记。'],['borkar2011'],
     [rule('chiplet','eq',True,'启用Chiplet'),rule('package','eq','imc25d','使用2.5D封装'),rule('sustain','ge',.8,'持续/峰值多核≥80%')]),
case('supply','11 · 先进节点没有产能','xring2025','产品挑战',
     '虚构供应情景：本单只允许N4P。相同产品目标要在较大面积和更高功耗下重做；不能用未来节点绕过约束。',
     ['切回N4P，重新检查面积和参考频率缩放。','降低核规模或缓存，避免超过功耗与面积预算。','保证基本单核能力，完成档位/成本签核。'],['cacti7','sankaranarayanan2005'],
     [rule('node','eq','n4p','只使用N4P'),rule('die','le',140,'Die面积≤140mm²'),rule('st','ge',1400,'单核模型分≥1400')]),
case('margin','12 · 售价不替你省成本','mid2019','产品挑战',
     '单颗售价锁定38美元。毛利至少35%，功耗不能靠跑分作弊掩盖；在成熟节点上做一颗能量产的低成本芯片。',
     ['保持售价38，读取裸die/封装/测试的分项成本。','限制缓存、GPU与高频档位，比较成本与基础性能。','取消跑分特化，检查35%毛利和单核能力。'],['murphy1964'],
     [rule('margin','ge',.35,'芯片毛利率≥35%'),rule('price','eq',38,'售价保持38美元'),rule('st','ge',550,'单核模型分≥550'),rule('no_tuning','eq',True,'不启用跑分特化')]),
]
CHALLENGES={c['id']:c for c in _CASES}


def challenge_segments(existing):
    from copy import deepcopy
    out={}
    for sid,c in CHALLENGES.items():
        seg=deepcopy(existing[c['base']]);seg.update(id=sid,name=c['name'],year=2026,
            tagline=c['brief'].split('。')[0]+'。',brief=c['brief'],tutorial=' → '.join(c['steps']),
            budget_m=300,base_units_m=2,challenge=True,category=c['category'],
            allowed_licenses=['arm','riscv','research','custom'],evidence=c['sources'],confidence='game_assumption')
        # 明确的虚构委托预算，非真实产品实测。
        seg['limits'].update(max_cost=200,max_die_area=240,max_tdp=35,max_die_w=20,max_die_h=20)
        if sid in ('challenge_bin','challenge_compact','challenge_supply'):seg['allowed_nodes']=['n3e','n3p','n4p']
        if c['base']=='sandbox':seg['board']='laptop';seg['limits']['skin_temp']=65
        if sid=='challenge_supply':seg['allowed_nodes']=['n4p']
        out[sid]=seg
    return out
