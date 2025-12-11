from dataclasses import dataclass, field
from typing import List


@dataclass
class Character:
    id: int
    name: str
    location_id: int
    hp_current: int = 10
    hp_max: int = 10
    alive: bool = True
    level: int = 1
    xp: int = 0
    money: int = 0
    character_type_id: int = 1
    inventory: List[str] = field(default_factory=list)
