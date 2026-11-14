"""Fingertip estimate from COCO pose keypoints.

The pose model has no finger points, so the fingertip is guessed by extending the forearm
(elbow -> wrist) past the wrist. A hand is about 0.7 x the forearm length.
Bending the wrist breaks the guess, but it is close enough to aim at a drum pad.
"""
from __future__ import annotations

Point = tuple[float, float]

LEFT_WRIST, RIGHT_WRIST = 9, 10      # COCO keypoint indices (model's left/right)
ELBOW_OF = {LEFT_WRIST: 7, RIGHT_WRIST: 8}
HAND_RATIO = 0.7
CONF_MIN = 0.5


def fingertip(wrist: Point, elbow: Point, k: float = HAND_RATIO) -> Point:
    wx, wy = wrist
    ex, ey = elbow
    return wx + (wx - ex) * k, wy + (wy - ey) * k


def hand_points(xy, conf, k: float = HAND_RATIO,
                conf_min: float = CONF_MIN) -> dict[int, tuple[Point, Point]]:
    """{wrist_id: (tip, wrist)} for confident wrists; tip falls back to the wrist
    when the elbow is not confident."""
    out = {}
    for w, e in ELBOW_OF.items():
        if conf[w] < conf_min:
            continue
        wrist = (float(xy[w][0]), float(xy[w][1]))
        if conf[e] >= conf_min:
            tip = fingertip(wrist, (float(xy[e][0]), float(xy[e][1])), k)
        else:
            tip = wrist
        out[w] = (tip, wrist)
    return out
