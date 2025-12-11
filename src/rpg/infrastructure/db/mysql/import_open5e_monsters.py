"""One-off importer to pull Open5e monsters into the MySQL-RPG-Schema.

Usage (example):
    set RPG_DATABASE_URL=mysql+mysqlconnector://user:pass@localhost:3306/rpg_game
    python -m rpg.infrastructure.db.mysql.import_open5e_monsters --pages 2
"""

import argparse
from typing import Dict
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


def import_monsters(pages: int) -> None:
    client = Open5eClient()
    with SessionLocal() as session:
        attr_ids = _attribute_ids(session)
        monster_type_id = _monster_entity_type_id(session)

        for page in range(1, pages + 1):
            payload = client.list_monsters(page=page)
            for monster in payload.get("results", []):
                level = int(float(monster.get("challenge_rating") or 1) * 4)
                ins = session.execute(
                    text(
                        """
                        INSERT INTO entity (entity_type_id, name, level)
                        VALUES (:etype, :name, :level)
                        """
                    ),
                    {
                        "etype": monster_type_id,
                        "name": monster.get("name", "Unknown Monster"),
                        "level": level,
                    },
                )
                entity_id = ins.lastrowid

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
                            """
                        ),
                        {"eid": entity_id, "aid": attribute_id, "val": int(raw)},
                    )
            session.commit()

    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import monsters from Open5e into MySQL")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to import (20 items each)")
    args = parser.parse_args()
    import_monsters(pages=args.pages)


if __name__ == "__main__":
    main()
