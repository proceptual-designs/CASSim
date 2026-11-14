"""The screen pointer that the keypad's centre key moves like a joystick (FR-DEV-005).

The pointer shows only while it is in use. A press on the centre key arms it; dragging away from
where the press began moves the pointer at a speed that grows with the distance, so a finger held
still off centre keeps it moving. It hides `HIDE` seconds after it last moved. A tap while it shows
is a click at its place; a tap while it is hidden is the key's usual `select`.

Distances on the key are in key widths (1.0 is the width of the centre key), so the feel does not
change with the keypad's scale; the pointer's place is in screen pixels.

The joystick and the hiding are CASSim's own design, chosen on purpose (Simon, 2026-11-14). The
device's touchpad is a touchpad: the pointer moves only while the finger moves, it stays on the
screen until something else happens, and a key press does not hide it (emulator check 6, part P,
`docs/testing/emulator-pointer-results.md`). As there, the pointer stops at the screen edges and
comes back where it was. A later setting could offer the touchpad behaviour beside the joystick.
"""

from __future__ import annotations

from dataclasses import dataclass

HIDE = 1.0  # seconds without movement before the pointer hides
DEAD = 0.1  # key widths of travel that do not move the pointer, so a steady press does not drift
FULL = 1.0  # key widths of travel that give full speed
SPEED = 1.2  # full speed, in screen widths a second
SLOWEST = 0.04  # speed just outside the dead zone, as a share of full speed


@dataclass
class Pointer:
    """Where the pointer is on a screen of `width` by `height` pixels, and whether it shows."""

    width: float = 320.0
    height: float = 200.0
    x: float = -1.0  # -1: not placed yet; it first shows at the centre of the screen
    y: float = -1.0
    visible: bool = False
    held: bool = False
    stick: tuple[float, float] = (0.0, 0.0)  # the finger's travel from where it pressed
    idle: float = 0.0  # seconds since the pointer last moved

    def resize(self, width: float, height: float) -> None:
        """The screen changed size: keep the pointer on it."""
        self.width, self.height = max(width, 1.0), max(height, 1.0)
        if self.x >= 0:
            self.x, self.y = self._clamp(self.x, self.y)

    def press(self) -> None:
        """The finger is down on the centre key and has started to move: show the pointer."""
        if self.x < 0:
            self.x, self.y = self.width / 2, self.height / 2
        self.held = True
        self.visible = True
        self.stick = (0.0, 0.0)
        self.idle = 0.0

    def drag(self, dx: float, dy: float) -> None:
        """The finger is `dx`, `dy` key widths from where it pressed."""
        self.stick = (dx, dy)

    def release(self) -> None:
        """The finger lifted: the pointer stops and starts its wait to hide."""
        self.held = False
        self.stick = (0.0, 0.0)
        self.idle = 0.0

    def hide(self) -> None:
        """Hide at once (a key was pressed, or the page changed)."""
        self.visible = False
        self.held = False
        self.stick = (0.0, 0.0)

    def velocity(self) -> tuple[float, float]:
        """Pixels a second for the present travel: none inside the dead zone, then growing with
        the square of the travel up to full speed."""
        dx, dy = self.stick
        travel = (dx * dx + dy * dy) ** 0.5
        if travel <= DEAD:
            return 0.0, 0.0
        share = min(1.0, (travel - DEAD) / (FULL - DEAD))
        speed = SPEED * self.width * (SLOWEST + (1 - SLOWEST) * share * share)
        return dx / travel * speed, dy / travel * speed

    def step(self, seconds: float) -> bool:
        """Move for `seconds` and age the idle time. Returns whether anything shown changed."""
        if not self.visible:
            return False
        vx, vy = self.velocity()
        x, y = self._clamp(self.x + vx * seconds, self.y + vy * seconds)
        if (x, y) != (self.x, self.y):
            self.x, self.y = x, y
            self.idle = 0.0
            return True
        if self.held and (vx or vy):  # pushing against an edge still counts as use
            self.idle = 0.0
            return False
        self.idle += seconds
        if self.idle >= HIDE and not self.held:
            self.visible = False
            return True
        return False

    def click(self) -> tuple[float, float] | None:
        """A tap on the centre key: the place to click, or None when the pointer is hidden (the
        key then does its usual `select`). A click keeps the pointer showing a while longer."""
        if not self.visible:
            return None
        self.idle = 0.0
        return self.x, self.y

    def _clamp(self, x: float, y: float) -> tuple[float, float]:
        return min(max(x, 0.0), self.width - 1), min(max(y, 0.0), self.height - 1)
