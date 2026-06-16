import argparse
import time
from datetime import datetime, timezone
from typing import Iterator, Tuple

import cv2
import numpy as np

import config
from common_tcp import bytes_to_base64, connect_client, send_json


def encode_frame(frame: np.ndarray) -> str:
    params = [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY]
    success, encoded = cv2.imencode(".jpg", frame, params)
    if not success:
        raise RuntimeError("Could not encode frame as JPEG")
    return bytes_to_base64(encoded.tobytes())


def synthetic_frames(limit: int) -> Iterator[Tuple[int, np.ndarray]]:
    for frame_id in range(limit):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        x = 80 + (frame_id * 8) % 420
        cv2.rectangle(frame, (x, 110), (x + 80, 340), (255, 255, 255), -1)
        cv2.circle(frame, (x + 40, 80), 35, (255, 255, 255), -1)
        cv2.putText(
            frame,
            f"Synthetic frame {frame_id}",
            (20, 440),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        yield frame_id, frame


def camera_frames(source: str, limit: int) -> Iterator[Tuple[int, np.ndarray]]:
    capture_source: object = int(source) if source.isdigit() else source
    capture = cv2.VideoCapture(capture_source)
    if not capture.isOpened():
        print("Camera/video source is unavailable. Falling back to synthetic frames.")
        yield from synthetic_frames(limit)
        return

    frame_id = 0
    try:
        while frame_id < limit:
            success, frame = capture.read()
            if not success:
                break
            yield frame_id, frame
            frame_id += 1
    finally:
        capture.release()


def send_frames(source: str, limit: int, fps: float) -> None:
    delay = 1.0 / fps if fps > 0 else 0.0
    connection = connect_client(config.PROCESSOR_HOST, config.PROCESSOR_PORT)
    print(f"Connected to processor at {config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}")

    try:
        for frame_id, frame in camera_frames(source, limit):
            payload = {
                "type": "frame",
                "camera_id": "camera-01",
                "frame_id": frame_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "image_format": "jpg",
                "image": encode_frame(frame),
            }
            send_json(connection, payload)
            print(f"Sent frame {frame_id}")
            if delay:
                time.sleep(delay)

        send_json(connection, {"type": "end_of_stream"})
        print("Finished sending frames")
    finally:
        connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Camera server: stream frames to processor.")
    parser.add_argument("--source", default=str(config.DEFAULT_CAMERA_INDEX), help="Camera index, video path, or image stream.")
    parser.add_argument("--limit", type=int, default=config.DEFAULT_FRAME_LIMIT, help="Maximum number of frames to send.")
    parser.add_argument("--fps", type=float, default=5.0, help="Send rate.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    send_frames(args.source, args.limit, args.fps)
