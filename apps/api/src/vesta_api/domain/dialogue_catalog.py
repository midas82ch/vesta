from dataclasses import dataclass, field
from typing import Literal

ValueType = Literal["boolean", "integer", "enum"]
AnswerType = Literal["yes_no_unknown", "single_choice", "number"]

# locale -> field name -> text, e.g. {"de": {"title": "...", "description": "..."}}
Localizations = dict[str, dict[str, str]]


@dataclass(frozen=True)
class NeedDefinition:
    key: str
    sort_order: int
    localizations: Localizations
    icon: str = "other"


@dataclass(frozen=True)
class AttributeOption:
    value: str
    sort_order: int
    localizations: Localizations


@dataclass(frozen=True)
class AttributeDefinition:
    key: str
    value_type: ValueType
    confirmation_required: bool
    skippable: bool
    options: tuple[AttributeOption, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class QuestionDefinition:
    key: str
    attribute_key: str
    answer_type: AnswerType
    priority: int
    ai_rephrasing_allowed: bool
    localizations: Localizations
    need_keys: tuple[str, ...] = field(default_factory=tuple)
