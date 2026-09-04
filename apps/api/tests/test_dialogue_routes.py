import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from vesta_api.main import app  # noqa: E402
from vesta_api.services.dialogue_orchestrator import (  # noqa: E402
    DialogueOrchestrator,
    DialogueSessionStore,
)
from vesta_api.services.matching import MatchingService  # noqa: E402


class EmptyOfferRepository:
    def list_offers(self) -> tuple[()]:
        return ()


class DialogueRoutesTest(unittest.TestCase):
    def test_anonymized_audit_regressions_run_through_the_public_api(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parents[1]
            / "evals"
            / "dialogue_regression_cases.json"
        )
        cases = json.loads(fixture_path.read_text(encoding="utf-8"))["cases"]
        with TestClient(app) as client:
            for case in cases:
                with self.subTest(case=case["id"]):
                    if "free_text" in case:
                        response = client.post(
                            "/v1/dialogue/interpret",
                            json={"free_text": case["free_text"], "language": "en"},
                        )
                        self.assertEqual(200, response.status_code, response.text)
                        payload = response.json()
                        self.assertEqual(case["expected_outcome"], payload["outcome"])
                        self.assertEqual(case["expected_need"], payload["need_key"])
                        self.assertEqual(
                            case["expected_question_key"],
                            payload["safety_turn"]["question"]["question_key"],
                        )
                        continue

                    response = client.post(
                        "/v1/dialogue/start",
                        json={"need": case["need"], "language": "de"},
                    )
                    self.assertEqual(200, response.status_code, response.text)
                    turn = response.json()
                    if case["expected_outcome"] == "question":
                        self.assertIsNotNone(turn["question"])
                        self.assertEqual(
                            case["expected_question_key"],
                            turn["question"]["question_key"],
                        )
                        self.assertEqual(case["expected_ai_mode"], turn["ai_mode"])
                        continue

                    for _ in range(10):
                        question = turn.get("question")
                        if question is None:
                            break
                        configured = case["answers"].get(question["attribute_key"], "unknown")
                        answer: dict[str, object] = {
                            "session_id": turn["session_id"],
                            "question_key": question["question_key"],
                        }
                        if configured == "declined":
                            answer["declined"] = True
                        elif configured == "unknown":
                            answer["unknown"] = True
                        else:
                            answer["value"] = configured
                        next_response = client.post("/v1/dialogue/answer", json=answer)
                        self.assertEqual(200, next_response.status_code, next_response.text)
                        turn = next_response.json()

                    self.assertIsNone(turn.get("question"))
                    self.assertEqual(case["expected_outcome"], turn["outcome"])
                    self.assertEqual(case["expected_ai_mode"], turn["ai_mode"])
                    self.assertEqual(
                        case["expected_offer_ids"],
                        [
                            candidate["candidate"]["offer"]["id"]
                            for candidate in turn["candidates"]
                        ],
                    )

    def test_violence_signal_starts_deterministic_safety_dialogue(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/dialogue/interpret",
                json={"free_text": "Mein Mann ist gewalttätig", "language": "de"},
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("safety", payload["outcome"])
        self.assertEqual("victim_support", payload["need_key"])
        self.assertEqual("deterministic_safety", payload["source"])
        self.assertEqual(
            "safety.immediate_danger",
            payload["safety_turn"]["question"]["question_key"],
        )

    def test_immediate_danger_returns_only_emergency_numbers(self) -> None:
        with TestClient(app) as client:
            safety = client.post(
                "/v1/dialogue/interpret",
                json={"free_text": "Mein Mann ist gewalttätig", "language": "de"},
            ).json()["safety_turn"]
            response = client.post(
                "/v1/dialogue/answer",
                json={
                    "session_id": safety["session_id"],
                    "question_key": "safety.immediate_danger",
                    "value": True,
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("handoff", payload["outcome"])
        self.assertEqual([], payload["candidates"])
        self.assertEqual(
            {"117", "144"},
            {resource["phone"] for resource in payload["handoff_resources"]},
        )

    def test_non_immediate_danger_returns_142_and_only_victim_support(self) -> None:
        with TestClient(app) as client:
            safety = client.post(
                "/v1/dialogue/interpret",
                json={"free_text": "Ich werde bedroht", "language": "de"},
            ).json()["safety_turn"]
            response = client.post(
                "/v1/dialogue/answer",
                json={
                    "session_id": safety["session_id"],
                    "question_key": "safety.immediate_danger",
                    "value": False,
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("handoff", payload["outcome"])
        self.assertIn("142", {item["phone"] for item in payload["handoff_resources"]})
        self.assertTrue(payload["candidates"])
        self.assertTrue(
            all(
                item["candidate"]["offer"]["id"] == "demo-victim-support"
                for item in payload["candidates"]
            )
        )

    def test_safety_detector_respects_common_negation(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/dialogue/interpret",
                json={"free_text": "Mein Mann ist nicht gewalttätig", "language": "de"},
            )

        self.assertEqual("interpreted", response.json()["outcome"])

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
        self.assertEqual("question", payload["outcome"])
        assert payload["question"] is not None
        self.assertEqual("person.is_adult", payload["question"]["attribute_key"])
        # Regression: the web UI rendered a stray number-input form on every
        # question because answer_type was missing from the wire response,
        # so a yes/no question also showed an empty "confirm a number" field.
        self.assertEqual("yes_no_unknown", payload["question"]["answer_type"])
        self.assertTrue(payload["question"]["text"])
        self.assertEqual([], payload["candidates"])

    def test_start_rejects_an_unknown_or_inactive_category(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/v1/dialogue/start",
                json={"need": "unknown_category", "language": "de"},
            )

        self.assertEqual(422, response.status_code)
        self.assertEqual("unknown_or_inactive_category", response.json()["detail"])

    def test_dialogue_returns_an_explicit_no_offer_outcome(self) -> None:
        with TestClient(app) as client:
            original = app.state.dialogue_orchestrator
            app.state.dialogue_orchestrator = DialogueOrchestrator(
                matching_service=MatchingService(EmptyOfferRepository()),
                catalog=app.state.dialogue_catalog,
                session_store=DialogueSessionStore(),
            )
            try:
                response = client.post(
                    "/v1/dialogue/start",
                    json={"need": "basic_needs", "language": "de"},
                )
            finally:
                app.state.dialogue_orchestrator = original

        self.assertEqual(200, response.status_code)
        self.assertEqual("no_match", response.json()["outcome"])
        self.assertEqual([], response.json()["candidates"])
        self.assertFalse(response.json()["human_handoff_required"])

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
        self.assertEqual("matches", payload["outcome"])
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
                    "question_key": "access.has_identity_document",
                    "value": True,
                },
            )

        self.assertEqual(404, response.status_code)

    def test_adult_answer_must_be_boolean(self) -> None:
        with TestClient(app) as client:
            payload = client.post(
                "/v1/dialogue/start",
                json={"need": "sleep_tonight", "language": "de"},
            ).json()
            session_id = payload["session_id"]

            for _ in range(10):
                question = payload["question"]
                assert question is not None
                if question["attribute_key"] == "person.is_adult":
                    break
                response = client.post(
                    "/v1/dialogue/answer",
                    json={
                        "session_id": session_id,
                        "question_key": question["question_key"],
                        "declined": True,
                    },
                )
                self.assertEqual(200, response.status_code)
                payload = response.json()

            adult_question = payload["question"]
            assert adult_question is not None
            self.assertEqual("person.is_adult", adult_question["attribute_key"])
            self.assertEqual("yes_no_unknown", adult_question["answer_type"])

            for invalid_value in (-1, 18, "yes", 6.5):
                with self.subTest(value=invalid_value):
                    response = client.post(
                        "/v1/dialogue/answer",
                        json={
                            "session_id": session_id,
                            "question_key": adult_question["question_key"],
                            "value": invalid_value,
                        },
                    )
                    self.assertEqual(422, response.status_code)

            response = client.post(
                "/v1/dialogue/answer",
                json={
                    "session_id": session_id,
                    "question_key": adult_question["question_key"],
                    "value": True,
                },
            )
            self.assertEqual(200, response.status_code)

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
        self.assertIn("distance_band", serialized)
        self.assertTrue(
            any(event.payload.get("location_used") is True for event in events)
        )


if __name__ == "__main__":
    unittest.main()
