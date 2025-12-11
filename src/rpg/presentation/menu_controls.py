import os
import sys

try:  # Windows-specific keyboard handling
    import msvcrt  # type: ignore
except ImportError:  # pragma: no cover - fallback for non-Windows
    msvcrt = None


def clear_screen() -> None:
    """Clear the console in a basic cross-platform way."""

    os.system("cls" if os.name == "nt" else "clear")


def _read_key_windows():
    """Read a single key from the keyboard on Windows using msvcrt."""

    ch = msvcrt.getch()

    if ch in (b"\x00", b"\xe0"):
        ch2 = msvcrt.getch()
        if ch2 == b"H":
            return "UP"
        if ch2 == b"P":
            return "DOWN"
        if ch2 == b"K":
            return "LEFT"
        if ch2 == b"M":
            return "RIGHT"
        return None

    if ch in (b"\r", b"\n"):
        return "ENTER"
    if ch == b"\x1b":
        return "ESC"

    try:
        return ch.decode("utf-8")
    except UnicodeDecodeError:
        return None


def read_key():
    """Read a key, defaulting to simple input when msvcrt is unavailable."""

    if msvcrt is not None:
        return _read_key_windows()

    # Basic fallback: rely on blocking stdin
    return sys.stdin.readline().strip()


def arrow_menu(title: str, options: list[str]) -> int:
    """Render a vertical menu controlled by arrow keys.

    Returns the selected option index, or -1 if the user presses ESC.
    """

    if not options:
        raise ValueError("arrow_menu requires at least one option")

    selected = 0

    while True:
        clear_screen()
        print("=" * 40)
        print(f"{title:^40}")
        print("=" * 40)
        print("")

        for idx, option in enumerate(options):
            prefix = "> " if idx == selected else "  "
            print(f"{prefix}{option}")

        print("")
        print("-" * 40)
        print("Use arrow keys to move, ENTER to select, ESC to cancel.")
        print("-" * 40)

        key = read_key()
        if key == "UP":
            selected = (selected - 1) % len(options)
        elif key == "DOWN":
            selected = (selected + 1) % len(options)
        elif key == "ENTER":
            return selected
        elif key == "ESC":
            return -1
