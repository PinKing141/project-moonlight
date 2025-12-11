from rpg.domain.repositories import CharacterRepository, ClassRepository, LocationRepository
from rpg.domain.services.character_factory import create_new_character
from rpg.domain.models.character_class import CharacterClass


class CharacterCreationService:
    def __init__(self, character_repo: CharacterRepository,
                 class_repo: ClassRepository,
                 location_repo: LocationRepository):
        self.character_repo = character_repo
        self.class_repo = class_repo
        self.location_repo = location_repo

    def list_classes(self) -> list[CharacterClass]:
        return self.class_repo.list_playable()

    def create_character(self, name: str, class_index: int) -> "Character":
        classes = self.class_repo.list_playable()
        chosen = classes[class_index]

        character = create_new_character(name, chosen)

        starting_location = self.location_repo.get_starting_location()
        character.location_id = starting_location.id if starting_location else None

        self.character_repo.create(character, character.location_id or 0)

        return character
