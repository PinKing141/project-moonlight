from __future__ import annotations

from typing import Dict, List

from rpg.domain.models.entity import Entity
from rpg.domain.repositories import EntityRepository


class InMemoryEntityRepository(EntityRepository):
    def __init__(self) -> None:
        self._entities: List[Entity] = [
            Entity(id=1, name="Goblin", level=1, hp=6, attack_min=1, attack_max=4, armor=0),
            Entity(id=2, name="Wolf", level=1, hp=7, attack_min=1, attack_max=3, armor=0),
            Entity(id=3, name="Skeleton", level=2, hp=9, attack_min=2, attack_max=5, armor=1),
        ]
        self._by_location: Dict[int, List[int]] = {1: [1, 2]}

    def get_many(self, entity_ids: List[int]) -> List[Entity]:
        if not entity_ids:
            return []
        ids = set(entity_ids)
        return [entity for entity in self._entities if entity.id in ids]

    def list_for_level(self, target_level: int, tolerance: int = 2) -> List[Entity]:
        lower = target_level - tolerance
        upper = target_level + tolerance
        return [entity for entity in self._entities if lower <= entity.level <= upper]

    def list_by_location(self, location_id: int) -> List[Entity]:
        ids = self._by_location.get(location_id, [])
        return [entity for entity in self._entities if entity.id in ids]
