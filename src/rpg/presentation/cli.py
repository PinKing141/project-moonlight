from sqlalchemy import text

from rpg.application.services.character_creation_service import CharacterCreationService
from rpg.application.services.event_bus import EventBus
from rpg.application.services.game_service import GameService
from rpg.application.services.world_progression import WorldProgression
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
from rpg.presentation.main_menu import main_menu


PLAYER_ID = 1


def _bootstrap() -> tuple[GameService, CharacterCreationService]:
    try:
        return _bootstrap_mysql()
    except Exception as exc:  # pragma: no cover - safety fallback
        print(f"MySQL bootstrap failed ({exc}); falling back to in-memory state.")
    return _bootstrap_inmemory()


def _bootstrap_inmemory() -> tuple[GameService, CharacterCreationService]:
    event_bus = EventBus()
    world_repo = InMemoryWorldRepository(seed=42)
    char_repo = InMemoryCharacterRepository({})
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

    creation_service = CharacterCreationService(char_repo, location_repo)

    return (
        GameService(
            character_repo=char_repo,
            entity_repo=entity_repo,
            location_repo=location_repo,
            world_repo=world_repo,
            progression=progression,
        ),
        creation_service,
    )
    creation_service = CharacterCreationService(char_repo, location_repo)

    return game_service, creation_service

def _bootstrap_mysql() -> tuple[GameService, CharacterCreationService]:
    event_bus = EventBus()
    world_repo = MysqlWorldRepository()
    char_repo = MysqlCharacterRepository()
    entity_repo = MysqlEntityRepository()
    location_repo = MysqlLocationRepository()
    _ensure_mysql_seed()
    progression = WorldProgression(world_repo, entity_repo, event_bus)

    creation_service = CharacterCreationService(char_repo, location_repo)

    return (
        GameService(
            character_repo=char_repo,
            entity_repo=entity_repo,
            location_repo=location_repo,
            world_repo=world_repo,
            progression=progression,
        ),
        creation_service,
    )
    creation_service = CharacterCreationService(char_repo, location_repo)

    return game_service, creation_service


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
            session.execute(text("INSERT INTO place (name) VALUES (:name)"), {"name": "Starting Town"})
            place_id = session.execute(text("SELECT place_id FROM place LIMIT 1")).scalar()

        location_id = session.execute(text("SELECT location_id FROM location LIMIT 1")).scalar()
        if not location_id:
            session.execute(
                text("INSERT INTO location (x, y, place_id) VALUES (0, 0, :pid)"),
                {"pid": place_id},
            )

        player_type_id = session.execute(
            text("SELECT character_type_id FROM character_type WHERE name = :name LIMIT 1"),
            {"name": "player"},
        ).scalar()
        if not player_type_id:
            session.execute(text("INSERT INTO character_type (name) VALUES ('player')"))

        for class_name in ("fighter", "rogue", "wizard"):
            session.execute(
                text(
                    """
                    INSERT INTO class (name) VALUES (:name)
                    ON DUPLICATE KEY UPDATE name = VALUES(name)
                    """
                ),
                {"name": class_name},
            )

        session.commit()


def main() -> None:
    game, creator = _bootstrap()
    existing = game.character_repo.get(PLAYER_ID)
    player_id = PLAYER_ID

    if existing is None:
        player_id = run_character_creator(creator)

    game_over = False
    while not game_over:
        view = game.get_player_view(player_id)
        print(view)
        choice = input(">>> ")
        result = game.make_choice(player_id, choice)
        for msg in result.messages:
            print(msg)
        game_over = result.game_over


def run_character_creator(character_creation_service: CharacterCreationService) -> int:
    print("=== Character Creation ===")
    name = input("Enter your character's name: ").strip()

    print("Choose a class:")
    print("1) Fighter")
    print("2) Rogue")
    print("3) Wizard")

    choice = input("> ").strip()
    class_map = {"1": "fighter", "2": "rogue", "3": "wizard"}
    class_name = class_map.get(choice, "fighter")

    character = character_creation_service.create_character(name, class_name)

    print(f"\nCreated {character.name}, a level {character.level} {class_name.title()}")
    print(f"HP: {character.hp_current}/{character.hp_max}")
    print(f"Starting at location ID {character.location_id}")
    return character.id or 0


if __name__ == "__main__":
    main()
