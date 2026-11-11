"""Body instrument app: webcam pose -> drum pad hits -> synthesised drum sounds.

Usage:
  uv run python -m yolo_beat.app                # q / ESC to quit
  uv run python -m yolo_beat.app --seconds 10   # auto close
"""
from __future__ import annotations

import argparse
import time

import cv2

from yolo_beat.pose_preview import (WRIST_COLORS, hand_label, load_model,
                                      open_camera, wrists)
from yolo_beat.sounds import DrumKit
from yolo_beat.zones import HitDetector, default_drum_layout

FLASH_S = 0.15


def draw_zones(frame, zones, flash_until: dict[str, float], now: float) -> None:
    h, w = frame.shape[:2]
    overlay = frame.copy()
    for z in zones:
        p1 = (int(z.x1 * w), int(z.y1 * h))
        p2 = (int(z.x2 * w), int(z.y2 * h))
        lit = flash_until.get(z.name, 0) > now
        if lit:
            cv2.rectangle(overlay, p1, p2, (0, 255, 255), -1)
        cv2.rectangle(frame, p1, p2, (255, 255, 255), 2)
        cv2.putText(frame, z.name, (p1[0] + 6, p1[1] + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)


def run(imgsz: int, seconds: float | None, mute: bool) -> None:
    model, cap = load_model(), open_camera()
    kit = None if mute else DrumKit()
    zones = default_drum_layout()
    detector = HitDetector(zones)
    flash_until: dict[str, float] = {}
    last_hit_at: dict[str, float] = {}
    win = "body instrument (q/ESC to quit)"
    t_start = time.perf_counter()
    t_end = t_start + seconds if seconds else None
    fps, t_prev, n_hits = 0.0, t_start, 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            res = model(frame, imgsz=imgsz, verbose=False)[0]
            pts_px = wrists(res)
            now = time.perf_counter()
            pts = {i: (x / w, y / h) for i, (x, y) in pts_px.items()}
            for hit in detector.update(pts, now):
                name = hit.zone.name
                if kit:
                    kit.play(name)
                n_hits += 1
                flash_until[name] = now + FLASH_S
                prev = last_hit_at.get(name)
                gap = f"+{(now - prev) * 1000:5.0f} ms since last {name}" if prev else ""
                last_hit_at[name] = now
                print(f"{(now - t_start):7.2f}s  HIT {name:6s} by {hand_label(hit.wrist)}  {gap}",
                      flush=True)

            draw_zones(frame, zones, flash_until, now)
            for i, (x, y) in pts_px.items():
                cv2.circle(frame, (x, y), 12, WRIST_COLORS[i], -1)
            fps = 0.9 * fps + 0.1 * (1 / max(now - t_prev, 1e-6))
            t_prev = now
            cv2.putText(frame, f"FPS {fps:4.1f}", (w // 2 - 50, h - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow(win, frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
            if t_end and now > t_end:
                break
    except KeyboardInterrupt:  # Ctrl+C in the terminal: exit quietly
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if kit:
            kit.close()
        print(f"total hits: {n_hits}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--imgsz", type=int, default=320)
    p.add_argument("--seconds", type=float, default=None)
    p.add_argument("--mute", action="store_true", help="no sound")
    a = p.parse_args()
    run(a.imgsz, a.seconds, a.mute)


if __name__ == "__main__":
    main()
