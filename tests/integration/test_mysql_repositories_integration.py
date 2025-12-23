import sys
from pathlib import Path
import unittest
from unittest import mock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rpg.infrastructure.db.mysql import repos as mysql_repos
from rpg.infrastructure.db.mysql.repos import MysqlCharacterRepository, MysqlWorldRepository


def _bootstrap_character_schema(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE character_type (
                    character_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE class (
                    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    open5e_slug TEXT,
                    hit_die TEXT,
                    primary_ability TEXT,
                    source TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE character (
                    character_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    alive INTEGER,
                    level INTEGER,
                    xp INTEGER,
                    money INTEGER,
                    character_type_id INTEGER,
                    hp_current INTEGER,
                    hp_max INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE character_location (
                    character_id INTEGER,
                    location_id INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE character_class (
                    character_id INTEGER,
                    class_id INTEGER
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE attribute (
                    attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE character_attribute (
                    character_id INTEGER,
                    attribute_id INTEGER,
                    value INTEGER
                )
                """
            )
        )


def _bootstrap_world_schema(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE world (
                    world_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    current_turn INTEGER DEFAULT 0,
                    threat_level INTEGER DEFAULT 0,
                    flags TEXT
                )
                """
            )
        )


class MysqlCharacterRepositoryIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", future=True)
        _bootstrap_character_schema(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.session_patcher = mock.patch.object(mysql_repos, "SessionLocal", self.SessionLocal)
        self.session_patcher.start()
        self.repo = MysqlCharacterRepository()

    def tearDown(self) -> None:
        self.session_patcher.stop()
        self.engine.dispose()

    def _seed_character(self) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO attribute (name) VALUES ('strength')"))
            conn.execute(
                text(
                    """
                    INSERT INTO character_type (character_type_id, name)
                    VALUES (1, 'player')
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO class (class_id, name, open5e_slug)
                    VALUES (1, 'Fighter', 'fighter')
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO character (character_id, name, alive, level, xp, money, character_type_id, hp_current, hp_max)
                    VALUES (1, 'Aria', 1, 3, 150, 20, 1, 22, 25)
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO character_location (character_id, location_id)
                    VALUES (1, 7)
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO character_class (character_id, class_id)
                    VALUES (1, 1)
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO character_attribute (character_id, attribute_id, value)
                    VALUES (1, 1, 14)
                    """
                )
            )

    def test_get_returns_character_with_attributes_and_class(self) -> None:
        self._seed_character()

        character = self.repo.get(1)

        self.assertIsNotNone(character)
        self.assertEqual("Aria", character.name)
        self.assertEqual(7, character.location_id)
        self.assertEqual("Fighter", character.class_name)
        self.assertEqual({"strength": 14}, character.attributes)

    def test_find_by_location_filters_results(self) -> None:
        self._seed_character()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO character (character_id, name, alive, level, xp, money, character_type_id, hp_current, hp_max)
                    VALUES (2, 'Scout', 1, 2, 40, 5, 1, 12, 14)
                    """
                )
            )
            conn.execute(
                text("INSERT INTO character_location (character_id, location_id) VALUES (2, 3)")
            )

        at_seven = self.repo.find_by_location(7)
        self.assertEqual(1, len(at_seven))
        self.assertEqual("Aria", at_seven[0].name)


class MysqlWorldRepositoryIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", future=True)
        _bootstrap_world_schema(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.session_patcher = mock.patch.object(mysql_repos, "SessionLocal", self.SessionLocal)
        self.session_patcher.start()
        self.repo = MysqlWorldRepository()

    def tearDown(self) -> None:
        self.session_patcher.stop()
        self.engine.dispose()

    def test_load_default_creates_world_when_empty_and_save_persists_turns(self) -> None:
        world = self.repo.load_default()
        self.assertEqual("Default World", world.name)
        self.assertEqual(0, world.current_turn)

        world.advance_turns(4)
        self.repo.save(world)

        reloaded = self.repo.load_default()
        self.assertEqual(4, reloaded.current_turn)
        self.assertEqual(world.id, reloaded.id)


if __name__ == "__main__":
    unittest.main()
