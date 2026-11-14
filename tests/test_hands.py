"""Fingertip estimate tests.

Expected behaviour (written before implementation):
- fingertip(wrist, elbow, k): extends the forearm (elbow -> wrist) past the wrist by k x its length.
  wrist (0.5, 0.5), elbow (0.5, 0.3), k 0.7 -> (0.5, 0.64). k 0 -> the wrist itself.
- hand_points(xy, conf): for keypoints 9/10 (wrists) with confidence >= 0.5 returns
  {wrist_id: (tip, wrist)}. Elbow of 9 is 7, of 10 is 8.
  * confident elbow -> tip is the extended point
  * elbow below threshold -> tip falls back to the wrist (no guess)
  * wrist below threshold -> that hand is left out
"""
import pytest

from yolo_beat.hands import fingertip, hand_points


def test_fingertip_extends_forearm():
    assert fingertip((0.5, 0.5), (0.5, 0.3), k=0.7) == pytest.approx((0.5, 0.64))
    assert fingertip((0.4, 0.5), (0.2, 0.5), k=0.5) == pytest.approx((0.5, 0.5))


def test_fingertip_k_zero_is_wrist():
    assert fingertip((0.3, 0.6), (0.1, 0.2), k=0.0) == pytest.approx((0.3, 0.6))


def _kps(points: dict[int, tuple[float, float, float]]):
    xy = [(0.0, 0.0)] * 17
    conf = [0.0] * 17
    for i, (x, y, c) in points.items():
        xy[i] = (x, y)
        conf[i] = c
    return xy, conf


def test_hand_points_uses_matching_elbow():
    xy, conf = _kps({7: (100, 100, 0.9), 9: (100, 200, 0.9),     # left elbow / wrist
                     8: (300, 100, 0.9), 10: (300, 150, 0.9)})  # right elbow / wrist
    pts = hand_points(xy, conf, k=0.5)
    assert pts[9][0] == pytest.approx((100, 250))
    assert pts[9][1] == pytest.approx((100, 200))
    assert pts[10][0] == pytest.approx((300, 175))


def test_hand_points_low_conf_elbow_falls_back_to_wrist():
    xy, conf = _kps({7: (100, 100, 0.2), 9: (100, 200, 0.9)})
    pts = hand_points(xy, conf, k=0.7)
    assert pts[9][0] == pytest.approx((100, 200))


def test_hand_points_skips_low_conf_wrist():
    xy, conf = _kps({7: (100, 100, 0.9), 9: (100, 200, 0.3), 10: (300, 150, 0.9)})
    pts = hand_points(xy, conf)
    assert set(pts) == {10}
