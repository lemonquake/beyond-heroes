# 24/7 Hosting Guide for Godot Multiplayer Games

> **Implemented for Beyond Heroes (bh-034):** follow [FREE_VPS_HOSTING.md](FREE_VPS_HOSTING.md). `python tools/export_server.py`
> makes the headless dedicated-server build of step 1 (visuals stripped, packed with the account service);
> `sudo ./server/deploy/free-vps.sh` on an Oracle Always Free (ARM) or Google e2-micro VM does steps 2-4: firewall (ufw or
> Oracle's iptables, plus the console rules it prints), the systemd services that restart on failure and on boot, and in
> addition HTTPS for accounts through Caddy with a free host name (sslip.io or DuckDNS). The game starts in server mode
> with `--official-server=<config>` (game/src/main.gd), on UDP 24680 rather than 7777, for twelve players.

Godot does not offer official hosting servers. Because Godot is an open-source engine, running an online game 24/7 requires deploying a **headless dedicated server build** to a remote Virtual Private Server (VPS), container service, or changing your network model to peer-to-peer (P2P).

## 1. Hosting Architecture Overview

| **Approach** | **Best Free / Low-Cost Providers** | **Strengths** | **Drawbacks** | 
| **Cloud VPS (Dedicated)** | **Oracle Cloud Always Free** (4 OCPU ARM, 24 GB RAM)  **Google Cloud Platform Free Tier** (`e2-micro`, 1 GB RAM) | Full control; supports standard UDP/`ENetMultiplayerPeer`; persistent game world | Requires basic Linux and command-line management | 
| **Game Server BaaS** | **Edgegap**, **Hathora** | Built-in container orchestration, on-demand matchmaking, low latency | Limited free quotas; requires containerizing (Docker) | 
| **Peer-to-Peer (Relay)** | **Steamworks P2P (GodotSteam)**, **WebRTC** | Zero server cost; players host sessions themselves; bypasses port forwarding | Requires a player to remain host; vulnerable to host disconnects | 

## 2. Step 1: Export a Headless Dedicated Server in Godot

A dedicated server does not require graphics, audio, or UI. Godot provides native support to strip these systems to save CPU cycles and RAM.

### In Godot 4.x:

1. Open your project in the editor.

2. Go to **Project → Export...**

3. Click **Add...** and choose **Linux**.

4. In the export settings:

   * **Export Mode:** Select `Export as Dedicated Server` (if using Godot 4.1+) or check `Embed PCK`.

   * Under **Binary Format**, select `64-bit`.

5. Export the binary (e.g., `server.x86_64` or `server.arm64` if targeting ARM architecture).

6. Ensure your main scene or startup script detects server mode:

   ```
   extends Node
   
   func _ready():
       # Detect if running in headless/server mode
       if DisplayServer.get_name() == "headless" or OS.has_feature("dedicated_server"):
           start_server()
       else:
           start_client()
   
   func start_server():
       var peer = ENetMultiplayerPeer.new()
       var error = peer.create_server(7777, 32) # Port 7777, max 32 players
       if error != OK:
           print("Failed to bind port: ", error)
           return
       multiplayer.multiplayer_peer = peer
       print("Server online on port 7777")
   
   ```

## 3. Step 2: Set Up an Always-Free Cloud VPS (Oracle Cloud Example)

Oracle Cloud Infrastructure (OCI) provides the most generous permanent free tier:

* **Specs:** Up to 4 ARM Ampere cores and 24 GB RAM (can be partitioned into 1–4 instances).

* **OS:** Ubuntu 22.04 / 24.04 LTS (AArch64).

### 3.1 Install Dependencies & Upload Binary

1. Connect via SSH:

   ```
   ssh -i /path/to/private_key.key ubuntu@<SERVER_PUBLIC_IP>
   
   ```

2. Update packages and install runtime tools:

   ```
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y screen ufw
   
   ```

3. Upload your exported server binary and `.pck` via SFTP or `scp`:

   ```
   scp -i /path/to/key.key server.arm64 server.pck ubuntu@<SERVER_PUBLIC_IP>:~/godot-server/
   
   ```

4. Give executable permissions to the binary:

   ```
   chmod +x ~/godot-server/server.arm64
   
   ```

### 3.2 Configure Firewalls (Crucial Step)

Godot `ENet` uses **UDP**. You must open the port in two places:

1. **Host Firewall (`ufw`):**

   ```
   sudo ufw allow 7777/udp
   sudo ufw reload
   
   ```

2. **Oracle Cloud Ingress Rule (Web Console):**

   * Go to **Networking → Virtual Cloud Networks (VCN)**.

   * Open your VCN and click **Security Lists → Default Security List**.

   * Click **Add Ingress Rules**:

     * **Source CIDR:** `0.0.0.0/0`

     * **IP Protocol:** `UDP`

     * **Destination Port Range:** `7777`

     * **Description:** Godot Game Server Port

## 4. Step 3: Keep the Server Running 24/7

To ensure your game server runs after you close your SSH session and automatically restarts if it crashes or the VM reboots, use a `systemd` service.

1. Create a service file:

   ```
   sudo nano /etc/systemd/system/godot-server.service
   
   ```

2. Add the following configuration (adjust usernames and paths accordingly):

   ```
   [Unit]
   Description=Godot 4 Dedicated Multiplayer Server
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/godot-server
   ExecStart=/home/ubuntu/godot-server/server.arm64 --headless
   Restart=always
   RestartSec=5s
   StandardOutput=journal
   StandardError=journal
   
   [Install]
   WantedBy=multiplayer.target
   
   ```

3. Enable and start the service:

   ```
   sudo systemctl daemon-reload
   sudo systemctl enable godot-server
   sudo systemctl start godot-server
   
   ```

4. Check server status and view live output logs:

   ```
   # Check if running
   sudo systemctl status godot-server
   
   # View live game logs
   journalctl -u godot-server -f
   
   ```

## 5. Alternative: Zero-Port-Forwarding P2P

If maintaining a Linux server is not desirable and your game does not need persistent world data when all players log off:

* **Steamworks P2P (`GodotSteam`):**

  * Uses Steam's internal relay network.

  * NAT punchthrough is handled by Valve's infrastructure; no static IP or port forwarding is required.

* **WebRTC with a Free Signaling Hub:**

  * Host a tiny signaling server on Render, Railway, or Fly.io (free tiers).

  * Direct game data flows peer-to-peer between client browsers or native desktop builds.