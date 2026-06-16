import argparse
from datetime import datetime, timezone
from typing import Dict, List

import cv2
import numpy as np

import config
from common_tcp import base64_to_bytes, connect_client, create_server, receive_json_lines, send_json


def decode_frame(payload: Dict[str, object]) -> np.ndarray:
    image_bytes = base64_to_bytes(payload.get("image"))
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode incoming frame")
    return frame


def detect_people(frame: np.ndarray) -> List[Dict[str, float]]:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    boxes, weights = hog.detectMultiScale(
        frame,
        winStride=(8, 8),
        padding=(16, 16),
        scale=1.05,
    )

    detections: List[Dict[str, float]] = []
    for (x, y, width, height), confidence in zip(boxes, weights):
        detections.append(
            {
                "class_name": "person",
                "confidence": round(float(confidence), 4),
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
            }
        )
    return detections


def process_stream() -> None:
    storage_connection = connect_client(config.STORAGE_HOST, config.STORAGE_PORT)
    processor_server = create_server(config.PROCESSOR_HOST, config.PROCESSOR_PORT)
    print(f"Processor listening on {config.PROCESSOR_HOST}:{config.PROCESSOR_PORT}")
    print(f"Connected to storage at {config.STORAGE_HOST}:{config.STORAGE_PORT}")

    camera_connection, camera_address = processor_server.accept()
    print(f"Camera connected from {camera_address}")

    try:
        for payload in receive_json_lines(camera_connection):
            if payload.get("type") == "end_of_stream":
                send_json(storage_connection, {"type": "end_of_stream"})
                print("Received end of stream")
                break

            frame = decode_frame(payload)
            boxes = detect_people(frame)
            result = {
                "type": "detection_result",
                "camera_id": payload.get("camera_id"),
                "frame_id": payload.get("frame_id"),
                "source_timestamp": payload.get("timestamp"),
                "processed_timestamp": datetime.now(timezone.utc).isoformat(),
                "people_count": len(boxes),
                "bounding_boxes": boxes,
                "image_width": int(frame.shape[1]),
                "image_height": int(frame.shape[0]),
            }
            send_json(storage_connection, result)
            print(f"Processed frame {result['frame_id']}: {result['people_count']} people")
    finally:
        camera_connection.close()
        storage_connection.close()
        processor_server.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Processor server: detect people in incoming frames.")
    return parser.parse_args()


if __name__ == "__main__":
    parse_args()
    process_stream()
