from __future__ import annotations

import random
from typing import Optional

from rpg.domain.models.entity import Entity
from rpg.domain.repositories import EntityRepository


class EncounterService:
    def __init__(self, entity_repo: EntityRepository) -> None:
        self.entity_repo = entity_repo

    def find_encounter(self, location_id: int, character_level: int) -> Optional[Entity]:
        candidates = self.entity_repo.list_by_location(location_id)
        if not candidates:
            candidates = self.entity_repo.list_for_level(character_level)

        if not candidates:
            return None

        rng = random.Random(character_level + location_id)
        return rng.choice(candidates)
