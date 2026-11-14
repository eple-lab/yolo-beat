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

    def contains_grown(self, x: float, y: float, margin: float) -> bool:
        """Inside the zone grown on every side by `margin` x its width/height."""
        mx, my = (self.x2 - self.x1) * margin, (self.y2 - self.y1) * margin
        return self.x1 - mx <= x < self.x2 + mx and self.y1 - my <= y < self.y2 + my


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
    wrist: int            # hand id (model wrist keypoint index)
    t: float
    kind: str = "enter"   # "enter": came into the pad, "strike": hit down inside the pad
    speed: float = 0.0    # downward speed (normalised units / s) for strikes


@dataclass
class _HandState:
    zone: Zone | None = None
    missing: int = 0
    prev: tuple[float, float, float] | None = None   # x, y, t of the last frame
    vy: float | None = None                          # downward speed in the last frame
    armed: bool = True                               # may a strike count now?


@dataclass
class HitDetector:
    """Turns hand positions into drum hits.

    Two ways to hit a pad:
    - enter: the hand comes into the pad.
    - strike: a hand already inside moves down fast (vy >= v_min) and then stops or
      bounces back (next vy <= stop_ratio x previous). One stroke gives one hit: after a hit
      the hand must move up (vy <= -v_rearm) before the next strike counts.

    - cooldown_s: minimum time between two hits on the same zone
    - grace_frames: frames a hand may go undetected before its state is forgotten
    - margin: a hand stays in its pad until it leaves the pad grown by this fraction
      (stops jitter on the edge from re-triggering)
    """
    zones: list[Zone]
    cooldown_s: float = 0.12
    grace_frames: int = 3
    margin: float = 0.1
    v_min: float = 1.2      # 0.8 at first; still hands jittered into strikes (eple test, T-28)
    stop_ratio: float = 0.3
    v_rearm: float = 0.5    # 0.3 at first; jitter re-armed too easily
    _hands: dict[int, _HandState] = field(default_factory=dict, init=False)
    _last_hit: dict[str, float] = field(default_factory=dict, init=False)

    def zone_at(self, x: float, y: float) -> Zone | None:
        for z in self.zones:
            if z.contains(x, y):
                return z
        return None

    def update(self, points: dict[int, tuple[float, float]], t: float) -> list[Hit]:
        """points: {hand_id: (x, y)} normalised, only for confidently detected hands."""
        for hid, st in list(self._hands.items()):
            if hid not in points:
                st.missing += 1
                st.prev, st.vy = None, None     # speed restarts after a dropout
                if st.missing > self.grace_frames:
                    del self._hands[hid]

        hits: list[Hit] = []
        for hid, (x, y) in points.items():
            st = self._hands.setdefault(hid, _HandState())
            st.missing = 0
            vy = (y - st.prev[1]) / (t - st.prev[2]) if st.prev and t > st.prev[2] else None

            zone = self.zone_at(x, y)
            if zone is None and st.zone is not None and st.zone.contains_grown(x, y, self.margin):
                zone = st.zone                  # still within the margin: same pad
            entered = zone is not None and zone is not st.zone
            struck = (not entered and zone is not None and st.armed
                      and st.vy is not None and vy is not None
                      and st.vy >= self.v_min and vy <= self.stop_ratio * st.vy)
            speed = st.vy if struck else 0.0
            st.zone, st.prev, st.vy = zone, (x, y, t), vy

            hit = None
            if entered or struck:
                last = self._last_hit.get(zone.name)
                if last is None or t - last >= self.cooldown_s:
                    self._last_hit[zone.name] = t
                    hit = Hit(zone, hid, t, "enter" if entered else "strike", speed)
                    hits.append(hit)
                    st.armed = False
            if hit is None and vy is not None and vy <= -self.v_rearm:
                st.armed = True
        return hits
