from abc import ABC, abstractmethod
from typing import List, Optional

from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity
from rpg.domain.models.faction import Faction
from rpg.domain.models.location import Location
from rpg.domain.models.world import World
from rpg.domain.models.character_class import CharacterClass
from rpg.domain.models.encounter_definition import EncounterDefinition


class CharacterRepository(ABC):
    @abstractmethod
    def get(self, character_id: int) -> Optional[Character]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[Character]:
        raise NotImplementedError

    @abstractmethod
    def save(self, character: Character) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_location(self, location_id: int) -> List[Character]:
        raise NotImplementedError

    @abstractmethod
    def create(self, character: Character, location_id: int) -> Character:
        raise NotImplementedError


class WorldRepository(ABC):
    @abstractmethod
    def load_default(self) -> Optional[World]:
        raise NotImplementedError

    @abstractmethod
    def save(self, world: World) -> None:
        raise NotImplementedError

    def get_default(self) -> Optional[World]:
        """Convenience alias for load_default to align with UI expectations."""
        return self.load_default()


class EntityRepository(ABC):
    @abstractmethod
    def get(self, entity_id: int) -> Optional[Entity]:
        raise NotImplementedError

    @abstractmethod
    def get_many(self, entity_ids: List[int]) -> List[Entity]:
        raise NotImplementedError

    @abstractmethod
    def list_for_level(self, target_level: int, tolerance: int = 2) -> List[Entity]:
        raise NotImplementedError

    @abstractmethod
    def list_by_location(self, location_id: int) -> List[Entity]:
        raise NotImplementedError

    def list_by_level_band(self, level_min: int, level_max: int) -> List[Entity]:
        """Optional helper; default falls back to list_for_level with midpoint."""
        target = (level_min + level_max) // 2
        tolerance = max(level_max - target, 0)
        return self.list_for_level(target_level=target, tolerance=tolerance)


class LocationRepository(ABC):
    @abstractmethod
    def get(self, location_id: int) -> Optional[Location]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[Location]:
        raise NotImplementedError

    @abstractmethod
    def get_starting_location(self) -> Optional[Location]:
        raise NotImplementedError


class ClassRepository(ABC):
    @abstractmethod
    def list_playable(self) -> List[CharacterClass]:
        raise NotImplementedError

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[CharacterClass]:
        raise NotImplementedError


class FactionRepository(ABC):
    @abstractmethod
    def get(self, faction_id: str) -> Optional[Faction]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[Faction]:
        raise NotImplementedError

    @abstractmethod
    def save(self, faction: Faction) -> None:
        raise NotImplementedError

    def get_many(self, faction_ids: List[str]) -> List[Faction]:
        lookup = {faction.id: faction for faction in self.list_all()}
        return [lookup[fid] for fid in faction_ids if fid in lookup]


class EncounterDefinitionRepository(ABC):
    @abstractmethod
    def list_for_location(self, location_id: int) -> List[EncounterDefinition]:
        raise NotImplementedError

    def list_global(self) -> List[EncounterDefinition]:
        """Fallback hook for repositories that support global tables."""

        return []
