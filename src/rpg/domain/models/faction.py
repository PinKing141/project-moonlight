from dataclasses import dataclass


@dataclass
class Faction:
    id: str
    name: str
    influence: int = 0
