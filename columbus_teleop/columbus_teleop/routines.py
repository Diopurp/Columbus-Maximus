import time
from typing import Callable, Dict


class SpecialRoutines:
    """Container for pre-programmed motion sequences."""

    def __init__(
        self,
        set_twist: Callable[[float, float], None],
        get_linear_speed: Callable[[], float],
        get_angular_speed: Callable[[], float],
        logger,
        is_active: Callable[[], bool],
    ) -> None:
        self._set_twist = set_twist
        self._get_linear_speed = get_linear_speed
        self._get_angular_speed = get_angular_speed
        self._logger = logger
        self._is_active = is_active

        # Keys mapped to their corresponding motion routines.
        self.routines: Dict[str, Callable[[], None]] = {
            'o': self.circle,
            'p': self.square,
            'm': self.dance,
        }

    def run(self, key: str) -> bool:
        """Run the routine assigned to the given key."""
        routine = self.routines.get(key)
        if routine is None:
            return False
        self._logger.info(f"Starting routine '{key}'...")
        routine()
        self._stop()
        self._logger.info(f"Routine '{key}' finished. Back to manual control.")
        return True

    def _stop(self) -> None:
        self._set_twist(0.0, 0.0)

    def _hold(self, linear: float, angular: float, duration_sec: float) -> None:
        """Set a velocity and maintain it for the specified duration."""
        self._set_twist(linear, angular)
        end_time = time.monotonic() + duration_sec
        while time.monotonic() < end_time:
            if not self._is_active():
                return
            time.sleep(0.05)

    def circle(self) -> None:
        """Drive in a continuous circle for a few seconds."""
        linear = self._get_linear_speed()
        angular = self._get_angular_speed()
        self._hold(linear, angular, duration_sec=6.0)

    def square(self) -> None:
        """Drive a four-sided square path using timed motion segments."""
        linear = self._get_linear_speed()
        angular = self._get_angular_speed()
        side_duration = 2.0
        turn_duration = (3.14159 / 2.0) / max(angular, 0.1)

        for side in range(4):
            if not self._is_active():
                return
            self._hold(linear, 0.0, side_duration)
            self._hold(0.0, 0.0, 0.2)
            self._hold(0.0, angular, turn_duration)
            self._hold(0.0, 0.0, 0.2)

    def dance(self) -> None:
        """Perform a short sequence of alternating spins and movements."""
        angular = self._get_angular_speed()
        linear = self._get_linear_speed()

        sequence = [
            (0.0, angular),
            (0.0, -angular),
            (0.0, angular),
            (0.0, -angular),
            (linear * 0.5, 0.0),
            (-linear * 0.5, 0.0),
        ]
        for lin, ang in sequence:
            if not self._is_active():
                return
            self._hold(lin, ang, duration_sec=0.6)
