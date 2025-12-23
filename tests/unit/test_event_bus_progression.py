import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rpg.application.services.event_bus import EventBus
from rpg.application.services.world_progression import WorldProgression
from rpg.domain.events import TickAdvanced
from rpg.domain.models.world import World


class EventBusTests(unittest.TestCase):
    class _EventA:
        def __init__(self, payload: str):
            self.payload = payload

    class _EventB:
        def __init__(self, value: int):
            self.value = value

    def test_publish_invokes_all_subscribers_for_event_type(self) -> None:
        bus = EventBus()
        received_a: list[str] = []
        received_b: list[int] = []

        bus.subscribe(self._EventA, lambda event: received_a.append(event.payload))
        bus.subscribe(self._EventA, lambda event: received_a.append(event.payload.upper()))
        bus.subscribe(self._EventB, lambda event: received_b.append(event.value * 2))

        bus.publish(self._EventA("hello"))
        bus.publish(self._EventB(7))

        self.assertEqual(["hello", "HELLO"], received_a)
        self.assertEqual([14], received_b)


class _StubWorldRepository:
    def __init__(self) -> None:
        self.saved = []

    def load_default(self):
        return None

    def save(self, world: World) -> None:
        self.saved.append(world)


class _StubEntityRepository:
    pass


class WorldProgressionUnitTests(unittest.TestCase):
    def test_tick_advances_world_and_notifies_listeners(self) -> None:
        world = World(id=1, name="Unit", current_turn=3, rng_seed=5)
        world_repo = _StubWorldRepository()
        entity_repo = _StubEntityRepository()
        bus = EventBus()
        events: list[TickAdvanced] = []
        bus.subscribe(TickAdvanced, lambda event: events.append(event))

        progression = WorldProgression(world_repo, entity_repo, bus)
        progression.tick(world, ticks=2)

        self.assertEqual(5, world.current_turn)
        self.assertEqual([world], world_repo.saved)
        self.assertEqual(1, len(events))
        self.assertEqual(5, events[0].turn_after)


if __name__ == "__main__":
    unittest.main()
