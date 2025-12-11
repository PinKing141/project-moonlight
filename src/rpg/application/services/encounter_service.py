from __future__ import annotations

import random
from typing import Optional

from rpg.domain.models.entity import Entity
from rpg.domain.repositories import EntityRepository


class EncounterService:
    def __init__(self, entity_repo: EntityRepository) -> None:
        self.entity_repo = entity_repo

    def _weighted_pick(self, pool: list[Entity], count: int, faction_bias: str | None) -> list[Entity]:
        if not pool:
            return []
        if count <= 1:
            if faction_bias:
                weights = [2 if entity.faction_id == faction_bias else 1 for entity in pool]
                return [random.choices(pool, weights=weights, k=1)[0]]
            return [random.choice(pool)]

        remaining = list(pool)
        picks: list[Entity] = []
        for _ in range(count):
            if not remaining:
                break
            if faction_bias:
                weights = [2 if entity.faction_id == faction_bias else 1 for entity in remaining]
                chosen = random.choices(remaining, weights=weights, k=1)[0]
            else:
                chosen = random.choice(remaining)
            picks.append(chosen)
            remaining = [entity for entity in remaining if entity.id != chosen.id]
        return picks

    def generate(
        self,
        location_id: int,
        player_level: int,
        world_turn: int,
        faction_bias: str | None = None,
        max_enemies: int = 1,
    ) -> list[Entity]:
        """Return a small list of entities for an encounter, deterministic per turn."""
        random.seed(hash((location_id, player_level, world_turn, faction_bias, max_enemies)))

        by_location = self.entity_repo.list_by_location(location_id)
        if by_location:
            count = min(max(1, max_enemies), len(by_location))
            return self._weighted_pick(by_location, count, faction_bias)

        level_min = max(1, player_level - 1)
        level_max = player_level + 2
        candidates = getattr(self.entity_repo, "list_by_level_band", None)
        if callable(candidates):
            band = self.entity_repo.list_by_level_band(level_min, level_max)
        else:
            mid = (level_min + level_max) // 2
            band = self.entity_repo.list_for_level(mid, tolerance=level_max - mid)
        if not band:
            return []

        count = min(max(1, max_enemies), len(band))
        return self._weighted_pick(band, count, faction_bias)

    def find_encounter(self, location_id: int, character_level: int) -> Optional[Entity]:
        """Legacy helper for callers; wraps generate using a deterministic world_turn of 0."""
        generated = self.generate(location_id, character_level, world_turn=0, max_enemies=1)
        if not generated:
            return None

        return generated[0]
