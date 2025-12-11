from dataclasses import dataclass, field
from typing import List


@dataclass
class Entity:
    id: int
    name: str
    level: int
    tags: List[str] = field(default_factory=list)
