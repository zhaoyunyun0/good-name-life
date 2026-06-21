import tempfile
import unittest
from pathlib import Path

import app


class ShimingTests(unittest.TestCase):
    def setUp(self):
        self.original_db = app.DB_PATH
        self.temp_dir = tempfile.TemporaryDirectory()
        app.DB_PATH = Path(self.temp_dir.name) / "test.db"
        self.base = {
            "birth": "2023-01-25",
            "birth_time": "17:00",
            "gender": "girl",
            "rule_version": "missing_v1",
            "score_version": "balanced_v1",
        }

    def tearDown(self):
        app.DB_PATH = self.original_db
        self.temp_dir.cleanup()

    def test_generated_name_uses_same_score(self):
        result = app.generate_names({**self.base, "surname": "曹", "style": "elegant", "nonce": "test"})
        candidate = result["names"][0]
        score = app.score_name({**self.base, "name": candidate["name"], "gender": "女"})
        self.assertEqual(candidate["score"], score["score"])

    def test_rule_and_score_versions(self):
        missing = app.score_name({**self.base, "name": "曹安宁"})
        seasonal = app.score_name({**self.base, "name": "曹安宁", "rule_version": "seasonal_v2",
                                   "score_version": "element_v2"})
        self.assertEqual("missing_v1", missing["bazi"]["rule_version"])
        self.assertEqual("seasonal_v2", seasonal["bazi"]["rule_version"])
        self.assertEqual("element_v2", seasonal["calculation"]["score_version"])

    def test_history_is_opt_in(self):
        app.score_name({**self.base, "name": "曹安宁"})
        self.assertFalse(app.DB_PATH.exists())
        app.score_name({**self.base, "name": "曹安宁", "_store_history": True})
        self.assertTrue(app.DB_PATH.exists())

    def test_population_defaults_to_risk_mode(self):
        result = app.population({"name": "张伟"})
        self.assertEqual("risk", result["mode"])
        self.assertNotIn("total", result)


if __name__ == "__main__":
    unittest.main()
