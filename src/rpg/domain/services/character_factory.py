from rpg.domain.models.character import Character
from rpg.domain.models.character_class import CharacterClass


HIT_DIE_BASE_HP = {
    "d6": 6,
    "d8": 8,
    "d10": 10,
    "d12": 12,
}


def create_new_character(name: str, cls: CharacterClass) -> Character:
    base_hp = HIT_DIE_BASE_HP.get(cls.hit_die, 8)
    hp_max = base_hp + 2  # small bonus

    return Character(
        id=None,
        name=name,
        level=1,
        xp=0,
        money=0,
        hp_max=hp_max,
        hp_current=hp_max,
        class_name=cls.slug,
        base_attributes={},
        location_id=None,
    )
