from vesta_api.domain.ai_models import GroundingBundle, GroundingFact
from vesta_api.domain.models import Candidate

# Only offered when at least one uncertainty implies the person must reach
# out themselves (e.g. availability needs a call) - never implies a
# reservation or guaranteed admission.
_CONTACT_REQUIRED_UNCERTAINTIES = frozenset(
    {
        "availability_requires_contact",
        "availability_unknown",
        "dog_access_unknown",
        "identity_document_rule_unknown",
        "identity_document_must_be_confirmed",
        "target_group_must_be_confirmed",
        "adult_status_must_be_confirmed",
        "age_rule_requires_contact",
    }
)


def build_grounding_bundle(candidate: Candidate) -> GroundingBundle:
    """Builds the limited, fact-only bundle an AI explainer may see - no raw
    offer record, no open-ended task. Every reason/uncertainty code already
    produced by MatchingService becomes a traceable fact id."""

    facts = tuple(
        GroundingFact(id=f"reason:{code}", type=code, value=True)
        for code in candidate.reasons
    ) + tuple(
        GroundingFact(id=f"uncertainty:{code}", type=code, value=True)
        for code in candidate.uncertainties
    )

    allowed_next_actions = (
        ("call",)
        if any(code in _CONTACT_REQUIRED_UNCERTAINTIES for code in candidate.uncertainties)
        else ()
    )

    return GroundingBundle(
        offer_id=candidate.offer.id,
        facts=facts,
        match_reasons=candidate.reasons,
        uncertainties=candidate.uncertainties,
        allowed_next_actions=allowed_next_actions,
    )
