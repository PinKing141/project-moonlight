from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Entity:
    id: int
    name: str
    level: int
    hp: int = 6
    attack_min: int = 1
    attack_max: int = 3
    armor: int = 0
    faction_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    loot_tags: List[str] = field(default_factory=list)
