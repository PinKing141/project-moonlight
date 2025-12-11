from rpg.domain.models.character import Character
from rpg.domain.repositories import CharacterRepository, LocationRepository
from rpg.domain.services.character_factory import create_new_character


class CharacterCreationService:
    def __init__(self, character_repo: CharacterRepository, location_repo: LocationRepository) -> None:
        self.character_repo = character_repo
        self.location_repo = location_repo

    def create_character(self, name: str, class_name: str) -> Character:
        character = create_new_character(name, class_name)
        starting_location = self.location_repo.get_starting_location()
        if not starting_location:
            raise ValueError("No starting location configured")
        character.location_id = starting_location.id
        created = self.character_repo.create(character, character.location_id)
        return created
