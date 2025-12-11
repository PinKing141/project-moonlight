from abc import ABC, abstractmethod
from typing import List, Optional

from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity
from rpg.domain.models.location import Location
from rpg.domain.models.world import World


class CharacterRepository(ABC):
    @abstractmethod
    def get(self, character_id: int) -> Optional[Character]:
        raise NotImplementedError

    @abstractmethod
    def save(self, character: Character) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_location(self, location_id: int) -> List[Character]:
        raise NotImplementedError


class WorldRepository(ABC):
    @abstractmethod
    def load_default(self) -> Optional[World]:
        raise NotImplementedError

    @abstractmethod
    def save(self, world: World) -> None:
        raise NotImplementedError


class EntityRepository(ABC):
    @abstractmethod
    def get_many(self, entity_ids: List[int]) -> List[Entity]:
        raise NotImplementedError

    @abstractmethod
    def list_for_level(self, target_level: int, tolerance: int = 2) -> List[Entity]:
        raise NotImplementedError

    @abstractmethod
    def list_by_location(self, location_id: int) -> List[Entity]:
        raise NotImplementedError


class LocationRepository(ABC):
    @abstractmethod
    def get(self, location_id: int) -> Optional[Location]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[Location]:
        raise NotImplementedError
