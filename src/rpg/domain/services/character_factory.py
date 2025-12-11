from copy import deepcopy

from rpg.domain.models.character import Character
from rpg.domain.models.character_class import CharacterClass


DEFAULT_ATTRIBUTES = {
    "strength": 10,
    "constitution": 10,
    "dexterity": 10,
    "intelligence": 10,
    "wisdom": 10,
    "charisma": 10,
    "might": 1,
    "agility": 1,
    "wit": 1,
    "spirit": 1,
}


CLASS_BASE_STATS = {
    "fighter": {"strength": 15, "constitution": 14, "dexterity": 10},
    "rogue": {"strength": 10, "constitution": 12, "dexterity": 15},
    "wizard": {"strength": 8, "constitution": 10, "dexterity": 12, "intelligence": 15},
}


HIT_DIE_HP = {
    "d6": 6,
    "d8": 8,
    "d10": 10,
    "d12": 12,
}


def create_new_character(name: str, character_class: CharacterClass) -> Character:
    slug = character_class.slug.lower().strip() or "fighter"
    base_stats = CLASS_BASE_STATS.get(slug, CLASS_BASE_STATS.get("fighter", {}))

    attributes = deepcopy(DEFAULT_ATTRIBUTES)
    attributes.update(base_stats)

    primary_ability = (character_class.primary_ability or "").lower().strip()
    if primary_ability and primary_ability in attributes:
        attributes[primary_ability] = max(attributes[primary_ability], attributes[primary_ability] + 2)

    constitution = attributes.get("constitution", 10)
    hit_die = (character_class.hit_die or "d8").lower()
    base_hp = HIT_DIE_HP.get(hit_die, 8)
    hp = base_hp + constitution // 2

    return Character(
        id=None,
        name=name,
        level=1,
        xp=0,
        money=0,
        hp_max=hp,
        hp_current=hp,
        class_name=slug,
        attributes=attributes,
    )
