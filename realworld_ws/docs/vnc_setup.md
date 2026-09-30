# Setting Up a VNC Server on Ubuntu 24.04 (Jetson)

This guide covers installing TigerVNC with an XFCE desktop, making it reachable over the network, and starting it automatically on boot without requiring a display to be connected.

## Prerequisites

- Ubuntu 24.04 (tested on a Jetson device)
- A non-root user account to run the VNC session
- Network access to the machine (know its IP address, e.g. `10.42.0.242`)

## 1. Install TigerVNC and a desktop environment

```bash
sudo apt update
sudo apt install -y tigervnc-standalone-server tigervnc-common xfce4 xfce4-goodies
```

XFCE is used here because it's lightweight and reliable over VNC. GNOME (the default Ubuntu desktop) often fails to start correctly in a VNC session, since it expects a full systemd/dbus login session.

## 2. Set a VNC password

Run as the user who will own the session (not root):

```bash
vncpasswd
```

You'll be prompted for a password, and optionally a separate view-only password.

## 3. Choose a display number

Ubuntu desktops typically already use display `:0` (and sometimes `:1`) for the local physical session. Check what's already in use:

```bash
ls -la /tmp/.X11-unix/
```

Pick a display number that **isn't** listed (e.g. `:5` if only `X0` shows up). This guide uses `:5` (→ VNC port `5905`, since the port is always `5900 + display number`).

## 4. Create the xstartup script

This tells VNC to launch an XFCE session instead of relying on the system default, which is not reliable in a VNC context:

```bash
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4
EOF
chmod +x ~/.vnc/xstartup
```

## 5. Allow network connections

By default, recent TigerVNC packages bind only to `localhost`, which blocks any remote client even if the port is open. Set the following in `~/.vnc/config` (create the file if it doesn't exist):

```bash
cat > ~/.vnc/config << 'EOF'
localhost=0
EOF
```

> **Security note:** `localhost=0` exposes the VNC session — including the login prompt — to your network. VNC's built-in encryption (VncAuth) is weak by modern standards. This is fine on a trusted LAN. If the machine is ever reachable from an untrusted network or the internet, keep `localhost=1` (the default) instead and connect via an SSH tunnel (see the end of this guide).

## 6. Start the VNC server

```bash
vncserver :5 -geometry 1920x1080 -depth 24
```

Confirm it's running:

```bash
vncserver -list
```

## 7. Connect from a client

The server listens on port `5900 + display number` — for display `:5`, that's port **5905**.

**Using Remmina:**
1. Open Remmina → **+** (new connection)
2. Protocol: `VNC`
3. Server: `<jetson-ip>:5905` (e.g. `10.42.0.242:5905`)
4. Connect, then enter the VNC password

**Using any other VNC viewer:** connect to `<jetson-ip>:5905` (or `<jetson-ip>::5905` / `<jetson-ip>:5` depending on the client's syntax).

If the firewall (`ufw`) is active on the Jetson, open the port:

```bash
sudo ufw allow 5905/tcp
```

## 8. (Optional) Start VNC automatically on boot

Create a systemd service so the session survives reboots:

```bash
sudo nano /etc/systemd/system/vncserver@.service
```

```ini
[Unit]
Description=Start TigerVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=jetson
Group=jetson
WorkingDirectory=/home/jetson

PIDFile=/home/jetson/.vnc/%H:%i.pid
ExecStartPre=-/bin/bash -c '/usr/bin/vncserver -kill :%i > /dev/null 2>&1'
ExecStart=/usr/bin/vncserver -depth 24 -geometry 1920x1080 -localhost=0 :%i
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
```

Replace `jetson` with your actual username if different.

Two details worth calling out:

- **`ExecStartPre` is wrapped in `bash -c`.** Systemd doesn't run `ExecStart*` commands through a shell by default, so `>` and `2>&1` would otherwise be passed as literal arguments instead of redirecting output — this causes the pre-start "kill any existing session" step to fail with a control-process error on first boot.
- **`-localhost=0` is passed explicitly on the `ExecStart` line.** Relying solely on `localhost=0` in `~/.vnc/config` isn't reliable when the session is launched by systemd rather than an interactive shell — the config file may not be picked up the same way, silently leaving the server bound to `localhost` only (unreachable from the network). Setting the flag directly on the command line guarantees it takes effect.

Apply the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now vncserver@5.service
```

Check status any time with:

```bash
sudo systemctl status vncserver@5.service
```

Confirm the running process actually has the flag you expect:

```bash
ps aux | grep Xtigervnc
```

You should see `-localhost=0` in the command line — not `-localhost=1`.

## Managing the session

```bash
vncserver -list          # show running sessions
vncserver -kill :5       # stop a session
vncserver :5              # start it again manually
```

## Alternative: secure access via SSH tunnel

Instead of exposing VNC to the network directly (`localhost=0`), you can keep the default `localhost=1` and tunnel the connection through SSH:

```bash
ssh -L 5905:localhost:5905 -N -f jetson@<jetson-ip>
```

Then point your VNC viewer at `localhost:5905` instead of the Jetson's IP. This encrypts the traffic and avoids opening the VNC port to the network at all.