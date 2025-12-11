from typing import List

from rpg.domain.models.character import Character
from rpg.domain.models.character_class import CharacterClass
from rpg.domain.repositories import CharacterRepository, ClassRepository, LocationRepository
from rpg.domain.services.character_factory import create_new_character


class CharacterCreationService:
    def __init__(
        self,
        character_repo: CharacterRepository,
        location_repo: LocationRepository,
        class_repo: ClassRepository,
    ) -> None:
        self.character_repo = character_repo
        self.location_repo = location_repo
        self.class_repo = class_repo

    def list_playable_classes(self) -> List[CharacterClass]:
        return self.class_repo.list_playable()

    def create_character(self, name: str, class_slug: str) -> Character:
        character_class = self.class_repo.get_by_slug(class_slug)
        if not character_class:
            raise ValueError(f"Unknown class '{class_slug}'")

        character = create_new_character(name, character_class)
        starting_location = self.location_repo.get_starting_location()
        if not starting_location:
            raise ValueError("No starting location configured")
        character.location_id = starting_location.id
        created = self.character_repo.create(character, character.location_id)
        return created
