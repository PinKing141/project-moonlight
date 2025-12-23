import random
from typing import Optional

from rpg.application.dtos import ActionResult
from rpg.application.services.world_progression import WorldProgression
from rpg.domain.events import MonsterSlain
from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity
from rpg.domain.models.location import Location
from rpg.domain.repositories import (
    CharacterRepository,
    ClassRepository,
    EntityRepository,
    LocationRepository,
    WorldRepository,
    SpellRepository,
)


class GameService:
    def __init__(
        self,
        character_repo: CharacterRepository,
        entity_repo: EntityRepository | None = None,
        location_repo: LocationRepository | None = None,
        world_repo: WorldRepository | None = None,
        progression: WorldProgression | None = None,
        class_repo: ClassRepository | None = None,
        spell_repo: SpellRepository | None = None,
        verbose_level: str = "compact",
) -> None:
        from rpg.application.services.character_creation_service import CharacterCreationService
        from rpg.application.services.encounter_service import EncounterService
        from rpg.application.services.combat_service import CombatService

        self.character_repo = character_repo
        self.entity_repo = entity_repo
        self.location_repo = location_repo
        self.world_repo = world_repo
        self.progression = progression
        self.character_creation_service = None
        self.encounter_service = None
        self.combat_service = None
        self.spell_repo = spell_repo
        self.verbose_level = verbose_level

        if class_repo and location_repo:
            self.character_creation_service = CharacterCreationService(
                character_repo, class_repo, location_repo
            )

        if entity_repo:
            self.encounter_service = EncounterService(entity_repo)
            self.combat_service = CombatService(spell_repo, verbosity=verbose_level)

    def rest(self, character_id: int) -> tuple[Character, Optional["World"]]:
        character = self._require_character(character_id)
        heal_amount = max(character.hp_max // 4, 4)
        character.hp_current = min(character.hp_current + heal_amount, character.hp_max)
        character.alive = True
        if hasattr(character, "spell_slots_max"):
            character.spell_slots_current = getattr(character, "spell_slots_max", 0)
        self.character_repo.save(character)
        world = self.advance_world(ticks=1)
        return character, world

    def advance_world(self, ticks: int = 1):
        if not self.world_repo:
            return None

        # Prefer the progression pipeline if available.
        if self.progression:
            world = self._require_world()
            self.progression.tick(world, ticks=ticks)
            return world

        world = self.world_repo.load_default()
        if world is None:
            raise ValueError("World not initialized")
        world.advance_turns(ticks)
        self.world_repo.save(world)
        return world

    def explore(self, character_id: int):
        character = self._require_character(character_id)
        world = self._require_world()

        if not self.encounter_service:
            return [], character, world

        location = self.location_repo.get(character.location_id) if self.location_repo else None
        faction_bias = None
        if location and getattr(location, "factions", None):
            faction_bias = location.factions[0] if location.factions else None

        encounter = self.encounter_service.generate(
            location_id=character.location_id or 0,
            player_level=character.level,
            world_turn=world.current_turn,
            faction_bias=faction_bias,
            max_enemies=2,
        )

        self.advance_world(ticks=1)
        return encounter, character, world

    def get_player_view(self, player_id: int) -> str:
        world = self._require_world()
        character = self._require_character(player_id)
        location = self.location_repo.get(character.location_id)

        location_line = (
            f"in {location.name} [{location.biome}]"
            if location
            else "in an unknown place"
        )
        tags = ", ".join(location.tags) if location and location.tags else "quiet"
        factions = ", ".join(location.factions) if location and location.factions else "unclaimed"
        return (
            f"Turn {world.current_turn}\n"
            f"You are {character.name} (HP: {character.hp_current}/{character.hp_max}, Armor {character.armor}) {location_line}.\n"
            f"Local threats: {tags}; influence: {factions}; suggested level {location.recommended_level if location else '?'}\n"
            "Actions: explore, rest, quit"
        )

    def list_characters(self) -> list[Character]:
        return self.character_repo.list_all()

    def make_choice(self, player_id: int, choice: str) -> ActionResult:
        choice = choice.strip().lower()
        if choice not in {"explore", "rest", "quit"}:
            return ActionResult(messages=["Unknown action."], game_over=False)

        if choice == "quit":
            return ActionResult(messages=["Goodbye."], game_over=True)

        world = self._require_world()
        character = self._require_character(player_id)
        location = self.location_repo.get(character.location_id)

        if choice == "rest":
            self.rest(player_id)
            return ActionResult(messages=["You rest and feel a bit better."], game_over=False)

        # explore
        encounter_msg = self._run_encounter(character, world, location)
        self.character_repo.save(character)
        self.advance_world(ticks=1)
        return ActionResult(messages=[encounter_msg], game_over=not character.alive)

    def _run_encounter(self, character: Character, world, location: Optional[Location]) -> str:
        rng = random.Random(world.rng_seed + world.current_turn + character.location_id)
        monster = self._pick_monster(character, location, rng)
        if monster is None:
            return "The ruins are silent. Nothing happens."

        evade_roll = rng.random()
        if evade_roll > 0.8:
            return f"You spot signs of {monster.name} and steer clear before it notices you."

        return self._resolve_combat(character, monster, rng, world, location)

    def _pick_monster(
        self, character: Character, location: Optional[Location], rng: random.Random
    ) -> Optional[Entity]:
        if location and location.encounters:
            candidates = self.entity_repo.get_many([entry.entity_id for entry in location.encounters])
            lookup = {entity.id: entity for entity in candidates}
            weighted: list[tuple[Entity, int]] = []
            for entry in location.encounters:
                entity = lookup.get(entry.entity_id)
                if entity is None:
                    continue
                if not (entry.min_level <= character.level <= entry.max_level):
                    continue
                weighted.append((entity, max(entry.weight, 1)))

            if weighted:
                entities, weights = zip(*weighted)
                return rng.choices(list(entities), weights=list(weights), k=1)[0]

        choices = self.entity_repo.list_by_location(character.location_id)
        if not choices:
            choices = self.entity_repo.list_for_level(target_level=character.level)
        if not choices:
            return None
        return rng.choice(choices)

    def _resolve_combat(
        self,
        character: Character,
        monster: Entity,
        rng: random.Random,
        world,
        location: Optional[Location],
    ) -> str:
        monster_hp = monster.hp

        might = character.attributes.get("might", 0)
        strength = character.attributes.get("strength", 0)
        attribute_bonus = strength if strength else might
        player_strike = rng.randint(character.attack_min, character.attack_max) + attribute_bonus
        modified_strike = int(player_strike * character.outgoing_damage_multiplier)
        effective_player_damage = max(modified_strike - monster.armor, 1)
        monster_hp -= effective_player_damage

        if monster_hp <= 0:
            xp_gain = max(monster.level * 5, 1)
            character.xp += xp_gain
            faction_note = f" for the {monster.faction_id}" if monster.faction_id else ""
            self.progression.event_bus.publish(
                MonsterSlain(
                    monster_id=monster.id,
                    location_id=character.location_id,
                    by_character_id=character.id,
                    turn=world.current_turn,
                )
            )
            return (
                f"You cleave through {monster.name}{faction_note}, dealing {effective_player_damage} damage. "
                f"It falls. (+{xp_gain} XP)"
            )

        monster_strike = rng.randint(monster.attack_min, monster.attack_max)
        modified_monster_strike = int(monster_strike * character.incoming_damage_multiplier)
        damage_taken = max(modified_monster_strike - character.armor, 1)
        character.hp_current = max(character.hp_current - damage_taken, 0)

        if character.hp_current <= 0:
            character.alive = False
            threat = f" from the {monster.faction_id}" if monster.faction_id else ""
            return (
                f"{monster.name}{threat} lands a brutal hit for {damage_taken} damage. "
                "You collapse and darkness closes in."
            )

        location_note = f" around {location.name}" if location else "" 
        return (
            f"You and {monster.name} trade blows{location_note}. "
            f"You deal {effective_player_damage} damage but take {damage_taken}. "
            f"{monster.name} still has {monster_hp} HP; you have {character.hp_current}/{character.hp_max}."
        )

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
