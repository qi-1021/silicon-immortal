import random
import tempfile
import unittest
from pathlib import Path

from PySide6.QtGui import QImage
from tools.screen_image import prepare_screen_image


class ScreenImageTests(unittest.TestCase):
    def test_portrait_and_large_image_fit_both_limits(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'portrait.png'
            width, height = 360, 1720
            data = random.Random(7).randbytes(width * height * 3)
            image = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            self.assertTrue(image.save(str(path)))
            prepare_screen_image(path)
            actual = QImage(str(path))
            self.assertLessEqual(max(actual.width(), actual.height()), 1280)
            self.assertLessEqual(path.stat().st_size, 250_000)
            self.assertGreater(actual.height(), actual.width())

    def test_small_image_bytes_are_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'small.png'
            image = QImage(640, 360, QImage.Format.Format_RGB32)
            image.fill(0xff223344)
            image.save(str(path))
            before = path.read_bytes()
            prepare_screen_image(path)
            self.assertEqual(path.read_bytes(), before)

    def test_compression_never_upscales_a_small_noisy_image(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'noise.png'
            width, height = 400, 300
            data = random.Random(12).randbytes(width * height * 3)
            image = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            image.save(str(path))
            self.assertGreater(path.stat().st_size, 250_000)
            prepare_screen_image(path)
            actual = QImage(str(path))
            self.assertLessEqual(actual.width(), width)
            self.assertLessEqual(actual.height(), height)

    def test_invalid_image_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'invalid.png'
            path.write_bytes(b'invalid image')
            with self.assertRaises(ValueError):
                prepare_screen_image(path)
            self.assertEqual(path.read_bytes(), b'invalid image')


if __name__ == '__main__':
    unittest.main()
