"""Step 2 tests: zone geometry and hit (enter) detection.

Expected behaviour (written before implementation):
- Zone.contains: inside True, outside False; left/top edge inclusive, right/bottom exclusive
  (so a point on the shared edge of two adjacent pads belongs to exactly one).
- default_drum_layout: 6 pads, all inside [0, 1], no overlaps, centre column (face/body) free.
- HitDetector:
  * entering a zone -> one hit; staying -> no more hits
  * leaving and re-entering (after cooldown) -> another hit
  * moving A -> B directly -> hit on B
  * short detection dropout (<= grace frames) inside a zone -> no re-trigger
  * long dropout (> grace frames) then reappearing inside the zone -> new hit
  * re-entering the same zone within cooldown -> blocked
  * two wrists entering the same zone in the same frame -> one hit
"""
from yolo_beat.zones import HitDetector, Zone, default_drum_layout

A = Zone("a", 0.0, 0.0, 0.5, 0.5)
B = Zone("b", 0.5, 0.0, 1.0, 0.5)
L, R = 9, 10


def names(hits):
    return [h.zone.name for h in hits]


# ---- Zone -------------------------------------------------------------------

def test_contains_inside_outside():
    assert A.contains(0.25, 0.25)
    assert not A.contains(0.75, 0.25)
    assert not A.contains(0.25, 0.75)


def test_shared_edge_belongs_to_one_zone():
    assert A.contains(0.0, 0.0)          # top-left inclusive
    assert not A.contains(0.5, 0.25)     # right edge exclusive
    assert B.contains(0.5, 0.25)         # ...belongs to B


# ---- Layout -----------------------------------------------------------------

def _overlap(z1, z2):
    return z1.x1 < z2.x2 and z2.x1 < z1.x2 and z1.y1 < z2.y2 and z2.y1 < z1.y2


def test_default_layout_shape():
    zones = default_drum_layout()
    assert len(zones) == 6
    assert len({z.name for z in zones}) == 6
    for z in zones:
        assert 0 <= z.x1 < z.x2 <= 1 and 0 <= z.y1 < z.y2 <= 1
    for i, z1 in enumerate(zones):
        for z2 in zones[i + 1:]:
            assert not _overlap(z1, z2), (z1.name, z2.name)


def test_default_layout_keeps_centre_free():
    for z in default_drum_layout():
        assert not z.contains(0.5, 0.3)
        assert not z.contains(0.5, 0.6)


# ---- HitDetector ------------------------------------------------------------

def make(cooldown=0.1, grace=3):
    return HitDetector([A, B], cooldown_s=cooldown, grace_frames=grace)


def test_enter_once_then_stay():
    d = make()
    assert names(d.update({L: (0.8, 0.8)}, t=0.0)) == []     # outside
    assert names(d.update({L: (0.2, 0.2)}, t=0.1)) == ["a"]  # enter
    assert names(d.update({L: (0.3, 0.3)}, t=0.2)) == []     # stay
    assert names(d.update({L: (0.1, 0.4)}, t=0.3)) == []     # still inside


def test_first_frame_inside_counts_as_enter():
    d = make()
    assert names(d.update({L: (0.2, 0.2)}, t=0.0)) == ["a"]


def test_leave_and_reenter():
    d = make()
    d.update({L: (0.2, 0.2)}, t=0.0)
    d.update({L: (0.2, 0.8)}, t=0.2)
    assert names(d.update({L: (0.2, 0.2)}, t=0.4)) == ["a"]


def test_move_directly_between_zones():
    d = make()
    d.update({L: (0.2, 0.2)}, t=0.0)
    assert names(d.update({L: (0.7, 0.2)}, t=0.2)) == ["b"]


def test_short_dropout_does_not_retrigger():
    d = make(grace=3)
    d.update({L: (0.2, 0.2)}, t=0.0)
    for k in range(3):
        assert names(d.update({}, t=0.1 + k * 0.05)) == []
    assert names(d.update({L: (0.2, 0.2)}, t=0.5)) == []


def test_long_dropout_then_reappear_triggers():
    d = make(grace=3)
    d.update({L: (0.2, 0.2)}, t=0.0)
    for k in range(4):
        d.update({}, t=0.1 + k * 0.05)
    assert names(d.update({L: (0.2, 0.2)}, t=0.5)) == ["a"]


def test_cooldown_blocks_fast_reentry():
    d = make(cooldown=0.1)
    d.update({L: (0.2, 0.2)}, t=0.00)
    d.update({L: (0.2, 0.8)}, t=0.03)
    assert names(d.update({L: (0.2, 0.2)}, t=0.06)) == []    # within 0.1 s
    d.update({L: (0.2, 0.8)}, t=0.08)
    assert names(d.update({L: (0.2, 0.2)}, t=0.25)) == ["a"]  # after cooldown


def test_two_wrists_same_zone_same_frame_one_hit():
    d = make()
    assert names(d.update({L: (0.2, 0.2), R: (0.3, 0.3)}, t=0.0)) == ["a"]


def test_two_wrists_different_zones_two_hits():
    d = make()
    assert sorted(names(d.update({L: (0.2, 0.2), R: (0.7, 0.2)}, t=0.0))) == ["a", "b"]


def test_hit_reports_wrist():
    d = make()
    (hit,) = d.update({R: (0.7, 0.2)}, t=0.0)
    assert hit.wrist == R and hit.zone is B
