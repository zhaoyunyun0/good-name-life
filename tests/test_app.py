import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_ai_analysis_is_structured_and_omits_raw_birth(self):
        analysis = {
            "summary": "整体清朗自然。", "semantic_analysis": "语义协调。",
            "style_tags": ["清雅"], "era_impression": "现代中带有古典感。",
            "pronunciation_review": "声调有变化。", "cultural_imagery": "属于意象联想。",
            "risk_level": "low", "risk_items": [], "source_notes": [], "warnings": [],
        }

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self): return json.dumps({"output_text": json.dumps(analysis, ensure_ascii=False)}).encode()

        def fake_urlopen(request, timeout):
            payload = request.data.decode("utf-8")
            self.assertNotIn("2023-01-25", payload)
            return FakeResponse()

        payload = {**self.base, "name": "曹安宁", "gender": "女", "_ai_consent": True}
        with patch.object(app, "AI_ENABLED", True), patch.object(app, "OPENAI_API_KEY", "test-key"), \
             patch.object(app, "urlopen", fake_urlopen):
            result = app.analyze_name_with_ai(payload)
        self.assertEqual("low", result["analysis"]["risk_level"])
        self.assertFalse(result["meta"]["raw_birth_sent"])

    def test_ai_features_live_in_dedicated_tab(self):
        html = (app.ROOT / "index.html").read_text(encoding="utf-8")
        script = (app.ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-page="ai"', html)
        self.assertIn('id="ai-form"', html)
        self.assertIn('id="ai-page-result"', html)
        self.assertNotIn('id="ai-score-result"', script)
        self.assertNotIn('ai-candidate-', script)


if __name__ == "__main__":
    unittest.main()
