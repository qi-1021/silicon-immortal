"""生成并重放可携带的SoC/IP教学例子，不写入玩家存档。"""
from pathlib import Path
from copy import deepcopy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from silicon_professor.export import export_to, read_design
from silicon_professor.engine.ip_library import make_asset, make_design_asset, write_asset, read_asset, attach_asset
from silicon_professor.data.core_designs import default_hardware
from silicon_professor.engine.core_bundle import materialize
from silicon_professor.engine.labs import DEFAULTS
from silicon_professor.engine.types import empty_design
from silicon_professor.engine.simulate import simulate


def main():
    output = ROOT / 'docs/examples'
    assets = {}
    programs = {
        'rv32': ('riscv32', 'ADDI x1,x0,6\nADDI x2,x0,7\nMUL x3,x1,x2\nSW x3,0(x0)\nLW x4,0(x0)\nHALT'),
        'ia32': ('x86_32', 'MOV EAX,6\nMOV EBX,7\nIMUL EAX,EBX\nMOV [0],EAX\nMOV ECX,[0]\nCMP ECX,42\nHALT'),
        'a64': ('aarch64', 'MOV X0,#6\nMOV X1,#7\nMUL X2,X0,X1\nSTR X2,[X3]\nLDR X4,[X3]\nHALT'),
    }
    for key, (architecture, source) in programs.items():
        config = dict(DEFAULTS['cpu'], architecture=architecture, source=source,
                      extensions=['M'] if architecture=='riscv32' else [])
        assets[key] = make_asset('cpu', 'isqi / '+key, config)
    for kind in ('gpu', 'npu', 'isp'):
        assets[kind] = make_asset(kind, 'isqi / '+kind, deepcopy(DEFAULTS[kind]))
    for kind in ('cpu', 'gpu', 'npu', 'isp'):
        assets['studio-'+kind] = make_design_asset(kind, 'isqi / Studio '+kind.upper(), default_hardware(kind))
    assets['studio-x64']=make_design_asset('cpu','isqi / x86-64',default_hardware('cpu')|dict(architecture='x86_64',enable_m=False,enable_zbb=False))
    for key, asset in assets.items():
        path = write_asset(output / (key+'.cor'), asset)
        restored = read_asset(path)
        if restored['id'] != asset['id'] or not restored['verification']['passed']:
            raise RuntimeError(f'{path.name} 没有通过独立文件导入重放。')

    design = empty_design('sandbox')
    design.name = 'isqi / RV32 compute SoC'
    design.cores = []
    for key in ('rv32', 'rv32', 'gpu', 'npu', 'isp'):
        attach_asset(design, assets[key])
    design.pdn_quality = 1
    design.verification_effort = 1
    result = simulate(design)
    if not result['valid']:
        raise RuntimeError('示例结构错误：'+str(result['errors']))
    path = export_to(output / 'isqi-compute.sil', design, result)
    restored, notes = read_design(path)
    replay = simulate(restored)
    if (restored.to_dict() != materialize(design) or not replay['valid']
            or replay['die_area'] != result['die_area']):
        raise RuntimeError('SoC导入后定义或面积发生变化。')
    for label in ('studio-compute', 'template-soc','x86-workstation'):
        design=empty_design('x86_workstation' if label=='x86-workstation' else 'sandbox');design.name='isqi / '+label
        if label=='studio-compute':
            design.cores=[]
            for kind in ('cpu','cpu','gpu','npu','isp'):attach_asset(design,assets['studio-'+kind])
        design.pdn_quality=1;design.verification_effort=1
        result=simulate(design)
        path=export_to(output/(label+'.sil'),design,result)
        loaded,_=read_design(path);replayed=simulate(loaded)
        if loaded.to_dict()!=materialize(design) or replayed['die_area']!=result['die_area']:
            raise RuntimeError(label+'定义或面积重放不一致。')
    print(f'重放通过：{len(assets)}个.cor和4个.sil；旧资产、新硬件设计、x86工作站与完整模板包。')
    print(f'教学签核：{replay["signoff"]["ready"]}；不代表真实EDA签核。')
    for note in notes:
        print(note)


if __name__ == '__main__':
    main()
