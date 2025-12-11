from dataclasses import dataclass
from typing import Optional


@dataclass
class CharacterClass:
    id: Optional[int]
    name: str
    slug: str
    hit_die: Optional[str] = None
    primary_ability: Optional[str] = None
    source: Optional[str] = None
