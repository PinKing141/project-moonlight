from rpg.infrastructure.inmemory.inmemory_character_repo import InMemoryCharacterRepository
from rpg.infrastructure.inmemory.inmemory_location_repo import InMemoryLocationRepository
from rpg.infrastructure.inmemory.inmemory_class_repo import InMemoryClassRepository
from rpg.application.services.game_service import GameService


def create_game_service() -> GameService:
    char_repo = InMemoryCharacterRepository()
    loc_repo = InMemoryLocationRepository()
    cls_repo = InMemoryClassRepository()

    return GameService(char_repo, location_repo=loc_repo, class_repo=cls_repo)
