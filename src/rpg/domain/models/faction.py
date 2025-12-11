from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Faction:
    id: str
    name: str
    influence: int = 0
    alignment: str = "neutral"
    tags: List[str] = field(default_factory=list)
    rivalries: Dict[str, int] = field(default_factory=dict)
