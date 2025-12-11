from typing import List
from rpg.domain.models.character_class import CharacterClass
from rpg.domain.repositories import ClassRepository


class InMemoryClassRepository(ClassRepository):
    def __init__(self):
        self._classes: List[CharacterClass] = [
            CharacterClass(id=1,  name="Barbarian", slug="barbarian", hit_die="d12", primary_ability="STR"),
            CharacterClass(id=2,  name="Bard",      slug="bard",      hit_die="d8",  primary_ability="CHA"),
            CharacterClass(id=3,  name="Cleric",    slug="cleric",    hit_die="d8",  primary_ability="WIS"),
            CharacterClass(id=4,  name="Druid",     slug="druid",     hit_die="d8",  primary_ability="WIS"),
            CharacterClass(id=5,  name="Fighter",   slug="fighter",   hit_die="d10", primary_ability="STR"),
            CharacterClass(id=6,  name="Monk",      slug="monk",      hit_die="d8",  primary_ability="DEX"),
            CharacterClass(id=7,  name="Paladin",   slug="paladin",   hit_die="d10", primary_ability="STR"),
            CharacterClass(id=8,  name="Ranger",    slug="ranger",    hit_die="d10", primary_ability="DEX"),
            CharacterClass(id=9,  name="Rogue",     slug="rogue",     hit_die="d8",  primary_ability="DEX"),
            CharacterClass(id=10, name="Sorcerer",  slug="sorcerer",  hit_die="d6",  primary_ability="CHA"),
            CharacterClass(id=11, name="Warlock",   slug="warlock",   hit_die="d8",  primary_ability="CHA"),
            CharacterClass(id=12, name="Wizard",    slug="wizard",    hit_die="d6",  primary_ability="INT"),
            CharacterClass(id=13, name="Artificer", slug="artificer", hit_die="d8",  primary_ability="INT"),
        ]

    def list_playable(self) -> List[CharacterClass]:
        return list(self._classes)
