from sqlalchemy import text

from rpg.application.services.event_bus import EventBus
from rpg.application.services.game_service import GameService
from rpg.application.services.world_progression import WorldProgression
from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity
from rpg.domain.models.location import EncounterTableEntry, Location
from rpg.infrastructure.db.inmemory.repos import (
    InMemoryCharacterRepository,
    InMemoryEntityRepository,
    InMemoryLocationRepository,
    InMemoryWorldRepository,
)
from rpg.infrastructure.db.mysql.connection import SessionLocal
from rpg.infrastructure.db.mysql.repos import (
    MysqlCharacterRepository,
    MysqlEntityRepository,
    MysqlLocationRepository,
    MysqlWorldRepository,
)


PLAYER_ID = 1


def _bootstrap() -> GameService:
    try:
        return _bootstrap_mysql()
    except Exception as exc:  # pragma: no cover - safety fallback
        print(f"MySQL bootstrap failed ({exc}); falling back to in-memory state.")
    return _bootstrap_inmemory()


def _bootstrap_inmemory() -> GameService:
    event_bus = EventBus()
    world_repo = InMemoryWorldRepository(seed=42)
    char_repo = InMemoryCharacterRepository(
        {
            PLAYER_ID: Character(
                id=PLAYER_ID,
                name="Aria",
                hp_current=12,
                hp_max=12,
                location_id=1,
                armor=1,
                attack_min=2,
                attack_max=5,
                attributes={"might": 2, "agility": 2, "wit": 1, "spirit": 1},
                faction_id="wardens",
            )
        }
    )
    entity_repo = InMemoryEntityRepository(
        [
            Entity(
                id=1,
                name="Goblin Skirmisher",
                level=1,
                hp=8,
                attack_min=1,
                attack_max=4,
                armor=0,
                faction_id="mire_clan",
                tags=["raider", "skirmisher"],
                traits=["cowardly"],
                loot_tags=["scrap", "coin"],
            ),
            Entity(
                id=2,
                name="Dire Rat",
                level=1,
                hp=6,
                attack_min=1,
                attack_max=3,
                armor=0,
                faction_id="vermin_swarm",
                tags=["beast", "disease"],
                traits=["pack"],
                loot_tags=["pelt"],
            ),
            Entity(
                id=3,
                name="Cult Adept",
                level=2,
                hp=10,
                attack_min=2,
                attack_max=5,
                armor=1,
                faction_id="ashen_court",
                tags=["cult", "caster"],
                traits=["fanatic"],
                loot_tags=["relic", "ritual notes"],
            ),
        ]
    )
    entity_repo.set_location_entities(1, [1, 2, 3])
    location_repo = InMemoryLocationRepository(
        {
            1: Location(
                id=1,
                name="Old Ruins",
                base_level=1,
                recommended_level=1,
                biome="crumbling keep",
                factions=["ashen_court", "mire_clan"],
                tags=["ancient", "damp", "echoing"],
                encounters=[
                    EncounterTableEntry(entity_id=1, weight=4, max_level=3, tags=["raider"]),
                    EncounterTableEntry(entity_id=2, weight=3, max_level=2, tags=["beast"]),
                    EncounterTableEntry(entity_id=3, weight=2, min_level=2, max_level=4, faction_bias="ashen_court"),
                ],
            )
        }
    )
    progression = WorldProgression(world_repo, entity_repo, event_bus)

    return GameService(
        character_repo=char_repo,
        entity_repo=entity_repo,
        location_repo=location_repo,
        world_repo=world_repo,
        progression=progression,
    )


def _bootstrap_mysql() -> GameService:
    event_bus = EventBus()
    world_repo = MysqlWorldRepository()
    char_repo = MysqlCharacterRepository()
    entity_repo = MysqlEntityRepository()
    location_repo = MysqlLocationRepository()
    _ensure_mysql_seed()
    progression = WorldProgression(world_repo, entity_repo, event_bus)

    return GameService(
        character_repo=char_repo,
        entity_repo=entity_repo,
        location_repo=location_repo,
        world_repo=world_repo,
        progression=progression,
    )


def _ensure_mysql_seed() -> None:
    """Ensure minimal data exists for the CLI to run against MySQL."""
    with SessionLocal() as session:
        world_id = session.execute(text("SELECT world_id FROM world LIMIT 1")).scalar()
        if not world_id:
            session.execute(
                text(
                    """
                    INSERT INTO world (name, current_turn, threat_level, flags)
                    VALUES ('Default World', 0, 0, '{}')
                    """
                )
            )

        place_id = session.execute(text("SELECT place_id FROM place LIMIT 1")).scalar()
        if not place_id:
            session.execute(text("INSERT INTO place (name) VALUES (:name)"), {"name": "Old Ruins"})
            place_id = session.execute(text("SELECT place_id FROM place LIMIT 1")).scalar()

        location_id = session.execute(text("SELECT location_id FROM location LIMIT 1")).scalar()
        if not location_id:
            session.execute(
                text("INSERT INTO location (x, y, place_id) VALUES (0, 0, :pid)"),
                {"pid": place_id},
            )
            location_id = session.execute(text("SELECT location_id FROM location LIMIT 1")).scalar()

        player_type_id = session.execute(
            text("SELECT character_type_id FROM character_type WHERE name = :name LIMIT 1"),
            {"name": "player"},
        ).scalar()
        if not player_type_id:
            session.execute(text("INSERT INTO character_type (name) VALUES ('player')"))
            player_type_id = session.execute(
                text("SELECT character_type_id FROM character_type WHERE name = 'player' LIMIT 1")
            ).scalar()

        character_exists = session.execute(
            text("SELECT character_id FROM `character` WHERE character_id = :cid"),
            {"cid": PLAYER_ID},
        ).scalar()
        if not character_exists:
            session.execute(
                text(
                    """
                    INSERT INTO `character` (character_id, character_type_id, name, alive, level, xp, money, hp_current, hp_max)
                    VALUES (:cid, :ctype, :name, 1, 1, 0, 0, 10, 10)
                    """
                ),
                {"cid": PLAYER_ID, "ctype": player_type_id, "name": "Aria"},
            )

        session.execute(
            text(
                """
                INSERT INTO character_location (character_id, location_id)
                VALUES (:cid, :loc)
                ON DUPLICATE KEY UPDATE location_id = VALUES(location_id)
                """
            ),
            {"cid": PLAYER_ID, "loc": location_id},
        )

        session.commit()


def main() -> None:
    game = _bootstrap()
    game_over = False
    while not game_over:
        view = game.get_player_view(PLAYER_ID)
        print(view)
        choice = input(">>> ")
        result = game.make_choice(PLAYER_ID, choice)
        for msg in result.messages:
            print(msg)
        game_over = result.game_over


if __name__ == "__main__":
    main()
