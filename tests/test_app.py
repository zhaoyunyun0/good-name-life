import json
import tempfile
import unittest
from collections import Counter
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
        }

    def tearDown(self):
        app.DB_PATH = self.original_db
        self.temp_dir.cleanup()

    def test_generated_name_uses_same_score(self):
        result = app.generate_names({**self.base, "surname": "曹", "style": "elegant", "nonce": "test"})
        candidate = result["names"][0]
        score = app.score_name({**self.base, "name": candidate["name"], "gender": "女"})
        self.assertEqual(candidate["score"], score["score"])

    def test_generated_names_are_diverse_and_include_risk(self):
        result = app.generate_names({**self.base, "surname": "曹", "style": "elegant", "nonce": "diverse"})
        given_chars = [char for item in result["names"] for char in app.split_full_name(item["name"])[1]]
        self.assertEqual(10, len(result["names"]))
        self.assertGreaterEqual(len(set(given_chars)), 12)
        self.assertLessEqual(max(Counter(given_chars).values()), 2)
        self.assertTrue(all("duplicate_risk" in item for item in result["names"]))
        self.assertGreater(result["strategy"]["character_pool_size"], 200)
        self.assertEqual(8105, result["strategy"]["base_character_count"])
        self.assertGreaterEqual(result["strategy"]["eligible_character_count"], 800)
        self.assertTrue(all(not (set(app.split_full_name(item["name"])[1]) & app.MASCULINE_CHARS)
                            for item in result["names"]))

    def test_birth_date_and_style_change_recommendations(self):
        common = {"surname": "曹", "birth_time": "17:00", "gender": "girl", "nonce": "same"}
        june_1 = app.generate_names({**common, "birth": "2025-06-01", "style": "elegant"})
        june_3 = app.generate_names({**common, "birth": "2025-06-03", "style": "elegant"})
        bright = app.generate_names({**common, "birth": "2025-06-01", "style": "bright"})
        names_1 = {item["name"] for item in june_1["names"]}
        self.assertNotEqual(names_1, {item["name"] for item in june_3["names"]})
        self.assertNotEqual(names_1, {item["name"] for item in bright["names"]})
        self.assertTrue(all(item["style_matches"] >= 1 for item in bright["names"]))

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
        self.assertNotIn('name="rule_version"', html)
        self.assertNotIn('name="score_version"', html)
        self.assertNotIn("rule_version", script)
        self.assertNotIn("score_version", script)


if __name__ == "__main__":
    unittest.main()
