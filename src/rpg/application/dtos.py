from dataclasses import dataclass, field
from typing import List
from rpg.domain.models.entity import Entity


@dataclass
class ActionResult:
    messages: List[str] = field(default_factory=list)
    game_over: bool = False


@dataclass
class EncounterPlan:
    enemies: List[Entity] = field(default_factory=list)
    definition_id: str | None = None
    faction_bias: str | None = None
    source: str = "table"
