import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.main import app  # noqa: E402


class DialogueRoutesTest(unittest.TestCase):
    def test_workflow_audit_failure_does_not_break_public_dialogue(self) -> None:
        class FailingWorkflowAuditLog:
            def record(self, _event: object) -> None:
                raise RuntimeError("workflow_database_unavailable")

        with TestClient(app) as client:
            original = app.state.workflow_audit_log
            app.state.workflow_audit_log = FailingWorkflowAuditLog()
            try:
                response = client.post(
                    "/v1/dialogue/interpret",
                    json={
                        "free_text": "Ich brauche einen Schlafplatz",
                        "language": "de",
                    },
                )
            finally:
                app.state.workflow_audit_log = original

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["workflow_id"])

    def test_interpret_is_honest_about_template_mode(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/dialogue/interpret",
                json={"free_text": "Ich brauche einen Schlafplatz", "language": "de"},
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["workflow_id"])
        self.assertEqual("template", payload["source"])
        self.assertEqual([], payload["proposals"])
        self.assertIn("free_text_interpretation_unavailable", payload["ambiguities"])

    def test_interpretation_workflow_id_is_reused_by_dialogue(self) -> None:
        with TestClient(app) as client:
            interpreted = client.post(
                "/v1/dialogue/interpret",
                json={"free_text": "Ich brauche einen Schlafplatz", "language": "de"},
            )
            workflow_id = interpreted.json()["workflow_id"]
            started = client.post(
                "/v1/dialogue/start",
                json={
                    "need": "sleep_tonight",
                    "language": "de",
                    "workflow_id": workflow_id,
                },
            )
            events = app.state.workflow_audit_log.list_events(workflow_id)

        self.assertEqual(200, started.status_code)
        self.assertEqual(workflow_id, started.json()["session_id"])
        self.assertEqual(
            ("input", "system", "input", "system", "output"),
            tuple(event.stage for event in events),
        )
        self.assertEqual("free_text_submitted", events[0].event_type)
        self.assertEqual("public_response_returned", events[-1].event_type)

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

    def test_location_is_accepted_but_not_retained_in_workflow_audit(self) -> None:
        location = {"latitude": 46.948123, "longitude": 7.447456}
        with TestClient(app) as client:
            started = client.post(
                "/v1/dialogue/start",
                json={
                    "need": "sleep_tonight",
                    "language": "de",
                    "user_location": location,
                },
            )
            payload = started.json()
            workflow_id = payload["session_id"]

            for _ in range(10):
                if payload["question"] is None:
                    break
                response = client.post(
                    "/v1/dialogue/answer",
                    json={
                        "session_id": workflow_id,
                        "question_key": payload["question"]["question_key"],
                        "declined": True,
                        "user_location": location,
                    },
                )
                self.assertEqual(200, response.status_code)
                payload = response.json()

            events = app.state.workflow_audit_log.list_events(workflow_id)

        serialized = json.dumps(
            [event.payload for event in events],
            ensure_ascii=False,
            sort_keys=True,
        )
        self.assertNotIn("46.948", serialized)
        self.assertNotIn("7.447", serialized)
        self.assertNotIn("distance_meters", serialized)
        self.assertTrue(
            any(event.payload.get("location_used") is True for event in events)
        )


if __name__ == "__main__":
    unittest.main()
