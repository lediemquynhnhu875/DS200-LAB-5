import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import config
from common_tcp import create_server, receive_json_lines


def partition_path(base_dir: str, timestamp: str) -> Path:
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.now(timezone.utc)
    date_part = parsed.date().isoformat()
    return Path(base_dir) / f"date={date_part}" / "results.jsonl"


def append_result(payload: Dict[str, object], base_dir: str) -> Path:
    timestamp = str(payload.get("processed_timestamp") or datetime.now(timezone.utc).isoformat())
    output_path = partition_path(base_dir, timestamp)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return output_path


def run_storage(base_dir: str) -> None:
    server = create_server(config.STORAGE_HOST, config.STORAGE_PORT)
    print(f"Storage listening on {config.STORAGE_HOST}:{config.STORAGE_PORT}")
    connection, address = server.accept()
    print(f"Processor connected from {address}")

    saved = 0
    try:
        for payload in receive_json_lines(connection):
            if payload.get("type") == "end_of_stream":
                print("Received end of stream")
                break

            output_path = append_result(payload, base_dir)
            saved += 1
            print(
                f"Stored frame {payload.get('frame_id')} "
                f"with {payload.get('people_count')} people -> {output_path}"
            )
    finally:
        connection.close()
        server.close()
        print(f"Storage stopped. Saved {saved} records.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Storage server: persist detection results as JSONL.")
    parser.add_argument("--output", default=config.STORAGE_DIR, help="Base directory for partitioned JSONL output.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_storage(args.output)
