"""Step 1: webcam + YOLO pose preview with wrist markers and FPS.

Usage:
  uv run python -m yolo_beat.pose_preview                 # live window (q / ESC to quit)
  uv run python -m yolo_beat.pose_preview --seconds 10    # live window, auto close
  uv run python -m yolo_beat.pose_preview --bench 60      # no window, print timing stats
"""
from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

MODEL_PATH = Path("models/yolo11n-pose.pt")
LEFT_WRIST, RIGHT_WRIST = 9, 10  # COCO keypoint indices
WRIST_COLORS = {LEFT_WRIST: (255, 160, 0), RIGHT_WRIST: (0, 200, 255)}  # BGR
CONF_MIN = 0.5


def hand_label(i: int) -> str:
    """User's real hand for a model keypoint index.

    Frames are mirrored before inference, so the model sees the user flipped:
    what it calls the LEFT wrist is the user's RIGHT hand.
    """
    return "R" if i == LEFT_WRIST else "L"


def open_camera(index: int = 0) -> cv2.VideoCapture:
    # MSMF delivers 30 fps on this laptop; DSHOW measured only ~15 fps.
    cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    if not cap.isOpened():
        raise RuntimeError(f"webcam {index} could not be opened")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def load_model() -> YOLO:
    MODEL_PATH.parent.mkdir(exist_ok=True)
    return YOLO(str(MODEL_PATH))


def wrists(result) -> dict[int, tuple[int, int]]:
    """Return {keypoint_index: (x, y)} for confident wrists of the first person."""
    kp = result.keypoints
    if kp is None or kp.xy is None or len(kp.xy) == 0 or kp.conf is None:
        return {}
    xy, conf = kp.xy[0].tolist(), kp.conf[0].tolist()
    return {
        i: (int(xy[i][0]), int(xy[i][1]))
        for i in (LEFT_WRIST, RIGHT_WRIST)
        if conf[i] >= CONF_MIN
    }


def bench(n: int, imgsz: int) -> None:
    model, cap = load_model(), open_camera()
    cap_ms, inf_ms, found = [], [], 0
    try:
        for _ in range(5):  # warm-up
            ok, frame = cap.read()
            model(frame, imgsz=imgsz, verbose=False)
        t_start = time.perf_counter()
        for _ in range(n):
            t0 = time.perf_counter()
            ok, frame = cap.read()
            t1 = time.perf_counter()
            if not ok:
                continue
            res = model(cv2.flip(frame, 1), imgsz=imgsz, verbose=False)[0]
            t2 = time.perf_counter()
            cap_ms.append((t1 - t0) * 1000)
            inf_ms.append((t2 - t1) * 1000)
            found += bool(wrists(res))
        total = time.perf_counter() - t_start
    finally:
        cap.release()
    print(f"imgsz={imgsz} frames={len(inf_ms)}")
    print(f"  capture   mean {statistics.mean(cap_ms):6.1f} ms")
    print(f"  inference mean {statistics.mean(inf_ms):6.1f} ms  "
          f"p90 {statistics.quantiles(inf_ms, n=10)[-1]:6.1f} ms")
    print(f"  end-to-end FPS {len(inf_ms) / total:5.1f}")
    print(f"  frames with a confident wrist: {found}/{len(inf_ms)}")


def live(imgsz: int, seconds: float | None) -> None:
    model, cap = load_model(), open_camera()
    win = "pose preview (q/ESC to quit)"
    t_end = time.perf_counter() + seconds if seconds else None
    fps, t_prev = 0.0, time.perf_counter()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            res = model(frame, imgsz=imgsz, verbose=False)[0]
            for i, (x, y) in wrists(res).items():
                cv2.circle(frame, (x, y), 14, WRIST_COLORS[i], -1)
                cv2.putText(frame, hand_label(i), (x - 6, y + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            now = time.perf_counter()
            fps = 0.9 * fps + 0.1 * (1 / max(now - t_prev, 1e-6))
            t_prev = now
            cv2.putText(frame, f"FPS {fps:4.1f}  imgsz {imgsz}", (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow(win, frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
            if t_end and now > t_end:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--bench", type=int, default=0, help="run N frames without a window")
    p.add_argument("--seconds", type=float, default=None, help="auto close live window")
    a = p.parse_args()
    if a.bench:
        bench(a.bench, a.imgsz)
    else:
        live(a.imgsz, a.seconds)


if __name__ == "__main__":
    main()
