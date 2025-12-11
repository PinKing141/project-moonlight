import json
from typing import List, Optional

from sqlalchemy import bindparam, text

from rpg.domain.models.character import Character
from rpg.domain.models.entity import Entity
from rpg.domain.models.location import Location
from rpg.domain.models.world import World
from rpg.domain.repositories import CharacterRepository, EntityRepository, LocationRepository, WorldRepository
from .connection import SessionLocal


def _default_stats_for_level(level: int) -> tuple[int, int, int, int]:
    scaled_level = max(level, 1)
    hp = 6 + scaled_level * 3
    attack_min = 1 + scaled_level // 2
    attack_max = 2 + scaled_level
    armor = max(scaled_level // 3, 0)
    return hp, attack_min, attack_max, armor


class MysqlCharacterRepository(CharacterRepository):
    def get(self, character_id: int) -> Optional[Character]:
        with SessionLocal() as session:
            row = session.execute(
                text(
                    """
                    SELECT c.character_id, c.name, c.alive, c.level, c.xp, c.money,
                           c.character_type_id, c.hp_current, c.hp_max,
                           cl.location_id
                    FROM `character` c
                    LEFT JOIN character_location cl ON cl.character_id = c.character_id
                    WHERE c.character_id = :cid
                    """
                ),
                {"cid": character_id},
            ).first()

            if not row:
                return None

            return Character(
                id=row.character_id,
                name=row.name,
                alive=bool(row.alive),
                level=row.level,
                xp=row.xp,
                money=row.money,
                character_type_id=row.character_type_id,
                location_id=row.location_id or 0,
                hp_current=row.hp_current,
                hp_max=row.hp_max,
            )

    def list_all(self) -> List[Character]:
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT c.character_id, c.name, c.alive, c.level, c.xp, c.money,
                           c.character_type_id, c.hp_current, c.hp_max, cl.location_id
                    FROM `character` c
                    LEFT JOIN character_location cl ON cl.character_id = c.character_id
                    ORDER BY c.character_id
                    """
                )
            ).all()

            return [
                Character(
                    id=row.character_id,
                    name=row.name,
                    alive=bool(row.alive),
                    level=row.level,
                    xp=row.xp,
                    money=row.money,
                    character_type_id=row.character_type_id,
                    location_id=row.location_id or 0,
                    hp_current=row.hp_current,
                    hp_max=row.hp_max,
                )
                for row in rows
            ]

    def save(self, character: Character) -> None:
        with SessionLocal() as session:
            session.execute(
                text(
                    """
                    INSERT INTO `character` (character_id, name, alive, level, xp, money, character_type_id, hp_current, hp_max)
                    VALUES (:cid, :name, :alive, :level, :xp, :money, :ctype, :hp_current, :hp_max)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        alive = VALUES(alive),
                        level = VALUES(level),
                        xp = VALUES(xp),
                        money = VALUES(money),
                        character_type_id = VALUES(character_type_id),
                        hp_current = VALUES(hp_current),
                        hp_max = VALUES(hp_max)
                    """
                ),
                {
                    "cid": character.id,
                    "name": character.name,
                    "alive": int(character.alive),
                    "level": character.level,
                    "xp": character.xp,
                    "money": character.money,
                    "ctype": character.character_type_id,
                    "hp_current": character.hp_current,
                    "hp_max": character.hp_max,
                },
            )
            # Upsert location mapping
            session.execute(
                text(
                    """
                    INSERT INTO character_location (character_id, location_id)
                    VALUES (:cid, :loc)
                    ON DUPLICATE KEY UPDATE location_id = VALUES(location_id)
                    """
                ),
                {"cid": character.id, "loc": character.location_id},
            )
            session.commit()

    def find_by_location(self, location_id: int) -> List[Character]:
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT c.character_id, c.name, c.alive, c.level, c.xp, c.money,
                           c.character_type_id, c.hp_current, c.hp_max,
                           cl.location_id
                    FROM `character` c
                    INNER JOIN character_location cl ON cl.character_id = c.character_id
                    WHERE cl.location_id = :loc
                    """
                ),
                {"loc": location_id},
            ).all()

            return [
                Character(
                    id=row.character_id,
                    name=row.name,
                    alive=bool(row.alive),
                    level=row.level,
                    xp=row.xp,
                    money=row.money,
                    character_type_id=row.character_type_id,
                    location_id=row.location_id,
                    hp_current=row.hp_current,
                    hp_max=row.hp_max,
                )
                for row in rows
            ]


class MysqlEntityRepository(EntityRepository):
    def list_for_level(self, target_level: int, tolerance: int = 2) -> List[Entity]:
        lower = target_level - tolerance
        upper = target_level + tolerance
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT entity_id, name, level
                    FROM entity
                    WHERE level BETWEEN :low AND :high
                    """
                ),
                {"low": lower, "high": upper},
            ).all()
            entities: List[Entity] = []
            for row in rows:
                level = row.level or 1
                hp, attack_min, attack_max, armor = _default_stats_for_level(level)
                entities.append(
                    Entity(
                        id=row.entity_id,
                        name=row.name,
                        level=level,
                        hp=hp,
                        attack_min=attack_min,
                        attack_max=attack_max,
                        armor=armor,
                        tags=[],
                    )
                )
            return entities

    def list_by_location(self, location_id: int) -> List[Entity]:
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT e.entity_id, e.name, e.level, e.entity_type_id
                    FROM entity e
                    JOIN entity_location el ON el.entity_id = e.entity_id
                    WHERE el.location_id = :loc
                    """
                ),
                {"loc": location_id},
            ).all()

            entities: List[Entity] = []
            for row in rows:
                level = row.level or 1
                hp, attack_min, attack_max, armor = _default_stats_for_level(level)
                entities.append(
                    Entity(
                        id=row.entity_id,
                        name=row.name,
                        level=level,
                        hp=hp,
                        attack_min=attack_min,
                        attack_max=attack_max,
                        armor=armor,
                        tags=[],
                    )
                )
            return entities

    def get_many(self, entity_ids: List[int]) -> List[Entity]:
        if not entity_ids:
            return []

        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT entity_id, name, level
                    FROM entity
                    WHERE entity_id IN :ids
                    """
                ).bindparams(bindparam("ids", expanding=True)),
                {"ids": entity_ids},
            ).all()

            entities: List[Entity] = []
            for row in rows:
                level = row.level or 1
                hp, attack_min, attack_max, armor = _default_stats_for_level(level)
                entities.append(
                    Entity(
                        id=row.entity_id,
                        name=row.name,
                        level=level,
                        hp=hp,
                        attack_min=attack_min,
                        attack_max=attack_max,
                        armor=armor,
                        tags=[],
                    )
                )
            return entities


class MysqlWorldRepository(WorldRepository):
    def load_default(self) -> Optional[World]:
        with SessionLocal() as session:
            row = session.execute(
                text(
                    """
                    SELECT world_id, name, current_turn, threat_level, flags, 1 as rng_seed
                    FROM world
                    ORDER BY world_id
                    LIMIT 1
                    """
                )
            ).first()
            if not row:
                session.execute(text("INSERT INTO world (name) VALUES ('Default World')"))
                session.commit()
                inserted_id = 1
                return World(
                    id=inserted_id,
                    name="Default World",
                    current_turn=0,
                    threat_level=0,
                    flags={},
                    rng_seed=1,
                )
            flags = json.loads(row.flags) if isinstance(row.flags, str) else (row.flags or {})
            return World(
                id=row.world_id,
                name=row.name,
                current_turn=row.current_turn,
                threat_level=row.threat_level,
                flags=flags if isinstance(flags, dict) else {},
                rng_seed=1,
            )

    def save(self, world: World) -> None:
        with SessionLocal() as session:
            payload_flags = world.flags if isinstance(world.flags, str) else json.dumps(world.flags)
            session.execute(
                text(
                    """
                    UPDATE world
                    SET current_turn = :turn,
                        threat_level = :threat,
                        flags = :flags
                    WHERE world_id = :wid
                    """
                ),
                {"turn": world.current_turn, "threat": world.threat_level, "flags": payload_flags, "wid": world.id},
            )
            session.commit()


class MysqlLocationRepository(LocationRepository):
    def get(self, location_id: int) -> Optional[Location]:
        with SessionLocal() as session:
            row = session.execute(
                text(
                    """
                    SELECT l.location_id, l.x, l.y, p.name AS place_name
                    FROM location l
                    INNER JOIN place p ON p.place_id = l.place_id
                    WHERE l.location_id = :loc
                    """
                ),
                {"loc": location_id},
            ).first()
            if not row:
                return None
            return Location(id=row.location_id, name=row.place_name, base_level=1)

    def list_all(self) -> List[Location]:
        with SessionLocal() as session:
            rows = session.execute(
                text(
                    """
                    SELECT l.location_id, l.x, l.y, p.name AS place_name
                    FROM location l
                    INNER JOIN place p ON p.place_id = l.place_id
                    ORDER BY l.location_id
                    """
                )
            ).all()
            return [Location(id=row.location_id, name=row.place_name, base_level=1) for row in rows]
