"""Step 3 tests: synthesised drum sounds and hand labels (pure functions, no audio device).

Expected behaviour (written before implementation):
- synth_all() returns exactly the 6 pad names of default_drum_layout().
- every sound: float32 1-D array, length = duration * sample rate, not silent,
  peak <= 1.0 (no clipping), loud at the start (attack) and quiet at the end (decay).
- hihat is the shortest, crash the longest.
- to_int16(..., channels=2) gives an int16 (n, 2) C-contiguous array, both channels equal.
- hand_label: the image is mirrored before inference, so the model's LEFT wrist (9)
  is the user's RIGHT hand -> "R", and keypoint 10 -> "L".
"""
import numpy as np

from yolo_beat.pose_preview import LEFT_WRIST, RIGHT_WRIST, hand_label
from yolo_beat.sounds import SAMPLE_RATE, synth_all, to_int16
from yolo_beat.zones import default_drum_layout


def test_one_sound_per_pad():
    assert set(synth_all()) == {z.name for z in default_drum_layout()}


def test_sound_shape_and_levels():
    for name, s in synth_all().items():
        assert s.dtype == np.float32 and s.ndim == 1, name
        assert len(s) > SAMPLE_RATE * 0.03, name
        peak = np.abs(s).max()
        assert 0.3 < peak <= 1.0, (name, peak)
        n = len(s) // 10
        start = np.abs(s[:n]).mean()
        end = np.abs(s[-n:]).mean()
        assert start > 5 * end, (name, start, end)


def test_relative_lengths():
    sounds = synth_all()
    lengths = {k: len(v) for k, v in sounds.items()}
    assert min(lengths, key=lengths.get) == "hihat"
    assert max(lengths, key=lengths.get) == "crash"


def test_to_int16_stereo():
    s = synth_all()["snare"]
    a = to_int16(s, channels=2)
    assert a.dtype == np.int16 and a.shape == (len(s), 2)
    assert a.flags["C_CONTIGUOUS"]
    assert np.array_equal(a[:, 0], a[:, 1])
    assert np.abs(a).max() <= 32767


def test_to_int16_mono():
    s = synth_all()["kick"]
    assert to_int16(s, channels=1).shape == (len(s),)


def test_hand_label_accounts_for_mirror():
    assert hand_label(LEFT_WRIST) == "R"
    assert hand_label(RIGHT_WRIST) == "L"
