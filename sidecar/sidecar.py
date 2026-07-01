#!/usr/bin/env python3
"""Hermes Desktop sidecar — manages Docker container lifecycle.

Listens on 127.0.0.1:17887. Provides:
  GET  /health            — sidecar + container status
  POST /container/start   — start the desktop container via docker compose
  POST /container/stop    — stop the desktop container
  GET  /container/status  — container state detail
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

try:
    from websockets.asyncio.server import serve
except ImportError:
    print("Install websockets: pip install websockets")
    sys.exit(1)

HOST = os.environ.get("HERMES_DESKTOP_HOST", "127.0.0.1")
PORT = int(os.environ.get("HERMES_DESKTOP_PORT", "17887"))
COMPOSE_DIR = Path(__file__).resolve().parent.parent / "docker"
COMPOSE_FILE = COMPOSE_DIR / "docker-compose.yml"
CONTAINER_NAME = "hermes-desktop"
VNC_PORT = 5900
NOVNC_PORT = 6080


def _compose(args: list[str]) -> subprocess.CompletedProcess:
    cmd = ["docker", "compose", "-f", str(COMPOSE_FILE)]
    return subprocess.run(cmd + args, capture_output=True, text=True, timeout=120)


def container_status() -> dict:
    """Return the current container state."""
    try:
        r = subprocess.run(
            ["docker", "inspect", CONTAINER_NAME],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0:
            return {"running": False, "state": "not-found"}
        info = json.loads(r.stdout)[0]
        st = info.get("State", {})
        return {
            "running": st.get("Running", False),
            "state": st.get("Status", "unknown"),
            "started_at": st.get("StartedAt", ""),
            "ports": {
                "vnc": VNC_PORT,
                "novnc": NOVNC_PORT,
            }
        }
    except Exception as exc:
        return {"running": False, "state": "error", "error": str(exc)}


def start_container() -> dict:
    """Build and start the desktop container."""
    # Build first (idempotent — fast on repeats)
    r = _compose(["build", "--pull"])
    if r.returncode != 0:
        return {"status": "error", "step": "build", "detail": r.stderr[-200:]}

    # Start
    r = _compose(["up", "-d", "--wait"])
    if r.returncode != 0:
        return {"status": "error", "step": "up", "detail": r.stderr[-200:]}

    # Wait for VNC to be ready
    for _ in range(30):
        cs = container_status()
        if cs["running"]:
            return {"status": "started", "container": cs}
        time.sleep(2)

    return {"status": "error", "detail": "container did not become ready within 60s"}


def stop_container() -> dict:
    """Stop the desktop container."""
    r = _compose(["down", "--timeout", "10"])
    if r.returncode != 0:
        # If the container was removed manually, "down" may fail — just
        # check if it's gone and treat that as success.
        if container_status().get("state") == "not-found":
            return {"status": "stopped"}
        return {"status": "error", "detail": r.stderr[-200:]}
    return {"status": "stopped"}


def build_response(status: int, body: dict) -> bytes:
    """Build a minimal HTTP response."""
    payload = json.dumps(body, indent=2).encode()
    return (
        f"HTTP/1.1 {status} OK\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(payload)}\r\n"
        f"Access-Control-Allow-Origin: *\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode() + payload


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        request = await asyncio.wait_for(reader.read(4096), timeout=10)
    except asyncio.TimeoutError:
        writer.close()
        return

    if not request:
        writer.close()
        return

    line0 = request.split(b"\r\n")[0].decode("utf-8", errors="replace")
    parts = line0.split()
    if len(parts) < 2:
        writer.close()
        return

    method, path = parts[0], parts[1]

    # CORS preflight
    if method == "OPTIONS":
        writer.write(
            b"HTTP/1.1 204 No Content\r\n"
            b"Access-Control-Allow-Origin: *\r\n"
            b"Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
            b"Access-Control-Allow-Headers: Content-Type\r\n"
            b"Connection: close\r\n\r\n"
        )
        await writer.drain()
        writer.close()
        return

    try:
        if method == "GET" and path == "/health":
            cs = container_status()
            body = {
                "ok": True,
                "container": "running" if cs["running"] else "stopped",
                "message": "sidecar running",
                "container_detail": cs,
            }

        elif method == "GET" and path == "/container/status":
            body = container_status()

        elif method == "POST" and path == "/container/start":
            body = start_container()

        elif method == "POST" and path == "/container/stop":
            body = stop_container()

        else:
            body = {"error": "not found", "path": path}
            writer.write(build_response(404, body))
            await writer.drain()
            writer.close()
            return

        writer.write(build_response(200, body))

    except Exception as exc:
        body = {"error": str(exc)}
        writer.write(build_response(500, body))

    await writer.drain()
    writer.close()


async def main():
    print(f"[sidecar] binding {HOST}:{PORT}")
    print(f"[sidecar] compose file: {COMPOSE_FILE}")
    async with serve(handler, HOST, PORT) as server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[sidecar] stopped")
