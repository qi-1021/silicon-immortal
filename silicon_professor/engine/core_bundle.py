"""SoC内的模板参数快照。摘要用于检出损坏，不是厂商真实性认证。"""
from copy import deepcopy
import hashlib
import json
import math

SCHEMA = 'embedded-cores-v1'
MODEL_SCHEMA = 'catalog-ppa-v1'
COMMON = {'id', 'name', 'note', 'evidence', 'confidence', 'parameter_basis', 'license_cost_m'}
FIELDS = {
    'cpu': COMMON | {'vendor', 'arch', 'isa', 'year', 'tier', 'license', 'ref_node',
                      'ipc', 'fmax_ref', 'logic_area', 'l2_default', 'l2_max', 'power_ref',
                      'leak_frac', 'eng_weeks', 'decode', 'rob', 'eco', 'execution_model','hardware'},
    'gpu': COMMON | {'vendor', 'year', 'ref_node', 'unit_name', 'default_units',
                      'min_units', 'max_units', 'perf_per_unit', 'area_per_unit',
                      'power_per_unit', 'compat', 'cu_per_unit'},
    'npu': COMMON | {'tops', 'area', 'power', 'precision', 'sparsity', 'operations_per_mac'},
    'isp': COMMON | {'area', 'power', 'edge', 'color'},
}
REQUIRED = {
    'cpu': {'id', 'name', 'vendor', 'arch', 'isa', 'year', 'tier', 'license', 'ref_node',
            'ipc', 'fmax_ref', 'logic_area', 'l2_default', 'l2_max', 'power_ref',
            'leak_frac', 'eng_weeks', 'decode', 'rob', 'license_cost_m', 'note'},
    'gpu': {'id', 'name', 'year', 'ref_node', 'unit_name', 'default_units', 'min_units',
            'max_units', 'perf_per_unit', 'area_per_unit', 'power_per_unit', 'license_cost_m'},
    'npu': {'id', 'name', 'tops', 'area', 'power', 'license_cost_m'},
    'isp': {'id', 'name', 'area', 'power', 'edge', 'color', 'license_cost_m'},
}
NUMBERS = {'year', 'ipc', 'fmax_ref', 'logic_area', 'l2_default', 'l2_max', 'power_ref',
           'leak_frac', 'eng_weeks', 'decode', 'rob', 'eco', 'license_cost_m',
           'default_units', 'min_units', 'max_units', 'perf_per_unit', 'area_per_unit',
           'power_per_unit', 'compat', 'cu_per_unit', 'tops', 'area', 'power', 'operations_per_mac'}
INTEGERS = {'year', 'decode', 'rob', 'default_units', 'min_units', 'max_units', 'cu_per_unit', 'operations_per_mac'}
POSITIVE = {'fmax_ref', 'logic_area', 'area_per_unit', 'cu_per_unit', 'decode', 'max_units'}


def _digest(record):
    identity = {k: record[k] for k in ('kind', 'catalog_id', 'name', 'model_schema', 'model', 'reference_node')}
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def validate_templates(records):
    if not isinstance(records, dict) or len(records) > 128:
        raise ValueError('design.core_templates须为最多128项的对象。')
    for key, record in records.items():
        path = f'design.core_templates[{key}]'
        def fail(message): raise ValueError(path+' '+message)
        if not isinstance(record, dict): fail('须为对象。')
        kind = record.get('kind'); ident = record.get('catalog_id'); model = record.get('model')
        if not isinstance(kind,str) or kind not in FIELDS or not isinstance(ident, str) or not ident or len(ident)>128 or key != kind+':'+ident:
            fail('类别或目录ID不匹配。')
        if record.get('model_schema') != MODEL_SCHEMA: fail('本版无法解释此模板模型结构。')
        if not isinstance(model, dict) or REQUIRED[kind]-set(model): fail('缺少完整模型字段。')
        if set(model)-FIELDS[kind]: fail('本版无法解释模板字段：'+', '.join(sorted(set(model)-FIELDS[kind])))
        if model['id'] != ident or record.get('name') != model['name']: fail('名称/ID与模型不一致。')
        for field, value in model.items():
            if field=='hardware':
                if kind!='cpu':fail('只有CPU教学模板支持hardware。')
                from .core_studio import validate_hardware
                validate_hardware('cpu',value)
            elif field in NUMBERS:
                if field == 'license_cost_m' and value is None: continue
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1_000_000:
                    fail(f'model.{field}须为有限非负数值。')
                if field in INTEGERS and type(value) is not int: fail(f'model.{field}须为整数。')
                if field in POSITIVE and value <= 0: fail(f'model.{field}须大于0。')
            elif field == 'edge':
                if type(value) is not bool: fail('model.edge须为布尔值。')
            elif field == 'evidence':
                if not isinstance(value, list) or len(value)>128 or any(not isinstance(v,str) or len(v)>256 for v in value): fail('evidence无效。')
            elif not isinstance(value, str) or not value or len(value)>4096:
                fail(f'model.{field}须为非空字符串。')
        if kind == 'cpu':
            if model['isa'] not in ('armv8', 'armv9', 'riscv', 'x86_32') or model['tier'] not in ('big', 'mid', 'little') or model['license'] not in ('arm', 'riscv', 'research'):
                fail('CPU类别语义未支持。')
            if not 0 <= model['leak_frac'] <= 1 or model['l2_max'] < model['l2_default']: fail('CPU功耗/缓存范围无效。')
        if kind == 'gpu' and not model['min_units'] <= model['default_units'] <= model['max_units'] <= 1024:
            fail('GPU单元范围无效。')
        ref = record.get('reference_node')
        if kind in ('cpu', 'gpu'):
            if not isinstance(ref, dict) or ref.get('id') != model['ref_node']: fail('参考制程定义缺失或不匹配。')
            for field in ('area_scale', 'freq_scale', 'sram_mb'):
                value = ref.get(field)
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 10000:
                    fail(f'reference_node.{field}须为有限正数。')
        elif ref is not None: fail('此模板不使用参考制程对象。')
        if record.get('digest') != _digest(record): fail('内容摘要不匹配；模板被修改或损坏。')
    return deepcopy(records)


def required_templates(record):
    """包括零实例CPU组与未启用ISP，保持其可编辑选择也可携带。"""
    keys = {'cpu:'+g['core_id'] for g in record.get('cores', [])
            if g['core_id'] != 'custom' and not g['core_id'].startswith('ip:')}
    for kind, ident in [('gpu', record.get('gpu_id', 'maliG76')), ('npu', record.get('npu_id', 'npu8')), ('isp', 'isp')]:
        keys.add(kind+':'+ident)
    return keys


def check_complete(record):
    templates = record.get('core_templates', {})
    missing = required_templates(record)-set(templates)
    if missing: raise ValueError('完整核心包缺少模板定义：'+', '.join(sorted(missing)))
    if any(g['core_id']=='custom' for g in record.get('cores',[])):
        from .types import CustomCore
        custom=record.get('custom')
        if not isinstance(custom,dict) or set(CustomCore.__dataclass_fields__)-set(custom):
            raise ValueError('完整核心包缺少design.custom的完整名称或核心参数。')


def materialize(design):
    """仅填补未快照的目录项；不修改活跃设计，不替换已导入快照。"""
    from ..data.cores import CORES
    from ..data.blocks import GPUS, NPUS, FIXED_BLOCKS
    from ..data.nodes import NODES
    from ..version import producer
    record = design.to_dict()
    templates = validate_templates(record.get('core_templates', {}))
    catalogs = {'cpu': CORES, 'gpu': GPUS, 'npu': NPUS, 'isp': FIXED_BLOCKS}
    for key in sorted(required_templates(record)):
        if key in templates: continue
        kind, ident = key.split(':', 1)
        if ident not in catalogs[kind]: raise ValueError('无法导出缺少定义的模板：'+key)
        model = deepcopy(catalogs[kind][ident])
        ref = deepcopy(NODES[model['ref_node']]) if 'ref_node' in model else None
        snapshot = dict(kind=kind, catalog_id=ident, name=model['name'], model_schema=MODEL_SCHEMA,
                        model=model, reference_node=ref, producer=producer())
        snapshot['digest'] = _digest(snapshot)
        templates[key] = snapshot
    record['core_templates'] = validate_templates(templates)
    return record


def template_model(design, kind, ident):
    snapshot = design.core_templates.get(kind+':'+ident)
    if snapshot is None: return None
    model = deepcopy(snapshot['model'])
    if snapshot['reference_node'] is not None: model['_reference_node'] = deepcopy(snapshot['reference_node'])
    return model


def template_catalog(design, kind, catalog):
    """UI目录合并；同ID使用文件名称/参数，删除的目录项仍可编辑。"""
    merged = dict(catalog)
    for record in design.core_templates.values():
        if record['kind'] == kind: merged[record['catalog_id']] = record['model']
    return merged
