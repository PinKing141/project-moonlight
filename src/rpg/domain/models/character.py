from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Character:
    id: Optional[int]
    name: str
    level: int = 1
    xp: int = 0
    money: int = 0
    hp_max: int = 10
    hp_current: int = 10
    class_name: Optional[str] = None
    base_attributes: Dict[str, int] = field(default_factory=dict)
    location_id: Optional[int] = None
    attack_min: int = 2
    attack_max: int = 4
    armor: int = 0
    alive: bool = True
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
