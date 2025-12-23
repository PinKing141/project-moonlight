import io
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rpg.presentation import cli


class CliFlowTests(unittest.TestCase):
    def test_character_creation_and_quit_flow(self) -> None:
        game, creation_service = cli._bootstrap_inmemory()

        with mock.patch("builtins.input", side_effect=["Asha", "2"]), mock.patch("sys.stdout", new_callable=io.StringIO):
            character_id = cli.run_character_creator(creation_service)

        characters = game.list_characters()
        self.assertTrue(any(char.id == character_id for char in characters))

        with mock.patch("builtins.input", side_effect=["quit"]), mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            cli._run_game_loop(game, character_id)

        transcript = output.getvalue()
        self.assertIn("Turn", transcript)
        self.assertIn("Goodbye.", transcript)


if __name__ == "__main__":
    unittest.main()
