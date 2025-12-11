from rpg.presentation.menu_controls import arrow_menu, clear_screen


def run_game_loop(game_service, character_id: int):
    while True:
        clear_screen()
        print("=== WORLD ===")
        print("You stand in the Starting Town.")
        print("")
        choice = arrow_menu("WHAT DO YOU DO?", [
            "Rest at the inn (heal to full)",
            "Explore the wilds",
            "Quit to main menu",
        ])

        if choice == 0:
            # rest – just pretend for now
            char = game_service.character_repo.get(character_id)
            if char:
                char.hp_current = char.hp_max
                game_service.character_repo.save(char)
            print("You rest and feel restored.")
            input("Press ENTER to continue...")

        elif choice == 1:
            print("You wander into the unknown... (encounters coming later)")
            input("Press ENTER to continue...")

        elif choice == 2 or choice == -1:
            break
