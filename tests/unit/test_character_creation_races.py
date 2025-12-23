import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rpg.application.services.character_creation_service import CharacterCreationService


class _DummyRepo:
    """Minimal stub for repositories not used in these tests."""

    pass


class _FakeRaceClient:
    def __init__(self, pages, should_raise: bool = False):
        self.pages = pages
        self.should_raise = should_raise
        self.calls = []
        self.closed = False

    def list_races(self, page: int = 1) -> dict:
        if self.should_raise:
            raise RuntimeError("boom")
        self.calls.append(page)
        return self.pages.get(page, {"results": []})

    def close(self) -> None:
        self.closed = True


class CharacterCreationRacesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.char_repo = _DummyRepo()
        self.class_repo = _DummyRepo()
        self.location_repo = _DummyRepo()

    def test_merges_open5e_races_and_parses_bonuses(self) -> None:
        client = _FakeRaceClient(
            pages={
                1: {
                    "results": [
                        {
                            "name": "Aarakocra",
                            "speed": "50",
                            "asi": [{"ability": "dex", "value": 2}, {"ability": "wis", "value": 1}],
                            "traits": ["Flight", "Talons"],
                        }
                    ],
                    "next": "has-more",
                },
                2: {
                    "results": [
                        {"name": "Genasi", "speed": 30, "ability_bonuses": {"str": 2}, "asi_desc": "Elemental Heritage"},
                        {"name": "Human", "speed": 30, "asi": "STR +1, DEX +1"},  # duplicate of default should be ignored
                    ],
                    "next": None,
                },
            }
        )

        service = CharacterCreationService(
            self.char_repo, self.class_repo, self.location_repo, open5e_client=client
        )
        races = service.list_races()

        names = [race.name for race in races]
        self.assertIn("Aarakocra", names)
        self.assertIn("Genasi", names)
        # Default races remain and duplicates are not double-added
        self.assertEqual(names.count("Human"), 1)

        aarakocra = next(r for r in races if r.name == "Aarakocra")
        self.assertEqual(50, aarakocra.speed)
        self.assertEqual({"DEX": 2, "WIS": 1}, aarakocra.bonuses)
        self.assertIn("Flight", aarakocra.traits)

        genasi = next(r for r in races if r.name == "Genasi")
        self.assertEqual({"STR": 2}, genasi.bonuses)
        self.assertIn("Elemental Heritage", genasi.traits)

        self.assertTrue(client.closed, "Open5e client should be closed after loading races")
        self.assertEqual([1, 2], client.calls)

    def test_falls_back_to_defaults_when_client_fails(self) -> None:
        client = _FakeRaceClient(pages={}, should_raise=True)

        service = CharacterCreationService(
            self.char_repo, self.class_repo, self.location_repo, open5e_client=client
        )
        races = service.list_races()

        names = {race.name for race in races}
        self.assertIn("Human", names)
        self.assertIn("Elf", names)
        self.assertTrue(client.closed)
        self.assertEqual([], client.calls)


if __name__ == "__main__":
    unittest.main()
