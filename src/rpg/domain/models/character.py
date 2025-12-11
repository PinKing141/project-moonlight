from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Character:
    id: Optional[int]
    name: str
    location_id: int = 0
    class_name: Optional[str] = None
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
        default_factory=lambda: {
            "strength": 10,
            "constitution": 10,
            "dexterity": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
            "might": 1,
            "agility": 1,
            "wit": 1,
            "spirit": 1,
        }
    )
    faction_id: Optional[str] = None
    inventory: List[str] = field(default_factory=list)
