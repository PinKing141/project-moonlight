from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Character:
    id: int
    name: str
    location_id: int
    attack_min: int = 2
    attack_max: int = 4
    armor: int = 0
    hp_current: int = 10
    hp_max: int = 10
    alive: bool = True
    level: int = 1
    xp: int = 0
    money: int = 0
    character_type_id: int = 1
    attributes: Dict[str, int] = field(
        default_factory=lambda: {"might": 1, "agility": 1, "wit": 1, "spirit": 1}
    )
    faction_id: Optional[str] = None
    inventory: List[str] = field(default_factory=list)
