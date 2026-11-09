"""生成当前界面截图；使用临时存档，避免改动玩家进度。"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix="silicon-screens-") as savedir:
        os.environ["SILICON_PROFESSOR_SAVE_DIR"] = savedir
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QCoreApplication, QEvent
        from silicon_professor.ui import anim, theme as T
        from silicon_professor.ui.main_window import MainWindow
        from silicon_professor import export
        app = QApplication([])
        def settle():
            for _ in range(5):
                app.processEvents()
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.setStyle("Fusion")
        app.setFont(T.font(13))
        app.setStyleSheet(T.QSS)
        anim.set_enabled(False)
        out = ROOT / "docs" / "screens"
        out.mkdir(parents=True, exist_ok=True)
        w = MainWindow()
        w.resize(1500, 940)
        w.show()
        settle()
        w.grab().save(str(out / "start.png"))
        w.start_scenario("xring2025")
        w.design.name = "SI / 01"
        w.design.pdn_quality = 1.0
        w.recompute_now()
        for page in ("architecture", "physical", "floorplan", "package", "engineering", "signoff", "report", "tutorial", "codex", "sources"):
            w.go(page)
            settle()
            w.grab().save(str(out / f"{page}.png"))
        w.tape_out()
        w.go("showcase")
        settle()
        s = w.screens["showcase"]
        s._render_hero()
        for mode, filename in (("silicon", "showcase"), ("wafer", "wafer"), ("layout", "showcase_layout")):
            s.views.select(mode)
            settle()
            w.grab().save(str(out / f"{filename}.png"))
        for mode in ("silicon", "wafer", "layout"):
            export.export_dieshot_png(out / f"sample_{mode}.png", w.design, w.result, mode=mode)
            if mode in ("silicon","wafer"):
                from PySide6.QtGui import QImage
                image=out/f"sample_{mode}.png"
                if not QImage(str(image)).save(str(image.with_suffix(".jpg")),"JPEG",94 if mode=="silicon" else 85):raise RuntimeError("文档图片转换失败。")
                image.unlink()
        w.go('labs')
        labs=w.screens['labs'];labs.run();settle()
        w.grab().save(str(out/'labs.png'))
        labs.select_course('l06');settle()
        w.grab().save(str(out/'lab_course.png'))
        labs._load_solution();labs.run();settle()
        w.grab().save(str(out/'lab_zbb.png'))
        labs.course_id=None
        labs.controls['architecture'].setCurrentIndex(labs.controls['architecture'].findData('x86_32'))
        labs.run();settle();w.grab().save(str(out/'lab_x86.png'))
        labs.controls['architecture'].setCurrentIndex(labs.controls['architecture'].findData('aarch64'))
        labs.run();settle();w.grab().save(str(out/'lab_a64.png'))
        labs.asset_name.setText('isqi A64 / 01');labs._save_ip()
        labs.tabs.setCurrentWidget(labs.library_page);settle();w.grab().save(str(out/'ip_library.png'))
        for kind in ('gpu','npu','isp'):
            labs.kind_picker.setCurrentIndex(labs.kind_picker.findData(kind));labs.run();settle()
            w.grab().save(str(out/f'lab_{kind}.png'))
        w.mode_picker.setCurrentIndex(w.mode_picker.findData('professional'))
        labs.kind_picker.setCurrentIndex(labs.kind_picker.findData('cpu'))
        labs.run();settle();w.grab().save(str(out/'labs_professional.png'))
        w.go('studio');studio=w.screens['studio']
        studio.name_edit.setText('isqi / Scalar 01');settle()
        w.grab().save(str(out/'studio_cpu.png'))
        studio.verify_current();studio.publish_current();settle()
        w.grab().save(str(out/'studio_validation.png'))
        studio.run_performance();settle();w.grab().save(str(out/'studio_performance.png'))
        w.start_scenario('x86_workstation');w.go('architecture');settle();w.grab().save(str(out/'x86_workstation.png'))
        architecture=w.screens['architecture'];menu=architecture._make_add_menu('x86')
        menu.show();settle();menu.grab().save(str(out/'core_menu.png'));menu.close()
        architecture._show_core_info(0);architecture._edit_template();settle()
        w.grab().save(str(out/'studio_x86.png'));studio.run_performance();settle()
        w.grab().save(str(out/'studio_x86_performance.png'))
        w.start_scenario('sandbox');settle();w.grab().save(str(out/'free_sandbox.png'))
        w.go('architecture');settle();w.grab().save(str(out/'sandbox_architecture.png'))
        w.go('engineering');w.screens['engineering'].pdn_resistance.setValue(25);w.recompute_now();settle()
        w.grab().save(str(out/'pdn_parameters.png'))
        w.go('signoff');settle();w.grab().save(str(out/'sandbox_diagnostics.png'))
        w.go('package');settle();w.grab().save(str(out/'device_thermal_scene.png'))
        w.go('studio')
        for kind in ('gpu','npu','isp'):
            studio.new_design(kind);studio.name_edit.setText('isqi / '+kind.upper()+' 01');settle()
            w.grab().save(str(out/f'studio_{kind}.png'))
            studio.verify_current();studio.publish_current();studio.run_bench();settle()
            w.grab().save(str(out/f'studio_{kind}_output.png'))
        studio.tabs.setCurrentWidget(studio.library_page);settle();w.grab().save(str(out/'studio_library.png'))
        for sid,label in [('challenge_bandwidth','challenge_bandwidth'),('challenge_camera','challenge_camera')]:
            w.start_scenario(sid);settle();w.grab().save(str(out/(label+'_brief.png')))
            w.screens['brief']._load_solution();w.go('engineering');settle();w.grab().save(str(out/(label+'_solved.png')))
        w.go('start');settle()
        start=w.screens['start'];start.findChild(__import__('PySide6.QtWidgets',fromlist=['QScrollArea']).QScrollArea).verticalScrollBar().setValue(1000)
        settle();w.grab().save(str(out/'challenges.png'))
        w.resize(1180, 760)
        s.views.select("silicon")
        for page in ("start", "architecture", "engineering", "showcase", "labs", "studio"):
            w.go(page)
            settle()
            w.grab().save(str(out / f"{page}_compact.png"))
        w.close()
        from tools.screen_image import prepare_screen_image
        for png in sorted(out.glob("*.png")):
            prepare_screen_image(png)
        print(f"Screenshots: {out}")


if __name__ == "__main__":
    main()
