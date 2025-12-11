import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rpg.application.services.event_bus import EventBus
from rpg.application.services.world_progression import WorldProgression
from rpg.domain.events import TickAdvanced
from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity
from rpg.domain.models.world import World
from rpg.infrastructure.db.inmemory.repos import (
    InMemoryCharacterRepository,
    InMemoryEntityRepository,
    InMemoryWorldRepository,
)


class InMemoryEntityRepositoryTests(unittest.TestCase):
    def test_filters_by_level_and_location(self) -> None:
        entities = [
            Entity(id=1, name="Rat", level=1),
            Entity(id=2, name="Ogre", level=6),
            Entity(id=3, name="Wolf", level=2),
        ]
        repo = InMemoryEntityRepository(entities)
        repo.set_location_entities(location_id=10, entity_ids=[1, 3])

        level_matches = repo.list_for_level(target_level=5)
        self.assertEqual([entities[1]], level_matches)

        nearby = repo.list_by_location(location_id=10)
        self.assertEqual({1, 3}, {e.id for e in nearby})


class InMemoryCharacterRepositoryTests(unittest.TestCase):
    def test_find_by_location_returns_only_matching_characters(self) -> None:
        repo = InMemoryCharacterRepository(
            {
                1: Character(id=1, name="Hero", location_id=2),
                2: Character(id=2, name="Villager", location_id=3),
                3: Character(id=3, name="Scout", location_id=2),
            }
        )

        at_location = repo.find_by_location(location_id=2)
        self.assertEqual({1, 3}, {c.id for c in at_location})


class InMemoryWorldRepositoryTests(unittest.TestCase):
    def test_save_and_load_persists_world_state(self) -> None:
        repo = InMemoryWorldRepository(seed=9)
        world = repo.load_default()
        world.name = "Test World"
        world.advance_turns(3)

        repo.save(world)
        reloaded = repo.load_default()

        self.assertEqual("Test World", reloaded.name)
        self.assertEqual(3, reloaded.current_turn)


class WorldProgressionTests(unittest.TestCase):
    def test_tick_advances_world_and_publishes_event(self) -> None:
        world = World(id=1, name="Seeded", rng_seed=1)
        world_repo = InMemoryWorldRepository(seed=1)
        world_repo.save(world)
        entity_repo = InMemoryEntityRepository([])
        event_bus = EventBus()
        events: list[TickAdvanced] = []
        event_bus.subscribe(TickAdvanced, lambda e: events.append(e))

        progression = WorldProgression(world_repo, entity_repo, event_bus)
        progression.tick(world, ticks=2)

        self.assertEqual(2, world.current_turn)
        self.assertEqual(1, len(events))
        self.assertEqual(2, events[0].turn_after)


if __name__ == "__main__":
    unittest.main()
