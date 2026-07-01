# Hermes Desktop (Companion Repo)

Docker container + Python sidecar for running a full Linux XFCE desktop
inside Hermes WebUI.

This repo is the **companion implementation** for the
[hermes-desktop extension](https://github.com/hermes-webui/hermes-webui-extensions/tree/main/extensions/hermes-desktop).
The extension entry lives there; this repo holds the Docker image, sidecar
process, and desktop tooling.

## Quick Start

```bash
git clone https://github.com/ChonSong/hermes-desktop
cd hermes-desktop

# Build the Docker image (~2 min first time)
docker compose -f docker/docker-compose.yml build

# Start the sidecar
python3 sidecar/sidecar.py
```

Then install the WebUI extension and click the 🐧 sidebar button.

## What's Inside

```
hermes-desktop/
├── sidecar/
│   └── sidecar.py          # Python async server (health, lifecycle)
├── docker/
│   ├── Dockerfile           # Ubuntu 24.04 + XFCE4 + TigerVNC + noVNC
│   ├── docker-compose.yml   # Single-service, host-only ports
│   └── xfce4-startup.sh     # VNC + websockify + XFCE launcher
└── README.md
```

## Sidecar API

| Endpoint | Method | Description |
|---|---|---|
| `GET /health` | GET | `{"ok":true,"container":"running\|stopped"}` |
| `GET /container/status` | GET | Detailed container state from `docker inspect` |
| `POST /container/start` | POST | Build + start the container (idempotent) |
| `POST /container/stop` | POST | Stop the container |

Default: `http://127.0.0.1:17887`. Override with
`HERMES_DESKTOP_HOST` and `HERMES_DESKTOP_PORT` environment variables.

## Desktop Tools (Pre-installed)

| Tool | Purpose |
|---|---|
| **Chromium** | Web browser |
| **LibreOffice** | Writer, Calc, Impress |
| **Blender** | 3D modeling (install in-container as needed: `apt install blender`) |
| **xdotool** | Mouse/keyboard automation |
| **xclip** | Clipboard access |
| **ImageMagick** | Screenshots (`import -window root`) |
| **Python 3** | Scripting inside the container |

## Agent Integration

The Hermes agent controls the desktop through `docker exec`:

```bash
# Launch terminal
docker exec hermes-desktop xfce4-terminal &

# Click at position  
docker exec hermes-desktop xdotool mousemove 400 300 click 1

# Screenshot → vision analysis
docker exec hermes-desktop import -window root /tmp/shot.png
docker cp hermes-desktop:/tmp/shot.png /tmp/shot.png
```

## Requirements

- **Docker 24+** with Compose plugin
- **Python 3.10+** with `websockets` (`pip install websockets`)
- **Linux host** — the extension iframe loads `localhost:6080`, which works
  when browser and host are on the same machine

## Related

- Extension entry: [hermes-webui/hermes-webui-extensions](https://github.com/hermes-webui/hermes-webui-extensions/tree/main/extensions/hermes-desktop)
- Inspiration: [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero)
