from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

AttributeStatus = Literal["proposed", "confirmed", "unknown", "declined"]
AttributeSource = Literal["user", "ai", "derived"]


@dataclass(frozen=True)
class AttributeState:
    key: str
    value: object | None
    status: AttributeStatus
    source: AttributeSource

    def __post_init__(self) -> None:
        if self.source == "ai" and self.status == "confirmed":
            raise ValueError(
                "An AI-sourced attribute may not be created as 'confirmed'. "
                "It must start as 'proposed' and be promoted only by an explicit "
                "user confirmation."
            )


@dataclass(frozen=True)
class DialogueState:
    session_id: str
    locale: str
    created_at: datetime
    expires_at: datetime
    need: str | None = None
    attributes: tuple[AttributeState, ...] = field(default_factory=tuple)
    safety_status: Literal["clear", "handoff"] = "clear"
    declined_question_keys: tuple[str, ...] = field(default_factory=tuple)
    asked_question_keys: tuple[str, ...] = field(default_factory=tuple)

    def attribute(self, key: str) -> AttributeState | None:
        for attribute in self.attributes:
            if attribute.key == key:
                return attribute
        return None

    def with_attribute(self, attribute: AttributeState) -> "DialogueState":
        remaining = tuple(a for a in self.attributes if a.key != attribute.key)
        return DialogueState(
            session_id=self.session_id,
            locale=self.locale,
            created_at=self.created_at,
            expires_at=self.expires_at,
            need=self.need,
            attributes=(*remaining, attribute),
            safety_status=self.safety_status,
            declined_question_keys=self.declined_question_keys,
            asked_question_keys=self.asked_question_keys,
        )

    def with_question_asked(self, question_key: str) -> "DialogueState":
        if question_key in self.asked_question_keys:
            return self
        return DialogueState(
            session_id=self.session_id,
            locale=self.locale,
            created_at=self.created_at,
            expires_at=self.expires_at,
            need=self.need,
            attributes=self.attributes,
            safety_status=self.safety_status,
            declined_question_keys=self.declined_question_keys,
            asked_question_keys=(*self.asked_question_keys, question_key),
        )

    def is_expired(self, at: datetime) -> bool:
        return at >= self.expires_at

    def confirmed_values(self) -> dict[str, object | None]:
        return {
            attribute.key: attribute.value
            for attribute in self.attributes
            if attribute.status == "confirmed"
        }
