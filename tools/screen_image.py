"""Bound document screenshots with the existing Qt runtime, without extra packages."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage


def prepare_screen_image(path, max_edge=1280, max_bytes=250_000):
    path = Path(path)
    image = QImage(str(path))
    if image.isNull():
        raise ValueError(f'无法读取截图：{path.name}')
    if max(image.width(), image.height()) <= max_edge and path.stat().st_size <= max_bytes:
        return
    bound = min(max_edge, max(image.width(), image.height()))
    original = image.scaled(bound, bound, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
    temporary = path.with_name(path.name + '.bounded.png')
    try:
        if not original.save(str(temporary), 'PNG'):
            raise OSError('截图编码失败')
        if temporary.stat().st_size > max_bytes:
            for edge in (max_edge, 1024, 800, 640, 512):
                candidate = original.scaled(min(edge, bound), min(edge, bound),
                    Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                candidate = candidate.convertToFormat(QImage.Format.Format_Indexed8)
                if not candidate.save(str(temporary), 'PNG'):
                    raise OSError('截图编码失败')
                if temporary.stat().st_size <= max_bytes:
                    break
            else:
                raise ValueError(f'截图压缩后仍过大：{path.name}')
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()
