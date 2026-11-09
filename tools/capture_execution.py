"""用临时存档拍摄执行观测台；输出严格限长、限体积。"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from tools.screen_image import prepare_screen_image
    from PySide6.QtWidgets import QApplication
    from silicon_professor.ui import anim,theme as T
    out=ROOT/'docs/screens';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sp-execution-') as td:
        os.environ['SILICON_PROFESSOR_SAVE_DIR']=td
        from silicon_professor.ui.main_window import MainWindow
        app=QApplication([]);app.setStyle('Fusion');app.setFont(T.font(13));app.setStyleSheet(T.QSS)
        anim.set_enabled(False);w=MainWindow();w.resize(1280,860);w.show();w.go('studio');s=w.screens['studio']
        for kind in ('cpu','gpu','npu','isp'):
            s.new_design(kind)
            if kind=='cpu':
                s.controls['smt_threads'].setCurrentIndex(s.controls['smt_threads'].findData(2))
                s.bench_controls['source'].setPlainText('ADDI x1,x0,1\n'+'MUL x1,x1,x1\n'*20+'HALT')
                s.bench_controls['source2'].setPlainText('ADDI x1,x0,9\n'+'ADDI x2,x0,7\n'*20+'HALT')
            if kind=='gpu':s.controls['alu_latency'].setValue(8)
            s.run_bench();s.tabs.setCurrentWidget(s.observer)
            o=s.observer;o.cycle.setValue(min(s.last_result['cycles']-1,12 if kind=='cpu' else 5 if kind in ('gpu','npu') else 25))
            for _ in range(4):app.processEvents()
            path=out/f'execution_{kind}.png';w.grab().save(str(path))
            prepare_screen_image(path)
            if path.stat().st_size>250_000:raise RuntimeError(f'截图过大：{path.name}')
            print(f'{path.name}: {path.stat().st_size} bytes')
        w.go('rescue');rescue=w.screens['rescue']
        for cid in ('rescue_fdiv','rescue_888'):
            rescue.select_case(cid);rescue.load_reference()
            for _ in range(4):app.processEvents()
            path=out/(cid+'.png');w.grab().save(str(path))
            prepare_screen_image(path)
            if path.stat().st_size>250_000:raise RuntimeError(f'截图过大：{path.name}')
            print(f'{path.name}: {path.stat().st_size} bytes')
        w.go('updates')
        for _ in range(4):app.processEvents()
        path=out/'software_updates.png';w.grab().save(str(path))
        prepare_screen_image(path)
        if path.stat().st_size>250_000:raise RuntimeError('更新页截图过大')
        print(f'{path.name}: {path.stat().st_size} bytes')
        w.go('codex')
        for cid in ('a20pro','tensorG4'):
            w.screens['codex'].select_id(cid)
            for _ in range(4):app.processEvents()
            path=out/f'catalog_{cid}.png';w.grab().save(str(path))
            prepare_screen_image(path)
            if path.stat().st_size>250_000:raise RuntimeError('图鉴截图过大')
            print(f'{path.name}: {path.stat().st_size} bytes')
        w.go('updates')
        w.resize(1180,760)
        for _ in range(4):app.processEvents()
        path=out/'software_updates_compact.png';w.grab().save(str(path))
        prepare_screen_image(path)
        if path.stat().st_size>250_000:raise RuntimeError('紧凑更新页截图过大')
        print(f'{path.name}: {path.stat().st_size} bytes; window {w.width()}x{w.height()}')
        w.close()


if __name__=='__main__':main()
