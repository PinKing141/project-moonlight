import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rpg.application.services.event_bus import EventBus
from rpg.application.services.game_service import GameService
from rpg.application.services.world_progression import WorldProgression
from rpg.domain.events import MonsterSlain
from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity
from rpg.domain.models.location import EncounterTableEntry, Location
from rpg.infrastructure.db.inmemory.repos import (
    InMemoryCharacterRepository,
    InMemoryEntityRepository,
    InMemoryLocationRepository,
    InMemoryWorldRepository,
)


class GameServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.event_bus = EventBus()

    def _build_service(
        self, character_repo, entity_repo, location_repo, world_repo
    ) -> GameService:
        progression = WorldProgression(world_repo, entity_repo, self.event_bus)
        return GameService(
            character_repo=character_repo,
            entity_repo=entity_repo,
            location_repo=location_repo,
            world_repo=world_repo,
            progression=progression,
        )

    def test_pick_monster_respects_level_ranges_and_weights(self) -> None:
        character = Character(id=1, name="Rogue", location_id=1, level=3)
        character_repo = InMemoryCharacterRepository({character.id: character})

        wolf = Entity(id=1, name="Wolf", level=2)
        dragon = Entity(id=2, name="Whelp", level=7)
        entity_repo = InMemoryEntityRepository([wolf, dragon])

        location = Location(
            id=1,
            name="Forest",
            encounters=[
                EncounterTableEntry(entity_id=1, weight=5, min_level=1, max_level=5),
                EncounterTableEntry(entity_id=2, weight=10, min_level=5, max_level=10),
            ],
        )
        location_repo = InMemoryLocationRepository({location.id: location})
        world_repo = InMemoryWorldRepository(seed=3)

        service = self._build_service(
            character_repo=character_repo,
            entity_repo=entity_repo,
            location_repo=location_repo,
            world_repo=world_repo,
        )

        rng = random.Random(0)
        picked = service._pick_monster(character, location, rng)

        self.assertIsNotNone(picked)
        self.assertEqual(wolf.id, picked.id, "Higher level monsters should be filtered out")

    def test_combat_awards_xp_and_emits_event_on_kill(self) -> None:
        world_repo = InMemoryWorldRepository(seed=5)
        character = Character(id=7, name="Knight", location_id=2)
        character_repo = InMemoryCharacterRepository({character.id: character})
        entity_repo = InMemoryEntityRepository([])
        location = Location(id=2, name="Ruins")
        location_repo = InMemoryLocationRepository({location.id: location})

        slain_events: list[MonsterSlain] = []
        self.event_bus.subscribe(MonsterSlain, lambda event: slain_events.append(event))

        service = self._build_service(
            character_repo=character_repo,
            entity_repo=entity_repo,
            location_repo=location_repo,
            world_repo=world_repo,
        )

        world = world_repo.load_default()
        monster = Entity(id=99, name="Goblin", level=1, hp=1)

        rng = random.Random(11)
        message = service._resolve_combat(character, monster, rng, world, location)

        self.assertIn("falls", message)
        self.assertEqual(5, character.xp)
        self.assertEqual(1, len(slain_events))
        self.assertEqual(monster.id, slain_events[0].monster_id)


if __name__ == "__main__":
    unittest.main()
