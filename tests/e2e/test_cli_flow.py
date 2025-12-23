import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from rpg.presentation import cli


class CLIE2ETests(unittest.TestCase):
    def test_main_menu_character_creation_and_quit(self) -> None:
        game, creator = cli._bootstrap_inmemory()

        with mock.patch("builtins.input", side_effect=["Hero", "1", "quit"]):
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                player_id = cli._main_menu(game, creator)
                cli._run_game_loop(game, player_id)

        output = buffer.getvalue()
        self.assertIsNotNone(player_id)
        self.assertGreater(player_id, 0)
        self.assertIn("MAIN MENU", output)
        self.assertIn("Goodbye.", output)


if __name__ == "__main__":
    unittest.main()
