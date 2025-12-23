import random
import time

from rpg.presentation.menu_controls import clear_screen


ATTR_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


def roll_4d6_drop_lowest() -> tuple[int, list[int]]:
    """Roll 4d6, drop the lowest, return (total, rolls)."""
    rolls = [random.randint(1, 6) for _ in range(4)]
    total = sum(rolls) - min(rolls)
    return total, rolls


def _render_dice_row(rolls: list[int], highlight_index: int | None = None) -> str:
    """Render dice like: [4] [2] [6] [3]; parentheses mark dropped die."""
    parts = []
    for i, r in enumerate(rolls):
        face = f"[{r}]"
        if highlight_index is not None and i == highlight_index:
            face = f"({r})"
        parts.append(face)
    return "  ".join(parts)


def _animate_stat_roll(stat_name: str, final_total: int, final_rolls: list[int]) -> None:
    """Show a quick rolling animation then reveal the final result."""
    frames = 12
    sleep_time = 0.05

    for _ in range(frames):
        clear_screen()
        print("=" * 40)
        print(f" ROLLING {stat_name} (4d6, drop lowest) ".center(40))
        print("=" * 40)
        print("")
        fake_rolls = [random.randint(1, 6) for _ in range(4)]
        print("Dice:", _render_dice_row(fake_rolls))
        print("")
        print("Rolling...")
        time.sleep(sleep_time)

    # Final reveal
    clear_screen()
    lowest = min(final_rolls)
    lowest_idx = final_rolls.index(lowest)

    print("=" * 40)
    print(f" {stat_name} RESULT ".center(40))
    print("=" * 40)
    print("")
    print("Final dice: ", _render_dice_row(final_rolls, highlight_index=lowest_idx))
    print(f"(Lowest die ({lowest}) is dropped.)")
    print("")
    print(f"{stat_name} = {final_total}")
    print("")
    input("Press ENTER to continue...")


def roll_attributes_with_animation() -> dict[str, int]:
    """
    Full rolling UI:
      - For each attribute in ATTR_ORDER, show animation
      - Roll 4d6 drop lowest
      - Return a dict like {'STR': 16, 'DEX': 12, ...}
    """
    clear_screen()
    print("=" * 40)
    print(" ATTRIBUTE ROLLING ".center(40))
    print("=" * 40)
    print("")
    print("You will roll 4d6 for each attribute, dropping the lowest die.")
    print("Order: STR, DEX, CON, INT, WIS, CHA.")
    print("")
    input("Press ENTER to begin rolling...")

    results: dict[str, int] = {}

    for stat in ATTR_ORDER:
        total, rolls = roll_4d6_drop_lowest()
        _animate_stat_roll(stat, total, rolls)
        results[stat] = total

    # Summary screen
    clear_screen()
    print("=" * 40)
    print(" FINAL ATTRIBUTE ROLLS ".center(40))
    print("=" * 40)
    print("")
    for stat in ATTR_ORDER:
        print(f"  {stat}: {results[stat]}")
    print("")
    input("Press ENTER to accept these rolls...")

    return results
