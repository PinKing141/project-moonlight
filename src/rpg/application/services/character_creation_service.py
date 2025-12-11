from __future__ import annotations

from dataclasses import replace
from typing import Dict

from rpg.domain.models.character import Character
from rpg.domain.repositories import CharacterRepository, LocationRepository


class CharacterCreationService:
    """Handle creation of new characters with simple class presets."""

    CLASS_PRESETS: Dict[str, Dict[str, int]] = {
        "fighter": {"hp": 16, "attack_min": 3, "attack_max": 6, "armor": 2, "might": 3, "agility": 1},
        "rogue": {"hp": 12, "attack_min": 2, "attack_max": 5, "armor": 1, "might": 1, "agility": 3},
        "wizard": {"hp": 10, "attack_min": 1, "attack_max": 7, "armor": 0, "might": 1, "agility": 1, "wit": 3},
    }

    def __init__(self, character_repo: CharacterRepository, location_repo: LocationRepository) -> None:
        self.character_repo = character_repo
        self.location_repo = location_repo

    def create_character(self, name: str, class_key: str) -> Character:
        preset = self.CLASS_PRESETS.get(class_key)
        if preset is None:
            raise ValueError(f"Unknown class selection: {class_key}")

        location_id = self._default_starting_location()
        character_id = self._next_character_id()

        base_character = Character(
            id=character_id,
            name=name or "Nameless One",
            location_id=location_id,
        )

        updated_attributes = dict(base_character.attributes)
        updated_attributes["might"] = max(preset.get("might", 1), updated_attributes.get("might", 1))
        updated_attributes["agility"] = max(preset.get("agility", 1), updated_attributes.get("agility", 1))
        updated_attributes["wit"] = max(preset.get("wit", 1), updated_attributes.get("wit", 1))
        updated_attributes["spirit"] = max(preset.get("spirit", 1), updated_attributes.get("spirit", 1))

        character = replace(
            base_character,
            hp_current=preset["hp"],
            hp_max=preset["hp"],
            attack_min=preset["attack_min"],
            attack_max=preset["attack_max"],
            armor=preset["armor"],
            attributes=updated_attributes,
        )

        self.character_repo.save(character)
        return character

    def _next_character_id(self) -> int:
        existing = self.character_repo.list_all()
        if not existing:
            return 1
        return max(character.id for character in existing) + 1

    def _default_starting_location(self) -> int:
        locations = self.location_repo.list_all()
        if locations:
            return locations[0].id
        return 1
