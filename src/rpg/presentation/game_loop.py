import random

from rpg.presentation.menu_controls import arrow_menu, clear_screen


def run_game_loop(game_service, character_id: int):
    while True:
        char = game_service.character_repo.get(character_id)
        if not char:
            print("Your character could not be found. Returning to the menu.")
            input("Press ENTER to continue...")
            break

        clear_screen()
        print("=== WORLD ===")
        print(f"You stand in the Starting Town. HP: {char.hp_current}/{char.hp_max}")
        print("")
        choice = arrow_menu("WHAT DO YOU DO?", ["Rest", "Explore", "Quit"])

        if choice == 0:
            char.hp_current = char.hp_max
            game_service.character_repo.save(char)
            print("You rest and feel restored.")
            input("Press ENTER to continue...")

        elif choice == 1:
            _run_explore(game_service, char)

        elif choice == 2 or choice == -1:
            break


def _run_explore(game_service, char):
    encounter_service = getattr(game_service, "encounter_service", None)
    clear_screen()
    if not encounter_service:
        print("You wander into the unknown... (encounters coming later)")
        input("Press ENTER to continue...")
        return

    encounter = encounter_service.find_encounter(char.location_id or 0, char.level)
    if encounter is None:
        print("The path is quiet. Nothing stirs.")
        input("Press ENTER to continue...")
        return

    rng = random.Random(char.level + encounter.id)
    player_damage = max(rng.randint(char.attack_min, char.attack_max) - encounter.armor, 1)
    enemy_hp = max(encounter.hp - player_damage, 0)

    enemy_damage = max(rng.randint(encounter.attack_min, encounter.attack_max) - char.armor, 1)
    char.hp_current = max(char.hp_current - enemy_damage, 0)
    game_service.character_repo.save(char)

    print(f"You face a {encounter.name}!")
    print(f"You strike for {player_damage} damage. {encounter.name} has {enemy_hp} HP left.")
    print(f"The {encounter.name} hits back for {enemy_damage}. Your HP is {char.hp_current}/{char.hp_max}.")

    if char.hp_current <= 0:
        print("You have fallen! The adventure ends here.")
    input("Press ENTER to continue...")
