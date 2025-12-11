from rpg.domain.models.character import Character

CLASS_BASE_STATS = {
    "fighter": {"strength": 15, "constitution": 14, "dexterity": 10},
    "rogue": {"strength": 10, "constitution": 12, "dexterity": 15},
    "wizard": {"strength": 8, "constitution": 10, "dexterity": 12, "intelligence": 15},
}


def create_new_character(name: str, class_name: str) -> Character:
    class_key = class_name.lower().strip() or "fighter"
    base = CLASS_BASE_STATS.get(class_key, CLASS_BASE_STATS["fighter"])
    constitution = base.get("constitution", 10)
    hp = 10 + constitution // 2

    return Character(
        id=None,
        name=name,
        level=1,
        xp=0,
        money=0,
        hp_max=hp,
        hp_current=hp,
        class_name=class_key,
        attributes=dict(base),
    )
