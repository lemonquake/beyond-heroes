# Beyond Heroes server

Run `python -m pip install -r server/requirements.txt`, then `python -m server.setup_server` once.
On Windows, double-click **Start Official Server.cmd** in the project folder to start both
services in the background. You can close its window after it confirms the server is online.
Double-click **Stop Official Server.cmd** to stop both services and save a final backup.
The launchers work regardless of the folder you open them from, and repeated Start clicks do
not launch duplicate managed servers. This PC already has a configuration; do not run setup again.
After a game/server update, use Stop then Start to load the updated code. Start checks the
running server's protocol and game heartbeat before confirming it is online.

For a foreground PowerShell session, use `server/start_server.ps1` instead.

Read [the complete setup, player and backup guide](../docs/OFFICIAL_SERVER.md) before sharing a build with friends.

The server is intended for a trusted friends group. Accounts and saves are protected by HTTPS,
password hashes, character ownership, exclusive sessions and database transactions. Gameplay
still uses the existing map-owner simulation on players' machines. This is not a public,
cheat-resistant, server-simulated game world.
