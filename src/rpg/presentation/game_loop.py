from rpg.presentation.menu_controls import clear_screen


def run_game_loop(game_service, character_id: int):
    game_over = False
    while not game_over:
        clear_screen()
        view = game_service.get_player_view(character_id)
        print(view)
        choice = input(">>> ")
        result = game_service.make_choice(character_id, choice)
        clear_screen()
        for msg in result.messages:
            print(msg)
        if not result.game_over:
            input("Press ENTER to continue...")
        game_over = result.game_over
