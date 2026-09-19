import select
import sys
import termios
import tty
from typing import Optional


class KeyboardReader:
    """Reads single keypresses from stdin without waiting for ENTER."""

    def __init__(self) -> None:
        self._fd: int = sys.stdin.fileno()
        self._original_settings: Optional[list] = None

    def __enter__(self) -> "KeyboardReader":
        # Save and switch the terminal to cbreak mode.
        self._original_settings = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.restore_terminal()

    def restore_terminal(self) -> None:
        """Restore the terminal settings from before keyboard input started."""
        if self._original_settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._original_settings)

    def get_key(self, timeout: float = 0.1) -> Optional[str]:
        """Return a single character if one is waiting on stdin, otherwise None."""
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            return sys.stdin.read(1)
        return None
