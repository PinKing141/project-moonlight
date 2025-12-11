import os
from rpg.application.services.event_bus import EventBus
from rpg.application.services.game_service import GameService
from rpg.application.services.world_progression import WorldProgression
from rpg.infrastructure.inmemory.inmemory_character_repo import InMemoryCharacterRepository
from rpg.infrastructure.inmemory.inmemory_class_repo import InMemoryClassRepository
from rpg.infrastructure.inmemory.inmemory_entity_repo import InMemoryEntityRepository
from rpg.infrastructure.inmemory.inmemory_location_repo import InMemoryLocationRepository
from rpg.infrastructure.inmemory.inmemory_world_repo import InMemoryWorldRepository


def _build_inmemory_game_service() -> GameService:
    char_repo = InMemoryCharacterRepository()
    loc_repo = InMemoryLocationRepository()
    cls_repo = InMemoryClassRepository()
    entity_repo = InMemoryEntityRepository()
    world_repo = InMemoryWorldRepository()

    return GameService(
        char_repo,
        location_repo=loc_repo,
        class_repo=cls_repo,
        entity_repo=entity_repo,
        world_repo=world_repo,
    )


def _build_mysql_game_service():
    # Attempt to hydrate from MySQL when RPG_DATABASE_URL is set
    from rpg.infrastructure.db.mysql.repos import (
        MysqlCharacterRepository,
        MysqlClassRepository,
        MysqlEntityRepository,
        MysqlLocationRepository,
        MysqlWorldRepository,
    )

    char_repo = MysqlCharacterRepository()
    loc_repo = MysqlLocationRepository()
    cls_repo = MysqlClassRepository()
    entity_repo = MysqlEntityRepository()
    world_repo = MysqlWorldRepository()

    event_bus = EventBus()
    progression = WorldProgression(world_repo, entity_repo, event_bus)

    return GameService(
        char_repo,
        location_repo=loc_repo,
        class_repo=cls_repo,
        entity_repo=entity_repo,
        world_repo=world_repo,
        progression=progression,
    )


def create_game_service() -> GameService:
    use_mysql = os.getenv("RPG_DATABASE_URL")
    if use_mysql:
        try:
            return _build_mysql_game_service()
        except Exception as exc:  # pragma: no cover - best-effort fallback
            print(f"MySQL unavailable, falling back to in-memory. Reason: {exc}")

    return _build_inmemory_game_service()
