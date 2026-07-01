FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    RESOLUTION=1280x720 \
    VNC_PORT=5900 \
    NOVNC_PORT=6080

# ---- System packages ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    xfce4 xfce4-goodies \
    tigervnc-standalone-server tigervnc-common \
    novnc websockify \
    dbus-x11 x11-xserver-utils x11-utils \
    xdotool xclip imagemagick \
    chromium-browser \
    curl wget ca-certificates \
    sudo supervisor net-tools procps \
    python3 python3-pip \
    libreoffice \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---- noVNC config ----
# noVNC in Ubuntu 24.04 installs to /usr/share/novnc
# websockify bridges WebSocket→TCP (noVNC→VNC server)
RUN ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html 2>/dev/null || true

# ---- Startup script ----
COPY xfce4-startup.sh /usr/local/bin/xfce4-startup.sh
RUN chmod +x /usr/local/bin/xfce4-startup.sh

# ---- Expose ports ----
EXPOSE 5900 6080

CMD ["/usr/local/bin/xfce4-startup.sh"]
