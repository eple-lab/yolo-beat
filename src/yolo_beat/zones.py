"""Step 2: drum pad zones and enter-hit detection.

Coordinates are normalised to [0, 1] (x to the right, y downward) so the logic
does not depend on camera resolution.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Zone:
    name: str
    x1: float
    y1: float
    x2: float
    y2: float

    def contains(self, x: float, y: float) -> bool:
        # left/top inclusive, right/bottom exclusive: a shared edge belongs to one zone
        return self.x1 <= x < self.x2 and self.y1 <= y < self.y2


def default_drum_layout() -> list[Zone]:
    """Six pads in two side columns; the centre column (face/body) stays free."""
    lx1, lx2 = 0.02, 0.30
    rx1, rx2 = 0.70, 0.98
    rows = [(0.05, 0.32), (0.34, 0.61), (0.63, 0.90)]
    left = ["crash", "hihat", "snare"]
    right = ["ride", "tom", "kick"]
    zones = []
    for (y1, y2), ln, rn in zip(rows, left, right):
        zones.append(Zone(ln, lx1, y1, lx2, y2))
        zones.append(Zone(rn, rx1, y1, rx2, y2))
    return zones


@dataclass(frozen=True)
class Hit:
    zone: Zone
    wrist: int
    t: float


@dataclass
class _WristState:
    zone: Zone | None = None
    missing: int = 0


@dataclass
class HitDetector:
    """Emits a Hit when a wrist enters a zone (not while it stays inside).

    - cooldown_s: minimum time between two hits on the same zone (stops jitter double-hits)
    - grace_frames: frames a wrist may go undetected before its state is forgotten
    """
    zones: list[Zone]
    cooldown_s: float = 0.12
    grace_frames: int = 3
    _wrists: dict[int, _WristState] = field(default_factory=dict, init=False)
    _last_hit: dict[str, float] = field(default_factory=dict, init=False)

    def zone_at(self, x: float, y: float) -> Zone | None:
        for z in self.zones:
            if z.contains(x, y):
                return z
        return None

    def update(self, points: dict[int, tuple[float, float]], t: float) -> list[Hit]:
        """points: {wrist_id: (x, y)} normalised, only for confidently detected wrists."""
        # forget wrists that have been missing too long
        for wid, st in list(self._wrists.items()):
            if wid not in points:
                st.missing += 1
                if st.missing > self.grace_frames:
                    del self._wrists[wid]

        hits: list[Hit] = []
        for wid, (x, y) in points.items():
            st = self._wrists.setdefault(wid, _WristState())
            st.missing = 0
            zone = self.zone_at(x, y)
            entered = zone is not None and zone is not st.zone
            st.zone = zone
            if not entered:
                continue
            last = self._last_hit.get(zone.name)
            if last is not None and t - last < self.cooldown_s:
                continue
            self._last_hit[zone.name] = t
            hits.append(Hit(zone, wid, t))
        return hits
