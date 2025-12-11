from dataclasses import dataclass, field
from typing import List


@dataclass
class ActionResult:
    messages: List[str] = field(default_factory=list)
    game_over: bool = False
