# Official Beyond Heroes server

## Player choices

The first game menu offers three ways to play:

| Choice | Characters | Save location | Connection required |
| --- | --- | --- | --- |
| Official Server | Account characters; new characters or one-time copies of existing offline characters | Server database | While playing |
| Offline Play | All existing local characters, plus new offline characters | Original local save slots | No |
| Custom Games | New characters for each new custom room; room characters can be continued when returning | Separate local folder for each room | Between players; LAN works without internet |

Choosing a server does not delete, move or overwrite existing offline saves. Importing copies a
character to an empty official slot. The original remains playable offline. Later offline XP,
items or changes do not replace official progress, and official progress does not change the
offline original. Custom characters cannot be selected for official imports.

Each account has eight official character slots. UserIDs are case insensitive and contain 3–32
letters, numbers or underscores. Passwords contain 12–128 characters. Registration displays a
private recovery code once; save that code to reset a forgotten password. Recovery invalidates
old sign-ins and active play sessions and replaces the recovery code. Passwords and sign-in
tokens are kept only in game memory; the next launch requires sign-in again.

## What is implemented

- A separate Godot process runs the official multiplayer coordinator without a playable host.
- The official server accepts 12 human players; custom games accept 11 guests and their host.
- Official players resume their own map instead of being pulled to a host character's location.
- The existing combat sharing, map-owner handoffs, presence, portals, chat, guild messages and
  personal rewards are available on the official connection. Players can explore different maps.
- The HTTPS service owns accounts, character ownership, revisions, play sessions and durable saves.
- Progress snapshots are saved every five seconds during official play, on XP rewards and on
  existing game save triggers. Manual Save, Main Menu and Quit wait for a server acknowledgement.
- A single account can play one character at a time. Old or concurrent saves cannot silently
  overwrite a newer revision. Retrying a save after a lost reply does not apply it twice.
- Official trades require matching approval from both authenticated character owners. Both
  inventories and gold balances are committed in one SQLite transaction. A disconnect or expired
  approval before commitment changes neither character. A committed trade survives either client
  closing before it receives the receipt.
- Connection loss pauses official gameplay. Failed saves are described as unconfirmed, and the
  player can retry or explicitly discard unconfirmed changes and load the last server save.
- Custom hosts announce themselves on LAN and publish to the shared HTTPS directory when
  reachable. Listings expire after 45 seconds without a heartbeat. No account is required to host
  or play a custom game. Saved custom rooms hosted on this device can be opened with Host Again.
- The HUD shows four detailed party frames and a button for the complete player list. This keeps
  a twelve-player roster from covering the whole screen.

## Current scope

This version is a **trusted friends testing server**. Combat, movement and most gameplay rewards
are still simulated by clients using the game's existing per-map owner system. The service
checks save structure and ownership; it does not recalculate every kill, quest, craft or loot roll.
One-time legacy imports necessarily trust the supplied local progress. Built-in cheats and the
developer panel are unavailable for official characters, but a modified game client could still
invent gameplay rewards. Full server-calculated combat and reward validation require another
engine architecture change before a public competitive release.

The server directory provides addresses, not a UDP relay or automatic router traversal. A listed
custom game still needs a reachable game port. LAN discovery can work while the official service
is offline; the shared internet list needs that service. Character storage is centralized,
but guild/world messages retain their existing peer synchronization behavior; this is not a
persistent MMO world database.

## Set up this PC

**To start the configured server on this PC, double-click `Start Official Server.cmd` in the
project folder.** It confirms the server is online and keeps it running in the background after
you close the window. Double-click `Stop Official Server.cmd` to stop both services and save a
final backup. Start can be clicked again safely; it does not launch duplicate managed servers.
If startup fails, the window stays open with the error and the log folder location.

The commands below are for first-time setup or a foreground PowerShell session:

From the project folder in PowerShell:

```powershell
python -m pip install -r server/requirements.txt
python -m server.setup_server --host 127.0.0.1
& .\server\start_server.ps1
```

Setup runs once. It creates the database directory, a 3072-bit RSA TLS identity, server credentials,
and the public files the game needs to verify this server. It refuses to replace an existing
configuration. The account service requires Python 3.12 or later. The game coordinator uses the
installed Godot 4.7.2 executable; pass a different matching executable with:

```powershell
& .\server\start_server.ps1 -Godot 'C:\Tools\Godot\Godot_v4.7.2-stable_win64.exe'
```

The default account address is `https://127.0.0.1:8443`. The game uses UDP port `24680`.
The database and logs are inside `server/data`. Both processes stay running until you stop the
launcher with Ctrl+C, a process fails, or the PC shuts down. The launcher stops both services
and creates a verified backup when it exits normally. There is no scheduled startup or Windows
service installation yet; start the launcher again after rebooting.

**This checkout already has a generated local testing configuration.** Run the launcher directly;
do not run setup again. Generated configuration and public certificate files are ignored by Git.
Never send `server/data` to players. It contains the private TLS key, internal server key, account
hashes, recovery-code hashes and character database. Share a client game build and, when needed,
only the public `.crt` file.

## Friends on LAN or Radmin VPN

### Desktop controls on this PC

The desktop now contains **Start Beyond Heroes Server**, **Stop Beyond Heroes Server** and
**Play Beyond Heroes** shortcuts. Start runs both services in the background without a terminal.
Repeated clicks do not launch duplicate managed servers. Stop shuts down both services and makes
a final verified backup. It does not close the game editor or unrelated applications. The server
does not automatically start after rebooting; use the Start shortcut again.

The managed launcher uses `server/data/launcher.pid`, `launcher.lock` and `stop.request` to control
its own instance. Its logs remain in `server/data/logs`. The equivalent commands are:

```powershell
python -m server.control start
python -m server.control status
python -m server.control stop
```

Setup checks confirmed the server heartbeat and verified TLS on localhost, the LAN address and
the Radmin VPN address. These checks were from the host PC; another PC's access still needs a
friends connectivity test. Windows Firewall was not changed in this session. In an administrator
PowerShell window, run the prepared restricted rule script yourself:

```powershell
& 'A:\Python\beyond-heroes\server\allow_friend_connections.ps1'
```

It allows TCP 8443 for this Python/pythonw installation and UDP 24680 for this Godot executable, only on
Ethernet/Radmin interfaces from their local subnets. It does not open router ports or change
Windows Firewall defaults. Friends on other networks should join your Radmin network first.

The generated certificate includes this PC's LAN and VPN IPv4 addresses at setup time. On this PC,
the addresses detected during setup were:

- Home network: `192.168.100.5`
- Radmin VPN: `26.192.28.40`

In the game's **Server Settings**, each player enters the route they can actually reach:
`https://192.168.100.5:8443` on your LAN, or `https://26.192.28.40:8443` on the same Radmin network.
The game connection uses that same host address and the game port announced by the service.
These addresses can change; check the current adapter address before sharing it.

Players use the public certificate bundled with your new game build. If using another build, copy
`server/data/server.crt` to a public location on their device and select it with Choose Certificate
File. Do not select or send `server.key`. The game verifies certificate trust and the address;
there is no option to disable verification. A blank certificate path uses the operating engine's
standard public certificate authorities for a properly certified public hostname.

Allow inbound **TCP 8443** for accounts and saves and **UDP 24680** for the game on the network
interface you intend friends to use. This change has not opened firewall or router ports for you.
An administrator can create appropriate Windows Firewall rules; restrict the rules to the
intended LAN/VPN where possible. A LAN/VPN does not require public router forwarding.

For public internet testing, use a reachable hostname/address, a certificate for that name, and
forward both service ports if your connection supports inbound traffic. An ISP using carrier
grade NAT may require a VPN or UDP relay. A publicly reachable address alone does not make this
trusted testing implementation suitable for an untrusted public player base.

## New builds

Before sharing a client build, include `server/*.cfg,server/*.crt` in each Godot export preset's
non-resource include filter. The active Windows and Android presets in this checkout are set
up to include these generated public files. The private server configuration sits outside
the Godot project and is never part of a client export.

The bundled default endpoint remains local testing. Friends can change it in Server Settings;
for a shared default, edit the **public** `game/server/official.cfg` URL before exporting.
The certificate must cover that hostname/IP. Existing version-14 clients cannot connect to
version-15 official or custom rooms; all players need the new build.

## Saving and PC shutdown

The SQLite database uses WAL journaling, full synchronous commits, foreign keys and serialized
write transactions. A successful save reply is sent only after commitment. Shutting down the PC
does not delete committed data. An abrupt shutdown can lose the client's newest changes that
were not yet confirmed; autosaving every five seconds reduces this window but cannot eliminate it.

Your PC must remain running while friends use the official server. When it is off, official
characters remain stored but cannot be played. Offline Play and reachable player-hosted custom
games continue to work without the official server.

## Backups and restore

Verified SQLite backups are made at account-service startup, every 15 minutes, and during normal
launcher shutdown. The newest 14 copies are kept in `server/data/backups`. These are local copies
on the same drive, so copy important backups to a separate drive or your own cloud backup folder.
There is no automatic offsite backup configured.

To create an additional verified backup while the service is running:

```powershell
python -m server.service --backup
```

To restore:

1. Stop both services and close any process using the database.
2. Preserve the current `beyond_heroes.sqlite3`, `beyond_heroes.sqlite3-wal`, and
   `beyond_heroes.sqlite3-shm` together in another folder for recovery.
3. Copy the chosen verified backup to `server/data/beyond_heroes.sqlite3`. Old WAL/SHM files must
   not remain beside the restored database. Keep them with the preserved original, not the restore.
4. Keep `server.json`, `server.key`, and `server.crt` unless deliberately changing the server identity.
5. Restart the launcher. Active play sessions are invalidated; players sign in and load the
   characters stored in that backup. Changes after the backup will be absent.

## Validation

The current Windows client is `build/official-server/windows/BeyondHeroes.exe`. The Android
testing client is `build/official-server/BeyondHeroes-testing.apk`, signed with the debug identity.
A release APK needs your release keystore; none was generated or substituted. Both packages
include the public certificate and client configuration, and exclude private server data.

Checks completed on 2 October 2026:

- Account/database unit tests: 23 tests passed.
- Official capacity, HTTPS, save separation and offline menu/save checks: 6 tests, 29 checks passed.
- Live integration: 12 clients, capacity refusal, restart/resume, shared avatars, atomic trade,
  confirmed exit saves and custom directory hosting passed.
- Launcher startup, HTTPS heartbeat, shutdown and final verified backup passed.
- Windows compiled-package and menu smoke checks passed; Android package contents verified.
- Full game regression: 118,826 checks, 34 failures in the existing balance, BH-017 weapon,
  enemy and inventory overhaul suites. Those suites also failed in earlier baseline logs.
  The full log and report are `output/official-full-tests.log` and `output/official-full-report.json`.

```powershell
python -m unittest server.test_service -v
python -m server.integration_probe --godot 'A:\Installer\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64_console.exe'
```

The integration probe uses an isolated temporary database and different ports; test accounts
never enter the real account database. It connects twelve real Godot clients, rejects a thirteenth,
restarts both services, resumes two complete map/player scenes, verifies shared avatars, performs
an atomic official trade, closes official sessions with confirmed saves, and checks a fresh custom
host and client in the shared directory. Logs are in `output/official-integration`.

Game unit checks cover capacity, HTTPS endpoint restrictions and local save separation. The
existing multiplayer, guild, team loot and cheat suites are also run. Menu screenshots use the
real renderer. Twelve lightweight network clients are not a performance benchmark for twelve
busy combat maps; that still needs a friends playtest under realistic map and latency conditions.

## Implementation references

- [Godot dedicated servers](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_dedicated_servers.html)
- [Godot HTTPS requests](https://docs.godotengine.org/en/stable/classes/class_httprequest.html)
- [Python scrypt](https://docs.python.org/3.13/library/hashlib.html#hashlib.scrypt)
- [SQLite connections and backup API](https://docs.python.org/3/library/sqlite3.html)
