"""已打包GUI的确定性冒烟，自选临时存档；不是功能覆盖证明。"""
import json
import tempfile
from pathlib import Path


def run(app,win,output):
    from . import export,save
    from .engine.challenges import challenge_design
    from .engine.rtl import rtl_info
    from .ui.brand import LOGO
    if not LOGO.is_file():raise RuntimeError('打包缺少logo资源。')
    rtl_info()
    studio=win.screens['studio']
    for kind in ('cpu','gpu','npu','isp'):
        studio.new_design(kind);studio.verify_current()
        if studio.publish_current() is None:raise RuntimeError('打包核心验证失败：'+kind)
    win.design=challenge_design('challenge_camera',solution=True)
    win.recompute_now(force_layout=True)
    if not win.result['signoff']['ready']:raise RuntimeError('打包SoC重放失败。')
    with tempfile.TemporaryDirectory() as temp:
        file=export.export_to(Path(temp)/'smoke.sil',win.design,win.result)
        loaded,_=export.read_design(file)
        if loaded.scenario_id!=win.design.scenario_id:raise RuntimeError('打包文件导入失败。')
    win.go('studio');win.show();app.processEvents()
    screenshot=Path(output).with_suffix('.png')
    if not win.grab().save(str(screenshot)):raise RuntimeError('打包GUI截图失败。')
    win.persist()
    Path(output).write_text(json.dumps(dict(passed=True,version=app.applicationVersion(),
        platform=__import__('sys').platform,save=str(save.SAVE_PATH),screenshot=screenshot.name),ensure_ascii=False,indent=2),'utf-8')
    win.close()
