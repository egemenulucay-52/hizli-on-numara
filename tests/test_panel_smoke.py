import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class PanelSmokeTests(unittest.TestCase):
    def test_all_lightweight_sections_open_without_exception(self):
        panel_path = Path(__file__).resolve().parents[1] / "panel.py"
        app = AppTest.from_file(str(panel_path), default_timeout=120)
        app.run(timeout=120)
        self.assertEqual(len(app.exception), 0)

        sections = [
            "Genel Bakış",
            "Keşifsel Analiz",
            "İkili ve Kombinasyonlar",
            "Araştırma Protokolü",
            "Canlı Tahmin",
            "Model Karşılaştırma",
            "İstatistiksel Kontrol",
            "Veri",
        ]
        for section in sections:
            with self.subTest(section=section):
                app.sidebar.radio[0].set_value(section)
                app.run(timeout=120)
                self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
