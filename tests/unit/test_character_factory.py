import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rpg.domain.models.character_class import CharacterClass
from rpg.domain.models.character_options import Background, DifficultyPreset, Race
from rpg.domain.services import character_factory


class CharacterFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wizard = CharacterClass(id=1, name="Wizard", slug="wizard", hit_die="d6")
        self.sorcerer = CharacterClass(id=2, name="Sorcerer", slug="sorcerer", hit_die="d6")

    def test_create_character_applies_race_and_difficulty(self) -> None:
        race = Race(name="Elf", bonuses={"int": 2, "WIS": 1}, speed=35, traits=["Fey Ancestry"])
        difficulty = DifficultyPreset(slug="story", name="Story", hp_multiplier=1.5, incoming_damage_multiplier=0.8)
        background = Background(name="Acolyte", faction="church", starting_money=12, proficiencies=["Insight"])

        character = character_factory.create_new_character(
            name="Lyra",
            cls=self.wizard,
            ability_scores={"INT": 15, "dex": 14},
            race=race,
            background=background,
            difficulty=difficulty,
            starting_equipment=["Spellbook"],
        )

        self.assertGreaterEqual(character.hp_max, 12)
        self.assertEqual(35, character.speed)
        self.assertIn("fey ancestry", [trait.lower() for trait in character.race_traits])
        self.assertEqual(17, character.attributes["intelligence"])
        self.assertEqual("church", character.flags.get("faction_affinity"))
        self.assertEqual("story", character.difficulty)
        self.assertIn("Spellbook", character.inventory)

    def test_spell_loadout_matches_class_profile(self) -> None:
        character = character_factory.create_new_character(
            name="Pyra",
            cls=self.sorcerer,
            ability_scores={"CHA": 16},
        )

        self.assertGreaterEqual(character.spell_slots_max, 1)
        self.assertIn("Fire Bolt", character.cantrips)
        self.assertIn("Burning Hands", character.known_spells)


if __name__ == "__main__":
    unittest.main()
