
import random

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
        plan, character, world = game_service.explore(char.id)
    except Exception:
        plan = None
        character = char
        world = None

    enemies = plan.enemies if plan else []
    if not enemies:
        print("You find nothing of interest today.")
        input("Press ENTER to continue...")
        return

    if not getattr(game_service, "combat_service", None):
        print("You spot danger but your combat system is not ready yet.")
        input("Press ENTER to continue...")
        return

    player = character
    player_survived = True

    for idx, enemy in enumerate(enemies, start=1):
        intro = random_intro(enemy)
        scene = _generate_scene()
        clear_screen()
        print("=== Encounter ===")
        print(intro)
        verbosity = getattr(getattr(game_service, 'combat_service', None), 'verbosity', 'compact')
        print(_scene_flavour(scene, verbosity=verbosity))
        print(f"Enemy {idx}/{len(encounter)}: {enemy.name} (AC {enemy.armour_class}, HP {enemy.hp_current}/{enemy.hp_max})")
        input("Press ENTER to start combat...")

        result = game_service.combat_service.fight_turn_based(
            player,
            enemy,
            lambda options, p, e, round_no, ctx=None: _choose_combat_action(game_service, options, p, e, round_no, scene),
            scene=scene,
        )
        player = result.player
        game_service.character_repo.save(player)

        clear_screen()
        print("=== Combat Log ===")
        for entry in result.log:
            print(entry.text)
        print("")

        if result.fled:
            print("You escaped the encounter.")
            input("Press ENTER to continue...")
            return

        if not result.player_won:
            player_survived = False
            break

    if player_survived:
        print("You survive the encounter.")
    else:
        print("You black out and wake up later...")
    input("Press ENTER to continue...")


def _choose_combat_action(game_service, options, player, enemy, round_no, scene_ctx=None):
    """Render a simple combat decision menu."""
    combat_service = getattr(game_service, "combat_service", None)
    stats = combat_service.derive_player_stats(player) if combat_service else {}
    rage_rounds = getattr(player, "flags", {}).get("rage_rounds", 0)
    rage_label = "Raging" if rage_rounds else "Ready" if (getattr(player, "class_name", "") == "barbarian") else "—"
    sneak_ready = "Yes" if getattr(player, "class_name", "") == "rogue" else "—"
    slots = getattr(player, "spell_slots_current", 0)
    ac = stats.get("ac", getattr(player, "armour_class", "?"))
    attack_bonus = stats.get("attack_bonus", getattr(player, "attack_bonus", "?"))

    clear_screen()
    print("=== COMBAT ===")
    print(f"Round {round_no}")
    if scene_ctx:
        print(f"Scene: Distance {scene_ctx.get('distance', 'close')} | Terrain {scene_ctx.get('terrain', 'open')}")
        print(f"Surprise: {scene_ctx.get('surprise', 'none')}")
    print("--- You ---")
    print(f"HP {player.hp_current}/{player.hp_max} | AC {ac} | Attack +{attack_bonus} | Slots {slots}")
    print(f"Rage: {rage_label} | Sneak Ready: {sneak_ready}")
    is_dodging = bool(getattr(player, "flags", {}).get("dodging"))
    conditions = "Dodging" if is_dodging else "—"
    print(f"Conditions: {conditions}")
    print("")
    print(f"--- {enemy.name} ---")
    print(f"HP {getattr(enemy, 'hp_current', '?')}/{getattr(enemy, 'hp_max', '?')} | AC {getattr(enemy, 'armour_class', '?')}")
    enemy_intent = getattr(enemy, "intent", None) or "Hostile"
    print(f"Intent: {enemy_intent}")
    print("")
    idx = arrow_menu("Choose your action", options)
    if idx < 0:
        return "Dodge"
    chosen = options[idx]
    if chosen == "Cast Spell":
        spell_slug = _choose_spell(game_service, player)
        return ("Cast Spell", spell_slug)
    return chosen


def _choose_spell(game_service, player):
    spell_repo = getattr(game_service, "spell_repo", None)
    known = getattr(player, "known_spells", []) or []
    if not known:
        clear_screen()
        print("You don't know any spells.")
        input("Press ENTER to continue...")
        return None

    spells_display = []
    slugs: list[str] = []
    slots_available = getattr(player, "spell_slots_current", 0)
    for name in known:
        slug = "".join(ch if ch.isalnum() or ch == " " else "-" for ch in name.lower()).replace(" ", "-")
        spell = spell_repo.get_by_slug(slug) if spell_repo else None
        level = spell.level_int if spell else 0
        range_text = spell.range_text if spell else ""
        needs_slot = level > 0
        playable = (slots_available > 0) if needs_slot else True
        label = f"{name} (Lv {level}{'; ' + range_text if range_text else ''})"
        if needs_slot and not playable:
            label += " [no slots]"
        spells_display.append(label)
        slugs.append(slug)

    choice = arrow_menu("CAST WHICH SPELL?", spells_display)
    if choice < 0:
        return None
    return slugs[choice]


def _generate_scene():
    distance = random.choice(["close", "mid", "far"])
    surprise = random.choice(["none", "player", "enemy"])
    terrain = random.choice(["open", "cramped", "difficult"])
    return {"distance": distance, "surprise": surprise, "terrain": terrain}


def _scene_flavour(scene: dict, verbosity: str = "compact") -> str:
    distance = scene.get("distance", "close")
    surprise = scene.get("surprise", "none")
    terrain = scene.get("terrain", "open")
    dist_line = {
        "close": "The enemy is already upon you.",
        "mid": "You spot movement not far away.",
        "far": "You see danger in the distance.",
    }.get(distance, "")
    surprise_line = {
        "player": "You catch them unaware.",
        "enemy": "You're too late - they strike first.",
        "none": "Both sides see each other at the same time.",
    }.get(surprise, "")
    terrain_line = {
        "open": "The ground is clear and open.",
        "cramped": "The space is tight and cluttered.",
        "difficult": "The ground is uneven and treacherous.",
    }.get(terrain, "")
    lines = [line for line in (dist_line, surprise_line, terrain_line) if line]
    limit = 2 if verbosity == "compact" else (3 if verbosity == "normal" else len(lines))
    return "\n".join(lines[:limit])


