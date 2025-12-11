from dataclasses import dataclass, field
from typing import List


@dataclass
class Location:
    id: int
    name: str
    base_level: int = 1
    tags: List[str] = field(default_factory=list)
