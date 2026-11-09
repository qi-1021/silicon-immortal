"""Specific workload retention gates; higher stability cannot hide lower absolute throughput."""
import math
from ..data.rescue_measurements import MOBILE_CHIPS


def performance_contract(cid):
    chip=MOBILE_CHIPS.get(cid);rules={}
    if not chip:return rules
    for record in chip['observations']:
        test=record['test'];value=record['value']
        if test=='Geekbench CPU':
            for key,ratio in (('single',.90),('multi',.85)):
                rules[key]=dict(baseline=value[key],minimum=value[key]*ratio,unit='GB6 score',kind='throughput',
                    version=record['version'],source=record['source'])
        elif test in ('T-Rex onscreen peak','Wild Life Extreme peak'):
            rules['gpu_peak']=dict(baseline=value,minimum=value*.85,unit='fps',kind='throughput',
                version=record['version'],source=record['source'],workload=test)
        elif test=='T-Rex stressed':
            rules['gpu_sustain']=dict(baseline=value,minimum=value,unit='fps',kind='throughput',
                version=record['version'],source=record['source'],workload=test)
        elif test=='Wild Life Extreme stability':
            rules['gpu_stability']=dict(baseline=value/100,minimum=value/100,unit='ratio',kind='stability',
                version=record['version'],source=record['source'],workload=test)
        elif test=='Wild Life completed loops':
            rules['completed_loops']=dict(baseline=max(value),minimum=20,unit='loops',kind='completion',
                version=record['version'],source=record['source'],workload=test)
    if 'gpu_peak' in rules and 'gpu_stability' in rules and rules['gpu_peak']['source']==rules['gpu_stability']['source']:
        peak=rules['gpu_peak'];stability=rules['gpu_stability'];baseline=peak['baseline']*stability['baseline']
        rules['gpu_sustain']=dict(baseline=baseline,minimum=baseline,unit='fps',kind='throughput',
            version=peak['version'],source=peak['source'],workload='Derived: peak fps × stress minimum/maximum ratio',
            derived=True,assumption='假设单次峰值与压力测试峰值可对应；这不是原文直接给出的最低fps')
    if rules:
        for key in ('single','multi','gpu_peak'):
            if key not in rules:rules[key]=dict(baseline=None,minimum=None,unit='原始记录待补',kind='missing',version=None,source=None)
    return rules


def evaluate_performance(contract,values,benchmark_version=None):
    if not isinstance(contract,dict) or not isinstance(values,dict):raise ValueError('性能验收输入必须是结构化数据。')
    checks=[]
    for key,rule in contract.items():
        value=values.get(key);minimum=rule['minimum']
        valid=type(value) in (int,float) and math.isfinite(value) and value>=0
        version_ok=not (key in ('single','multi') and benchmark_version is not None and rule['version']!=benchmark_version)
        checks.append(dict(id=key,ok=bool(minimum is not None and valid and value>=minimum and version_ok),value=value,
            baseline=rule['baseline'],minimum=minimum,unit=rule['unit'],version=rule['version']))
    return dict(ready=bool(checks) and all(c['ok'] for c in checks),checks=checks,
        scope='验收同工作负载的候选值；不生成预测、不验证数据来源，也不等于实物修复认证。')
