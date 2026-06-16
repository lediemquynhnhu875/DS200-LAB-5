import base64
import json
import socket
from typing import Any, Dict, Generator, Optional


ENCODING = "utf-8"


def create_server(host: str, port: int, backlog: int = 1) -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(backlog)
    return server


def connect_client(host: str, port: int) -> socket.socket:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    return client


def send_json(connection: socket.socket, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode(ENCODING) + b"\n"
    connection.sendall(data)


def receive_json_lines(connection: socket.socket) -> Generator[Dict[str, Any], None, None]:
    buffer = b""
    while True:
        chunk = connection.recv(65536)
        if not chunk:
            break

        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            if line.strip():
                yield json.loads(line.decode(ENCODING))


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode(ENCODING)


def base64_to_bytes(data: Optional[str]) -> bytes:
    if not data:
        return b""
    return base64.b64decode(data.encode(ENCODING))
