import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from vesta_api.domain.dialogue_catalog import QuestionDefinition
from vesta_api.domain.dialogue_models import AttributeState, DialogueState
from vesta_api.domain.models import GeoPoint, MatchQuery, MatchResult
from vesta_api.repositories.dialogue_catalog import DialogueCatalogRepository
from vesta_api.services.matching import MatchingService
from vesta_api.services.next_question import NextQuestionPolicy

SESSION_TTL = timedelta(minutes=45)


class DialogueSessionStore:
    """In-memory, short-lived session store for the prototype.

    Deliberately not a database table: the technical prototype runs on a
    single instance (docs/hosting.md), and free-form dialogue state must not
    outlive the session per the data-minimisation rule in
    docs/architecture.md. A ``dialogue_sessions`` table is a drop-in
    replacement once horizontal scaling is introduced.
    """

    def __init__(self, ttl: timedelta = SESSION_TTL) -> None:
        self._sessions: dict[str, DialogueState] = {}
        self._ttl = ttl

    def create(
        self,
        locale: str,
        now: datetime,
        *,
        session_id: str | None = None,
    ) -> DialogueState:
        resolved_session_id = session_id or secrets.token_urlsafe(18)
        state = DialogueState(
            session_id=resolved_session_id,
            locale=locale,
            created_at=now,
            expires_at=now + self._ttl,
        )
        self._sessions[resolved_session_id] = state
        return state

    def get(self, session_id: str, now: datetime) -> DialogueState | None:
        state = self._sessions.get(session_id)
        if state is None:
            return None
        if state.is_expired(now):
            del self._sessions[session_id]
            return None
        return state

    def save(self, state: DialogueState) -> None:
        self._sessions[state.session_id] = state

    def sweep_expired(self, now: datetime) -> int:
        expired_keys = [
            key for key, state in self._sessions.items() if state.is_expired(now)
        ]
        for key in expired_keys:
            del self._sessions[key]
        return len(expired_keys)


@dataclass(frozen=True)
class DialogueTurnResult:
    state: DialogueState
    question: QuestionDefinition | None
    match_result: MatchResult | None


def _build_match_query(
    state: DialogueState,
    at: datetime,
    user_location: GeoPoint | None = None,
) -> MatchQuery:
    assert state.need is not None
    values = state.confirmed_values()
    return MatchQuery(
        need=state.need,
        language=state.locale,
        at=at,
        dog=values.get("person.has_dog"),
        has_identity_document=values.get("person.has_identity_document"),
        gender=values.get("person.gender"),
        age=values.get("person.age"),
        user_location=user_location,
    )


class DialogueOrchestrator:
    """Coordinates catalog, matching and next-question policy.

    This class decides *what may be asked or shown*; it never asks an AI to
    decide access or safety (see ADR 0002). AI involvement, if enabled, only
    rephrases what this orchestrator has already selected.
    """

    def __init__(
        self,
        matching_service: MatchingService,
        catalog: DialogueCatalogRepository,
        session_store: DialogueSessionStore,
    ) -> None:
        self._matching_service = matching_service
        self._catalog = catalog
        self._session_store = session_store
        self._next_question_policy = NextQuestionPolicy(catalog.list_questions())

    def start(
        self,
        locale: str,
        need: str,
        now: datetime,
        *,
        session_id: str | None = None,
        user_location: GeoPoint | None = None,
    ) -> DialogueTurnResult:
        created = self._session_store.create(locale, now, session_id=session_id)
        state = DialogueState(
            session_id=created.session_id,
            locale=locale,
            created_at=created.created_at,
            expires_at=created.expires_at,
            need=need,
        )
        self._session_store.save(state)
        return self._advance(state, now, user_location)

    def flag_safety_handoff(self, session_id: str, now: datetime) -> DialogueTurnResult:
        state = self._require_state(session_id, now)
        state = DialogueState(
            session_id=state.session_id,
            locale=state.locale,
            created_at=state.created_at,
            expires_at=state.expires_at,
            need=state.need,
            attributes=state.attributes,
            safety_status="handoff",
            declined_question_keys=state.declined_question_keys,
            asked_question_keys=state.asked_question_keys,
        )
        self._session_store.save(state)
        return self._advance(state, now)

    def confirm_attribute(
        self,
        session_id: str,
        key: str,
        value: object | None,
        now: datetime,
        *,
        user_location: GeoPoint | None = None,
    ) -> DialogueTurnResult:
        state = self._require_state(session_id, now)
        state = state.with_attribute(
            AttributeState(key=key, value=value, status="confirmed", source="user")
        )
        self._session_store.save(state)
        return self._advance(state, now, user_location)

    def decline_attribute(
        self,
        session_id: str,
        key: str,
        now: datetime,
        *,
        user_location: GeoPoint | None = None,
    ) -> DialogueTurnResult:
        state = self._require_state(session_id, now)
        state = state.with_attribute(
            AttributeState(key=key, value=None, status="declined", source="user")
        )
        self._session_store.save(state)
        return self._advance(state, now, user_location)

    def _require_state(self, session_id: str, now: datetime) -> DialogueState:
        state = self._session_store.get(session_id, now)
        if state is None:
            raise KeyError("dialogue_session_not_found_or_expired")
        return state

    def _advance(
        self,
        state: DialogueState,
        now: datetime,
        user_location: GeoPoint | None = None,
    ) -> DialogueTurnResult:
        if state.safety_status == "handoff":
            return DialogueTurnResult(
                state=state,
                question=None,
                match_result=MatchResult(
                    candidates=(),
                    human_handoff_required=True,
                    handoff_reason="safety_rule_triggered",
                ),
            )

        if state.need is None:
            return DialogueTurnResult(state=state, question=None, match_result=None)

        match_result = self._matching_service.match(
            _build_match_query(state, now, user_location)
        )

        if not match_result.candidates:
            return DialogueTurnResult(
                state=state, question=None, match_result=match_result
            )

        question = self._next_question_policy.next_question(
            state, match_result.candidates
        )
        if question is not None:
            state = state.with_question_asked(question.key)
            self._session_store.save(state)
            return DialogueTurnResult(state=state, question=question, match_result=None)

        return DialogueTurnResult(state=state, question=None, match_result=match_result)
