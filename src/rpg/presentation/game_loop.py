
from rpg.presentation.menu_controls import arrow_menu, clear_screen
from rpg.application.services.encounter_flavour import random_intro


def run_game_loop(game_service, character_id: int):
    while True:
        char = game_service.character_repo.get(character_id)
        if not char:
            print("Your character could not be found. Returning to the menu.")
            input("Press ENTER to continue...")
            break

        clear_screen()
        print("=== WORLD ===")
        world = getattr(game_service, "world_repo", None)
        world_state = world.load_default() if world else None
        title_bits = []
        if char.race:
            title_bits.append(char.race)
        if char.class_name:
            title_bits.append(char.class_name.title())
        descriptor = " ".join(title_bits) if title_bits else "Adventurer"
        diff_label = getattr(char, "difficulty", "normal")
        world_line = (
            f"Day {world_state.current_turn} – Threat: {getattr(world_state, 'threat_level', 0)}"
            if world_state
            else "Day ? – Threat: ?"
        )
        print(f"{world_line}")
        print(f"{char.name} the {descriptor} | Difficulty: {diff_label.title()} | HP: {char.hp_current}/{char.hp_max}")
        print("")
        choice = arrow_menu("WHAT DO YOU DO?", ["Rest", "Explore", "Quit"])

        if choice == 0:
            try:
                rested_char, _ = game_service.rest(char.id)
                char = rested_char
            except Exception:
                char.hp_current = min(char.hp_current + 4, char.hp_max)
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

    try:
        encounter, character, world = game_service.explore(char.id)
    except Exception:
        encounter = []
        character = char
        world = None

    if not encounter:
        print("You find nothing of interest today.")
        input("Press ENTER to continue...")
        return

    if not getattr(game_service, "combat_service", None):
        print("You spot danger but your combat system is not ready yet.")
        input("Press ENTER to continue...")
        return

    logs = []
    player = character
    player_survived = True

    for idx, enemy in enumerate(encounter, start=1):
        intro = random_intro(enemy)
        logs.append(intro)
        result = game_service.combat_service.fight_simple(player, enemy)
        logs.append(f"--- Enemy {idx}: {enemy.name} ---")
        logs.extend(entry.text for entry in result.log)
        player = result.player
        if not result.player_won:
            player_survived = False
            break

    player.alive = player.hp_current > 0
    game_service.character_repo.save(player)

    clear_screen()
    print("=== Encounter ===")
    for line in logs:
        print(line)
    print("")
    if player_survived:
        print("You survive the encounter.")
    else:
        print("You black out and wake up later...")
    input("Press ENTER to continue...")
