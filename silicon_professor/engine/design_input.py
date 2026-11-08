"""交换文件的已知字段检查；资源上限不是真实硬件上限。"""
from __future__ import annotations

from dataclasses import fields


def _object(value, path):
    if not isinstance(value, dict):
        raise ValueError(f'{path} 必须是JSON对象。')
    return value


def _number(record, key, lo, hi, path='design', integer=False):
    if key not in record:
        return
    value = record[key]
    if integer:
        valid_type = type(value) is int
    else:
        valid_type = type(value) in (int, float)
    if not valid_type or not lo <= value <= hi:
        unit = '整数' if integer else '有限数值'
        raise ValueError(f'{path}.{key} 必须是 {lo}..{hi} 范围内的{unit}。')


def _text(record, key, path='design', limit=4096):
    if key in record and (not isinstance(record[key], str) or len(record[key]) > limit):
        raise ValueError(f'{path}.{key} 必须是长度不超过{limit}的字符串。')


def _choice(record, key, choices, path='design'):
    if key in record and (not isinstance(record[key], str) or record[key] not in choices):
        raise ValueError(f'{path}.{key} 无法识别：{record[key]!r}。')


def _bools(record, keys, path='design'):
    for key in keys:
        if key in record and type(record[key]) is not bool:
            raise ValueError(f'{path}.{key} 必须是JSON布尔值。')


def validate_design_record(record):
    """先检查大小/数值/引用，再运行模型；未完成的合法草稿仍能导入。"""
    from ..data.blocks import (COOLING, DRAMS, FIXED_BLOCKS, GPUS, METAL_STACKS,
                              NOCS, NPUS, PACKAGES, STORAGE)
    from ..data.cores import CORES
    from ..data.nodes import NODES
    from ..data.segments import SEGMENTS
    from .types import Design

    d = _object(record, 'design')
    from .core_bundle import validate_templates
    templates=validate_templates(d.get('core_templates',{}))
    gpu_ids=set(GPUS)|{r['catalog_id'] for r in templates.values() if r['kind']=='gpu'}
    npu_ids=set(NPUS)|{r['catalog_id'] for r in templates.values() if r['kind']=='npu'}
    for key, choices in {
        'scenario_id': SEGMENTS, 'node_id': NODES, 'noc': NOCS, 'dram': DRAMS,
        'gpu_id': gpu_ids, 'npu_id': npu_ids, 'storage_id': STORAGE,
        'modem_id': {k for k in FIXED_BLOCKS if k.startswith('modem')},
        'metal_stack': METAL_STACKS, 'package_id': PACKAGES, 'cooling_id': COOLING,
        'pvt_corner': {'tt', 'ss', 'ff'},
    }.items():
        _choice(d, key, choices)
    _text(d, 'name')
    _bools(d, ('l3_shared', 'isp', 'media', 'display', 'chiplet', 'rotated_once'))
    for key in ('bench_tuning', 'bench_isa', 'eco_invest', 'reputation',
                'verification_effort', 'pdn_quality', 'workload_parallel'):
        _number(d, key, 0, 1)
    for key in ('l3_mb', 'slc_mb'):
        _number(d, key, 0, 1024)
    for key, lo, hi in (
        ('ambient_c', -50, 100), ('floorplan_aspect', .2, 5),
        ('routing_overhead', 0, 1), ('price', .01, 1_000_000),
        ('workload_set_mb', .01, 1_000_000), ('workload_intensity', .001, 1_000_000),
    ):
        _number(d, key, lo, hi)
    for key, lo, hi in (('memory_channels', 0, 8), ('memory_gb', 1, 1_000_000),
                        ('gpu_units', 0, 1024), ('seed', 0, 2**64-1)):
        _number(d, key, lo, hi, integer=True)

    assets = _object(d.get('embedded_ips', {}), 'design.embedded_ips')
    if len(assets) > 64:
        raise ValueError('design.embedded_ips 超过64项资源上限。')
    for key, asset in assets.items():
        _object(asset, f'design.embedded_ips[{key}]')
    bindings = _object(d.get('ip_blocks', {}), 'design.ip_blocks')
    for kind, ident in bindings.items():
        if (kind not in ('gpu', 'npu', 'isp') or not isinstance(ident, str)
                or ident not in assets or assets[ident].get('kind') != kind):
            raise ValueError(f'design.ip_blocks.{kind} 缺少匹配类别的内嵌IP。')

    cores = d.get('cores', [])
    if not isinstance(cores, list) or len(cores) > 64:
        raise ValueError('design.cores 必须是最多64项的数组。')
    total = 0
    for index, group in enumerate(cores):
        path = f'design.cores[{index}]'
        g = _object(group, path)
        _text(g, 'core_id', path, 128)
        ident = g.get('core_id')
        if not isinstance(ident, str):
            raise ValueError(f'{path}.core_id 缺失。')
        if ident.startswith('ip:'):
            if ident[3:] not in assets or assets[ident[3:]].get('kind') != 'cpu':
                raise ValueError(f'{path}.core_id 缺少匹配的内嵌CPU IP。')
        elif ident not in CORES and ident != 'custom' and 'cpu:'+ident not in templates:
            raise ValueError(f'{path}.core_id 无法识别：{ident!r}。')
        _number(g, 'count', 0, 256, path, integer=True)
        total += g.get('count', 2)
        if total > 256:
            raise ValueError('design.cores 总核数超过256的资源上限。')
        _number(g, 'l2_mb', 0, 1024, path)
        _number(g, 'clock', 0, 100, path)
        _bools(g, ('l2_shared',), path)
        impl = _object(g.get('impl') if g.get('impl') is not None else {}, path+'.impl')
        _choice(impl, 'lib', {'hd', 'sd', 'hp'}, path+'.impl')
        _choice(impl, 'vt', {'ulvt', 'lvt', 'svt', 'hvt'}, path+'.impl')
        for key in ('density', 'timing'):
            _number(impl, key, 0, 1, path+'.impl')
        _number(impl, 'aspect', .2, 8, path+'.impl')

    placements = _object(d.get('placements') if d.get('placements') is not None else {}, 'design.placements')
    if len(placements) > 1024:
        raise ValueError('design.placements 超过1024项资源上限。')
    for key, value in placements.items():
        path = f'design.placements[{key}]'
        p = _object(value, path)
        for coord in ('x', 'y'):
            _number(p, coord, -10000, 10000, path)
        for size in ('w', 'h'):
            _number(p, size, 0, 10000, path)
        if 'rot' in p and (type(p['rot']) is not int or p['rot'] not in (0, 90, 180, 270)):
            raise ValueError(f'{path}.rot 必须是0/90/180/270。')

    custom = d.get('custom')
    if custom is not None:
        _object(custom, 'design.custom')
        _text(custom, 'name', 'design.custom')
        _choice(custom, 'isa', {'armv8', 'armv9', 'riscv'}, 'design.custom')
        for key, lo, hi in (('decode', 1, 12), ('rob', 1, 1024), ('l1_kb', 1, 256),
                            ('pipeline', 2, 24), ('backend', 1, 12)):
            _number(custom, key, lo, hi, 'design.custom', integer=True)
        if 'extensions' in custom:
            exts = custom['extensions']
            if not isinstance(exts, list) or any(e not in ('M', 'Zbb') for e in exts):
                raise ValueError('design.custom.extensions 无法识别。')

    unknown = sorted(set(d)-{field.name for field in fields(Design)})
    return ['忽略未识别的design字段，本版不参与计算：'+', '.join(unknown)] if unknown else []
