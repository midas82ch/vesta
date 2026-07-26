import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.main import app  # noqa: E402


class DialogueRoutesTest(unittest.TestCase):
    def test_interpret_is_honest_about_template_mode(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/dialogue/interpret",
                json={"free_text": "Ich brauche einen Schlafplatz", "language": "de"},
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("template", payload["source"])
        self.assertEqual([], payload["proposals"])
        self.assertIn("free_text_interpretation_unavailable", payload["ambiguities"])

    def test_start_returns_first_relevant_question_for_sleep_tonight(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/dialogue/start", json={"need": "sleep_tonight", "language": "de"}
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["session_id"])
        self.assertEqual("template", payload["ai_mode"])
        assert payload["question"] is not None
        self.assertEqual("person.has_identity_document", payload["question"]["attribute_key"])
        # Regression: the web UI rendered a stray number-input form on every
        # question because answer_type was missing from the wire response,
        # so a yes/no question also showed an empty "confirm a number" field.
        self.assertEqual("yes_no_unknown", payload["question"]["answer_type"])
        self.assertTrue(payload["question"]["text"])
        self.assertEqual([], payload["candidates"])

    def test_full_turn_reaches_an_explained_result(self) -> None:
        with TestClient(app) as client:
            started = client.post(
                "/v1/dialogue/start", json={"need": "sleep_tonight", "language": "de"}
            )
            session_id = started.json()["session_id"]
            payload = started.json()

            # Decline every follow-up question until the orchestrator has
            # enough information to return (explained) results.
            for _ in range(10):
                if payload["question"] is None:
                    break
                response = client.post(
                    "/v1/dialogue/answer",
                    json={
                        "session_id": session_id,
                        "question_key": payload["question"]["question_key"],
                        "declined": True,
                    },
                )
                self.assertEqual(200, response.status_code)
                payload = response.json()
        self.assertGreaterEqual(len(payload["candidates"]), 1)
        explanation = payload["candidates"][0]["explanation"]
        assert explanation is not None
        self.assertEqual("template", explanation["source"])
        for reason in explanation["reasons"]:
            self.assertTrue(reason["supported_by"])

    def test_answer_with_unknown_session_returns_404(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/dialogue/answer",
                json={
                    "session_id": "does-not-exist",
                    "question_key": "sleep.has_identity_document",
                    "value": True,
                },
            )

        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
