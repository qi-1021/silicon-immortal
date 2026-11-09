"""历史事件与反事实教学试验分开；商业参数不作为通关门槛。"""
from copy import deepcopy
from .core_designs import number, choice


def flag(key,label,default):return dict(key=key,label=label,default=default)


FIELDS={
    'divider':[
        choice('divider','商选择表','missing_entry',[('missing_entry','原版五个漏项'),('complete','补全SRT表项'),('software','串行软件替代')],'experiment'),
        choice('coverage','验证输入','basic',[('basic','常规样例'),('boundary','常规 + 边界样例')],'experiment')],
    'tlb':[
        choice('policy','并发处理','unchecked',[('unchecked','未修复'),('serialize','保守串行规避'),('revised','硬件修订')],'experiment'),
        flag('stress','并发压力验证',False)],
    'sata':[
        choice('ports','端口策略','all_ports',[('all_ports','原版全部启用'),('disable_3g','隔离3Gb/s端口'),('revised','使用修订版')],'experiment'),
        flag('external','为剩余设备添加外部控制器',False),
        number('external_bandwidth_gbps','外部控制器共享带宽 / Gb/s（教学）',6.0,.5,12.,'experiment')],
    'mobile':[
        number('frequency_ghz','频率 / GHz（教学）',2.8,.5,3.5,'chip'),
        number('voltage','电压 / V（教学）',1.0,.7,1.2,'chip'),
        number('thermal_r','设备等效热阻 / K/W',8.0,1.,20.,'device'),
        number('ambient','环境温度 / C',25.0,10.,40.,'device')],
}


def case(cid,name,year,kind,history,sources,conditions,scope,confidence='medium'):
    return dict(id='rescue_'+cid,name=name,year=year,kind=kind,
        category='移动SoC复盘' if kind=='mobile' else '历史故障',history=history,sources=sources,
        conditions=conditions,scope=scope,confidence=confidence)


_CASES=[
    case('fdiv','Pentium · 除法的漏项',1994,'divider',
         'Pentium的radix-4 SRT商选择表有五个应返回+2却返回0的表项。它们破坏部分余数边界；全覆盖不能建立在“漏项不可达”的错误前提上。',
         ['intel_fdiv1994','pentium_srt'],['Edelman，SIAM Review39(1) §2–4，五个D列=17/20/23/26/29÷16。','实验检查真实SRT边界不变量；不是所有x87指令执行。'],
         '复现SRT商位局部边界，不复刻Pentium完整carry-save选择/舍入或故障概率。性能代价按同精度商位步骤计，不是实测CPU延迟。'),
    case('barcelona','Barcelona · 并发与TLB勘误',2007,'tlb',
         'AMD勘误298：L2中的PTE Accessed/Dirty位更新不原子，旧PTE可进入L3；探测可能导致更新丢失、一致性错误或数据损坏。B2受影响，B3在原厂矩阵未标。',
         ['amd_10h_298'],['AMD41322 Rev3.92，p66勘误298、p31修订矩阵。','BIOS建议HWCR[TlbCacheDis]=1并设MSRC001_1023[1]；多处理器系统要一致处理。'],
         '检查PTE更新/驱逐/探测事件序列与缓存旁路代价，不执行真实MSR/BIOS或全系统一致性。工作负载与周期是教学输入，不是AMD实测性能损失。'),
    case('cougar','Cougar Point · 隔离还是修订',2011,'sata',
         'Intel在2011年1月确认6系列芯片组设计问题，并在2月开始出货硅修订版。任务要求保留四个存储设备，隔离风险端口后要补足连接能力。',
         ['intel_cougar2011'],['官方年报：2011 Annual Report，Note 20。','端口分组为教学任务假设；未校准老化、电路或传输故障。'],
         '不模拟晶体管老化曲线或真实SATA电气层；风险标记、4设备需求与桥接周期是教学假设。'),
    case('810','骁龙810 · 峰值之后',2015,'mobile',
         '以骁龙810时代的持续性能争议为题。资料不足以把某台手机的温度单独归因于SoC；先分清芯片功耗与设备散热，再讨论设计取舍。',
         ['snapdragon810'],['设备定位：HTC One M9；未取得可用于本模型校准的原始测量。','固件、环境温度、负载时长：未核验，不填入实测值。'],
         '使用通用功耗/热RC教学模型；没有810核心、工艺、频率曲线或整机散热标定。',confidence='low'),
    case('888','骁龙888 · 持续负载预算',2021,'mobile',
         '用骁龙888的讨论检验一个问题：短时峰值和设备长期功耗预算能否同时成立？本关不把不同手机、固件与负载下的结果混为芯片故障。',
         ['snapdragon888'],['设备定位：Galaxy S21 Ultra骁龙版本；未取得可用于校准的原始测量。','固件、环境温度、负载时长：未核验；不与Exynos版本混用。'],
         '通用移动功耗实验；不是骁龙888实测，也不把教学70C限制当作该芯片的规格。',confidence='low'),
]

_TENSOR_HISTORY={
    1:'Google将首代Tensor定义为服务Pixel 6/6 Pro的定制SoC，突出计算摄影、AI与安全；官方介绍不是持续性能测量。',
    2:'Pixel 7/7 Pro的官方介绍强调Tensor G2与多个子系统协同；不能仅用传统跑分决定整个设计是否失败。',
    3:'Tensor G3的官方介绍同时列出CPU、GPU、ISP/Imaging DSP和TPU升级，并强调端侧AI目标。',
    4:'Pixel 9系列的官方介绍确认Tensor G4，强调多模态端侧AI；厂商效率表述不能代替持续负载实测。',
    5:'Pixel 10系列的官方介绍确认Tensor G5，强调端侧AI和计算摄影；这里不使用未经独立复测的提升数字。',
    6:'2026年8月12日的Pixel 11官方介绍确认Tensor G6，并说明CPU、TPU和ISP升级；尚不据此作商业成败判定。',
}
for generation in range(1,7):
    history=_TENSOR_HISTORY.get(generation,'此代完整原始资料与整机测量条件仍待补齐。先保留设计复盘位置，不下“失败芯片”的结论。')
    _CASES.append(case(f'tensor_g{generation}',f'Tensor G{generation} · 设计目标与代价',2020+generation,'mobile',history,
        [f'tensor_g{generation}'],
        [f'设备：Pixel {generation+5}系列；官方介绍已确认代际对应。',
         '没有使用整机实测；固件、环境、负载与持续时长未核验。','教学对照统一为25C环境、8K/W等效热阻；不是Pixel参数。'],
        '每代单独保存案例；通用功耗实验不代表该代真实PPA、基带、AI体验或商业成败。',confidence='low'))

RESCUE_CASES={c['id']:c for c in _CASES}

# Do not certify a mobile rescue using the old universal C/V/f exercise.
from .rescue_measurements import MOBILE_CHIPS
for _cid,_chip in MOBILE_CHIPS.items():
    if _cid not in RESCUE_CASES:
        RESCUE_CASES[_cid]=case('8ee6','骁龙8EE6 · 硅与整机策略',2026,'mobile',_chip['problem'],['qcom_8ee6'],[],
            '原厂brief已确认架构；未获得原始故障/能效测试，不能证明芯片修复。',confidence='low')
    _c=RESCUE_CASES[_cid];_c['history']=_chip['problem']+'\n'+_chip['mechanism']
    _c['conditions']=[_chip['device'],_chip['os'],*_chip['missing']]
    _c['scope']='具体芯片/设备测量见档案；没有完整P/V/f与工作负载校准时不提供通用C/V/f通关。'
    _c['sources']=list(dict.fromkeys(_c['sources']+[o['source'] for o in _chip['observations']]))
    if _cid=='rescue_810':_c['sources']=['htc_m9_original']
    elif _cid=='rescue_888':_c['sources']=['qcom_sd888','mi11_original']
    _c['experiment_status']='model_pending'
    _c['performance_contract']=dict(single=.90,multi=.85,gpu=.85,sustained_not_worse=True,
                                    basis='proposed_game_contract_not_vendor_spec')


def default_controls(cid):
    return {f['key']:deepcopy(f['default']) for f in FIELDS[RESCUE_CASES[cid]['kind']]}


def reference_controls(cid):
    p=default_controls(cid);kind=RESCUE_CASES[cid]['kind']
    p.update({'divider':dict(divider='complete',coverage='boundary'),
              'tlb':dict(policy='revised',stress=True),'sata':dict(ports='revised'),
              'mobile':dict(frequency_ghz=2.0,voltage=.8)}[kind])
    return p
