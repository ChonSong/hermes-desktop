#!/bin/bash
set -e

# Start TigerVNC server on :1
# We use --SecurityTypes None because this is loopback-only
vncserver :1 \
  -geometry 1280x720 \
  -depth 24 \
  -localhost yes \
  -SecurityTypes None \
  -xstartup /etc/X11/Xsession

echo "[hermes-desktop] VNC server running on :1 (port 5900)"

# Start websockify to bridge WebSocket→VNC TCP
# noVNC clients connect to ws://host:6080 → forwarded to localhost:5900
websockify --web /usr/share/novnc 6080 localhost:5900 &
echo "[hermes-desktop] websockify running on :6080 → :5900"

# Launch XFCE4 desktop
echo "[hermes-desktop] starting XFCE4 desktop..."
startxfce4 &

# Keep the container alive
wait
