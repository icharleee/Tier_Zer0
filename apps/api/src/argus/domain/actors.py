"""Actor classes (Domain Schema Specification C1; Ontology §5).

Three kinds of agency exist, kept structurally distinct: the HumanActor (the
Steward — the only class permitted consequential transitions, ONT-PRN-007),
the AIWorkflow (the Telescope — proposals only), and the SystemProcess
(mechanism, not mind).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ActorClass(enum.Enum):
    HUMAN = "HUMAN"
    AI = "AI"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class Actor:
    actor_class: ActorClass
    actor_id: str
    # Required for AI actors (ONT-PRN-005): model identifier + version + workflow version.
    ai_model_version: str | None = None
    # SystemProcess operations attribute the human authority they act under (Article VI).
    human_authority: str | None = None


def human(actor_id: str) -> Actor:
    return Actor(ActorClass.HUMAN, actor_id)


def system(actor_id: str, *, human_authority: str) -> Actor:
    return Actor(ActorClass.SYSTEM, actor_id, human_authority=human_authority)
