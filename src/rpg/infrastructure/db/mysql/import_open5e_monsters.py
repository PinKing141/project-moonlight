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
import re


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


def _cr_to_level(raw) -> int:
    if raw is None:
        return 1
    try:
        if isinstance(raw, str) and "/" in raw:
            num, den = raw.split("/", 1)
            return max(1, int(round(float(num) / float(den))))
        return max(1, int(round(float(raw))))
    except Exception:
        return 1


_TO_HIT_RE = re.compile(r"([+-]\d+)\s*to hit", re.IGNORECASE)
_DICE_RE = re.compile(r"\((\d+d\d+(?:\s*[+-]\s*\d+)?)\)")


def _parse_action_block(actions) -> tuple[Optional[int], Optional[str]]:
    if not actions or not isinstance(actions, list):
        return None, None

    preferred = {"bite", "claw", "slam", "longsword", "shortsword", "dagger", "mace", "spear", "club", "maul", "morningstar", "scimitar", "halberd", "battleaxe", "greatsword", "longbow", "shortbow", "javelin"}
    chosen = None
    for action in actions:
        name = str(action.get("name", "")).lower()
        if name == "multiattack":
            continue
        if name in preferred:
            chosen = action
            break
        if chosen is None:
            chosen = action  # fallback first non-multiattack

    if not chosen:
        return None, None

    desc = chosen.get("desc", "") or ""
    to_hit_match = _TO_HIT_RE.search(desc)
    dice_match = _DICE_RE.search(desc)
    to_hit = int(to_hit_match.group(1)) if to_hit_match else None
    dice = dice_match.group(1).replace(" ", "") if dice_match else None
    return to_hit, dice


def _estimate_from_level(level: int) -> tuple[int, str]:
    if level <= 1:
        return 3, "1d6+1"
    if level <= 4:
        return 5, "1d8+2"
    if level <= 8:
        return 6, "2d6+3"
    if level <= 12:
        return 7, "2d8+4"
    if level <= 16:
        return 8, "3d8+5"
    return 9, "4d8+6"


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
                level = _cr_to_level(monster.get("challenge_rating"))
                name = monster.get("name", "Unknown Monster")
                armor_class = monster.get("armor_class")
                hit_points = monster.get("hit_points")
                kind = str(monster.get("type") or "beast").lower()
                to_hit, dice = _parse_action_block(monster.get("actions"))
                if to_hit is None or not dice:
                    est_hit, est_dice = _estimate_from_level(level)
                    to_hit = to_hit if to_hit is not None else est_hit
                    dice = dice or est_dice

                existing_id = session.execute(
                    text("SELECT entity_id FROM entity WHERE name = :name LIMIT 1"), {"name": name}
                ).scalar()

                if existing_id:
                    entity_id = existing_id
                    session.execute(
                        text(
                            """
                            UPDATE entity
                            SET level = :level,
                                armour_class = :ac,
                                attack_bonus = :atk,
                                damage_dice = :dd,
                                hp_max = :hp,
                                kind = :kind
                            WHERE entity_id = :eid
                            """
                        ),
                        {"level": level, "eid": entity_id, "ac": armor_class, "atk": to_hit, "dd": dice, "hp": hit_points, "kind": kind},
                    )
                else:
                    ins = session.execute(
                        text(
                            """
                            INSERT INTO entity (entity_type_id, name, level, armour_class, attack_bonus, damage_dice, hp_max, kind)
                            VALUES (:etype, :name, :level, :ac, :atk, :dd, :hp, :kind)
                            """
                        ),
                        {"etype": monster_type_id, "name": name, "level": level, "ac": armor_class, "atk": to_hit, "dd": dice, "hp": hit_points, "kind": kind},
                    )
                    entity_id = ins.lastrowid
                    imported += 1

                # Persist AC/HP into attribute table when columns exist (legacy)
                for attr, value in (("armor_class", armor_class), ("hit_points", hit_points)):
                    if value is None:
                        continue
                    attr_id = attr_ids.get(attr)
                    if not attr_id:
                        continue
                    session.execute(
                        text(
                            """
                            INSERT INTO entity_attribute (entity_id, attribute_id, value)
                            VALUES (:eid, :aid, :val)
                            ON DUPLICATE KEY UPDATE value = VALUES(value)
                            """
                        ),
                        {"eid": entity_id, "aid": attr_id, "val": int(value)},
                    )

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
