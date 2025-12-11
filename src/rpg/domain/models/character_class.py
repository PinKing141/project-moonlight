from dataclasses import dataclass


@dataclass
class CharacterClass:
    id: int | None
    name: str
    slug: str
    hit_die: str = "d8"
    primary_ability: str | None = None
