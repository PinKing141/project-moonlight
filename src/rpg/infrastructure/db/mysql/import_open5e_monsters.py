"""One-off importer to pull Open5e monsters into the MySQL-RPG-Schema.

Usage (example):
    set RPG_DATABASE_URL=mysql+mysqlconnector://user:pass@localhost:3306/rpg_game
    python -m rpg.infrastructure.db.mysql.import_open5e_monsters --pages 2
"""

import argparse
from typing import Dict, Optional

from sqlalchemy import text

from rpg.infrastructure.db.mysql.connection import SessionLocal
from rpg.infrastructure.open5e_client import Open5eClient


def _attribute_ids(session) -> Dict[str, int]:
    rows = session.execute(text("SELECT attribute_id, name FROM attribute")).all()
    return {row.name.lower(): row.attribute_id for row in rows}


def _monster_entity_type_id(session) -> int:
    row = session.execute(text("SELECT entity_type_id FROM entity_type WHERE name = 'monster'")).first()
    if row:
        return row.entity_type_id
    result = session.execute(text("INSERT INTO entity_type (name) VALUES ('monster')"))
    session.commit()
    return result.lastrowid


def _default_location(session, explicit_location_id: Optional[int]) -> Optional[int]:
    if explicit_location_id:
        return explicit_location_id
    return session.execute(text("SELECT location_id FROM location ORDER BY location_id LIMIT 1")).scalar()


def import_monsters(pages: int, location_id: Optional[int] = None) -> None:
    client = Open5eClient()
    imported = 0
    attached = 0
    with SessionLocal() as session:
        attr_ids = _attribute_ids(session)
        monster_type_id = _monster_entity_type_id(session)
        target_location_id = _default_location(session, location_id)

        for page in range(1, pages + 1):
            payload = client.list_monsters(page=page)
            for monster in payload.get("results", []):
                level = int(float(monster.get("challenge_rating") or 1) * 4)
                name = monster.get("name", "Unknown Monster")

                existing_id = session.execute(
                    text("SELECT entity_id FROM entity WHERE name = :name LIMIT 1"), {"name": name}
                ).scalar()

                if existing_id:
                    entity_id = existing_id
                    session.execute(
                        text("UPDATE entity SET level = :level WHERE entity_id = :eid"),
                        {"level": level, "eid": entity_id},
                    )
                else:
                    ins = session.execute(
                        text(
                            """
                            INSERT INTO entity (entity_type_id, name, level)
                            VALUES (:etype, :name, :level)
                            """
                        ),
                        {"etype": monster_type_id, "name": name, "level": level},
                    )
                    entity_id = ins.lastrowid
                    imported += 1

                for attr in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
                    raw = monster.get(attr)
                    attribute_id = attr_ids.get(attr)
                    if raw is None or not attribute_id:
                        continue
                    session.execute(
                        text(
                            """
                            INSERT INTO entity_attribute (entity_id, attribute_id, value)
                            VALUES (:eid, :aid, :val)
                            ON DUPLICATE KEY UPDATE value = VALUES(value)
                            """
                        ),
                        {"eid": entity_id, "aid": attribute_id, "val": int(raw)},
                    )

                if target_location_id:
                    session.execute(
                        text(
                            """
                            INSERT INTO entity_location (entity_id, location_id)
                            VALUES (:eid, :loc)
                            ON DUPLICATE KEY UPDATE location_id = VALUES(location_id)
                            """
                        ),
                        {"eid": entity_id, "loc": target_location_id},
                    )
                    attached += 1
            session.commit()

    client.close()
    print(f"Imported {imported} monsters; attached {attached} to location {target_location_id}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import monsters from Open5e into MySQL")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to import (20 items each)")
    parser.add_argument(
        "--location-id",
        type=int,
        default=None,
        help="Location ID to attach monsters to (defaults to the first location)",
    )
    args = parser.parse_args()
    import_monsters(pages=args.pages, location_id=args.location_id)


if __name__ == "__main__":
    main()
