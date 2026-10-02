# Beyond Heroes server

Run `python -m pip install -r server/requirements.txt`, then `python -m server.setup_server` once.
Start both services with `server/start_server.ps1` from PowerShell.

Read [the complete setup, player and backup guide](../docs/OFFICIAL_SERVER.md) before sharing a build with friends.

The server is intended for a trusted friends group. Accounts and saves are protected by HTTPS,
password hashes, character ownership, exclusive sessions and database transactions. Gameplay
still uses the existing map-owner simulation on players' machines. This is not a public,
cheat-resistant, server-simulated game world.
