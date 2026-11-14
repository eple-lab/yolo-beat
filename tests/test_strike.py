"""Boundary margin + strike-inside-the-pad tests.

Expected behaviour (written before implementation):
- Boundary margin: once a hand is in a pad, it counts as still inside until it leaves the pad
  grown by `margin` (fraction of the pad size, default 0.1). Jitter across the edge -> no new hit.
  Leaving beyond the margin and coming back -> a new hit.
- Defaults: v_min 1.2, stop_ratio 0.3, v_rearm 0.5 (normalised units / s).
- Strike inside a pad: a hand already inside a pad that moves DOWN fast (vy >= v_min) and then
  stops or bounces back (next vy <= stop_ratio x previous vy) -> one hit, kind "strike".
  * slow downward move then stop -> no hit
  * one stroke = one hit: entering a pad fast and stopping in it gives only the enter hit;
    the hand must move UP (vy <= -v_rearm) before the next strike can count
  * a stop outside every pad -> no hit
  * small jitter (about 0.005 per frame) -> no hit
  * after a detection dropout the speed history restarts, so the jump is not a strike
- Hit.kind is "enter" or "strike"; Hit.speed is the downward speed for strikes.
"""
from yolo_beat.zones import HitDetector, Zone

P = Zone("p", 0.1, 0.1, 0.4, 0.4)   # alone, size 0.3 -> margin 0.03
H = 9
DT = 0.08                            # about 12 fps


def make(**kw):
    kw.setdefault("cooldown_s", 0.12)
    return HitDetector([P], **kw)


def run(d, ys, x=0.2, t0=0.0):
    """Feed one y per frame; return [(frame index, kind)] of hits."""
    out = []
    for k, y in enumerate(ys):
        for h in d.update({H: (x, y)} if y is not None else {}, t=t0 + k * DT):
            out.append((k, h.kind))
    return out


# ---- boundary margin -----------------------------------------------------------

def test_edge_jitter_does_not_retrigger():
    d = make()
    xs = [0.30, 0.39, 0.41, 0.39, 0.42, 0.38, 0.41]     # right edge is 0.40
    hits = []
    for k, x in enumerate(xs):
        hits += d.update({H: (x, 0.2)}, t=k * 0.2)
    assert [h.kind for h in hits] == ["enter"]


def test_leave_beyond_margin_then_return_hits_again():
    d = make()
    hits = []
    for k, x in enumerate([0.30, 0.45, 0.30]):           # 0.45 > 0.40 + 0.03
        hits += d.update({H: (x, 0.2)}, t=k * 0.2)
    assert [h.kind for h in hits] == ["enter", "enter"]


# ---- strike inside the pad -------------------------------------------------------

def test_strike_inside_pad():
    d = make()
    #        enter  up    up    down  down  stop  stay
    ys = [0.20, 0.15, 0.12, 0.22, 0.35, 0.36, 0.36]
    assert run(d, ys) == [(0, "enter"), (5, "strike")]


def test_strike_reports_speed():
    d = make()
    hits = []
    for k, y in enumerate([0.20, 0.15, 0.12, 0.22, 0.35, 0.36]):
        hits += d.update({H: (0.2, y)}, t=k * DT)
    assert hits[-1].kind == "strike"
    assert abs(hits[-1].speed - (0.35 - 0.22) / DT) < 1e-6


def test_bounce_back_counts_as_strike():
    d = make()
    ys = [0.20, 0.15, 0.12, 0.22, 0.35, 0.30]           # down fast, then back up
    assert run(d, ys) == [(0, "enter"), (5, "strike")]


def test_two_strokes_two_strikes():
    d = make()
    ys = [0.20, 0.15, 0.12, 0.22, 0.35, 0.36,          # stroke 1 -> strike at 5
          0.25, 0.15, 0.25, 0.37, 0.37]                # up, then stroke 2 -> strike at 10
    assert run(d, ys) == [(0, "enter"), (5, "strike"), (10, "strike")]


def test_slow_down_then_stop_no_strike():
    d = make()
    ys = [0.20, 0.15, 0.12, 0.14, 0.16, 0.18, 0.18]     # 0.25 /s, below v_min
    assert run(d, ys) == [(0, "enter")]


def test_fast_enter_and_stop_is_one_hit():
    d = make()
    ys = [0.02, 0.05, 0.20, 0.30, 0.31, 0.31]           # from above the pad, enter, stop
    assert run(d, ys) == [(2, "enter")]


def test_no_rearm_without_moving_up():
    d = make()
    ys = [0.20, 0.15, 0.12, 0.22, 0.35, 0.36,          # strike at 5
          0.36, 0.37, 0.38, 0.38]                      # no upward move -> nothing more
    assert run(d, ys) == [(0, "enter"), (5, "strike")]


def test_second_push_down_without_lifting_no_strike():
    d = make()
    ys = [0.16, 0.10, 0.22, 0.23, 0.23, 0.34, 0.35]     # strike at 3, then down again, never up
    assert run(d, ys) == [(0, "enter"), (3, "strike")]


def test_stop_outside_pad_no_strike():
    d = make()
    ys = [0.60, 0.55, 0.52, 0.62, 0.75, 0.76]           # all below the pad
    assert run(d, ys) == []


def test_still_hand_jitter_no_strike():
    """A still hand whose fingertip jitters about 0.07 per frame (0.9 /s) must stay silent."""
    d = make()
    ys = [0.20, 0.16, 0.23, 0.16, 0.23, 0.16, 0.23, 0.16]
    assert run(d, ys) == [(0, "enter")]


def test_small_jitter_no_strike():
    d = make()
    ys = [0.200, 0.195, 0.200, 0.205, 0.200, 0.195, 0.205, 0.200]
    assert run(d, ys) == [(0, "enter")]


def test_dropout_restarts_speed_history():
    d = make(grace_frames=3)
    ys = [0.20, 0.15, 0.12, None, 0.35, 0.36]           # jump 1.44 /s across a dropout, then still
    assert run(d, ys) == [(0, "enter")]


def test_slow_lift_does_not_rearm():
    d = make()
    ys = [0.20, 0.15, 0.12, 0.22, 0.35, 0.36,          # strike at 5
          0.328, 0.296, 0.264,                         # lift at 0.4 /s (below v_rearm 0.5)
          0.37, 0.38]                                  # fast down and stop -> not a new stroke
    assert run(d, ys) == [(0, "enter"), (5, "strike")]
