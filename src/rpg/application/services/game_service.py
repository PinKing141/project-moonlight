import random
from typing import Optional

from rpg.application.dtos import ActionResult
from rpg.application.services.world_progression import WorldProgression
from rpg.domain.events import MonsterSlain
from rpg.domain.models.character import Character
from rpg.domain.repositories import CharacterRepository, EntityRepository, LocationRepository, WorldRepository


class GameService:
    def __init__(
        self,
        character_repo: CharacterRepository,
        entity_repo: EntityRepository,
        location_repo: LocationRepository,
        world_repo: WorldRepository,
        progression: WorldProgression,
    ) -> None:
        self.character_repo = character_repo
        self.entity_repo = entity_repo
        self.location_repo = location_repo
        self.world_repo = world_repo
        self.progression = progression

    def get_player_view(self, player_id: int) -> str:
        world = self._require_world()
        character = self._require_character(player_id)
        location = self.location_repo.get(character.location_id)
        return (
            f"Turn {world.current_turn}\n"
            f"You are {character.name} (HP: {character.hp_current}/{character.hp_max}) in {location.name if location else 'Unknown'}.\n"
            "Actions: explore, rest, quit"
        )

    def make_choice(self, player_id: int, choice: str) -> ActionResult:
        choice = choice.strip().lower()
        if choice not in {"explore", "rest", "quit"}:
            return ActionResult(messages=["Unknown action."], game_over=False)

        if choice == "quit":
            return ActionResult(messages=["Goodbye."], game_over=True)

        world = self._require_world()
        character = self._require_character(player_id)

        if choice == "rest":
            character.hp_current = min(character.hp_current + 2, character.hp_max)
            self.character_repo.save(character)
            self.progression.tick(world, ticks=1)
            return ActionResult(messages=["You rest and feel a bit better."], game_over=False)

        # explore
        encounter_msg = self._run_encounter(character, world)
        self.character_repo.save(character)
        self.progression.tick(world, ticks=1)
        return ActionResult(messages=[encounter_msg], game_over=not character.alive)

    def _run_encounter(self, character: Character, world) -> str:
        choices = self.entity_repo.list_by_location(character.location_id)
        if not choices:
            choices = self.entity_repo.list_for_level(target_level=character.level)
        if not choices:
            return "The ruins are silent. Nothing happens."
        rng = random.Random(world.rng_seed + world.current_turn + character.location_id)
        monster = rng.choice(choices)
        roll = rng.random()
        if roll > 0.4:
            return "You slip past danger and find nothing of note."
        if roll > 0.2:
            return f"You clash with {monster.name} and win!"
        character.alive = False
        self.progression.event_bus.publish(
            MonsterSlain(
                monster_id=monster.id,
                location_id=character.location_id,
                by_character_id=character.id,
                turn=world.current_turn,
            )
        )
        return f"{monster.name} overpowers you. Darkness closes in."

    def _require_world(self):
        world = self.world_repo.load_default()
        if world is None:
            raise ValueError("World not initialized")
        return world

    def _require_character(self, player_id: int) -> Character:
        character: Optional[Character] = self.character_repo.get(player_id)
        if character is None:
            raise ValueError("Character not found")
        return character
