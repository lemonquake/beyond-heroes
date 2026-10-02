# Beyond Heroes beta testing checklist

This checklist is for the beta. Current multiplayer supports twelve players and uses client map owners for combat; accounts and saves are centralized. A server-hosted coordinator does not make gameplay cheat-resistant.

## Versions and ports

| | |
| --- | --- |
| Game build | shown bottom right on the title screen: "Beta 0.8.0 · online version 16". The online version must match the server's. |
| Accounts and saves | HTTPS. A public server uses TCP 443 on its host name; a home server uses TCP 8443 and a certificate file its owner gives you (Server Settings, Advanced). |
| Game traffic | **UDP 24680**. If you can sign in but cannot join, this port is blocked on your network or the server's firewall: try another network or mobile data. |
| Same-network games | UDP 24680 and 24681 on the local network |
| Version messages | The game says whether your game or the server is older. Update the game, or ask the server owner to update the server. |

## Known limitations of this beta

- Fighting is worked out by the players' own games (the first player on a map runs its monsters). A modified game could invent kills and rewards, so the official server is for a trusted group; do not treat results as competitive.
- Public hosting on a Linux server has been prepared but not yet run on a real machine. Until the owner publishes a host name, the official server is a PC at the owner's home and is online only when that PC is.
- Performance targets (60 FPS at 720p low on a named low-end PC, 30 FPS in efficiency mode on a named low-end Android phone) are targets. Only a fast desktop has been measured; no phone has.
- Windows and Android builds are not yet signed with a release identity that survives store updates. Android installs use the debug identity; installing a build signed differently needs the old one removed first, which erases local saves on that device (official characters are safe on the server).
- In small windows the interface is enlarged automatically; if a screen looks too big or clipped, turn off Settings > Controls > Larger Interface in Small Windows and tell us the window size.

## First session

1. Confirm the build version and source of the download.
2. Start the game and choose PC or Mobile controls. Check readable text, visible buttons and ordinary keyboard/controller/touch navigation.
3. Create an offline character, play the first town and combat area, then save, exit and resume.
4. Check all four classes can move, aim, attack, use skills, pick up items and interact with services.
5. Open inventory, equipment, skills, quests, map, shop and settings. Check no content is clipped and essential information remains readable.
6. Change quality/control settings, reload a map and restart the game. Verify the selected settings and touch targets.

## Multiplayer

1. Use the beta's confirmed hostname and matching client/server version. Register, keep the recovery code private, create an official character and join.
2. Join with another tester. Check presence, chat, movement, monsters, attacks, loot and party indicators.
3. Explore different maps, reunite, and use a Team Portal. Verify players are not moved unexpectedly.
4. Have the map owner leave while another player remains. Check monster state and cleared encounters survive the handoff.
5. Trade with both players approving matching offers. Check cancellation, disconnect before commitment, and recovery of a committed trade.
6. Disconnect from the network, reconnect and reload the last confirmed save. Check the game describes unsaved changes clearly.
7. With the administrator coordinating, test server restart and restoration. Do not stop a live shared server without arranging it.
8. Test full-server and different-version messages. For a custom room, verify separate characters, host/join and saved-room continuation.

## Performance and device coverage

Record the device model, OS, game version, renderer/quality profile, resolution and control mode. Test town, forest, interior, dungeon, dense combat and repeated map changes. Report visible hitches, long loading screens, memory growth, low frame rate and unreadable controls.

On Android, include a longer session to check heating and throttling, background/resume, screen safe areas, touch aiming, interrupted connections and battery use. PC Mobile mode checks layout; it does not replace this device testing.

The proposed targets are 60 FPS at 720p/low on a specified low-end PC and 30 FPS in efficiency mode on a specified low-end Android device. Actual supported hardware must be determined by recorded tests.

## Bug report

Reproducible reports get fixed first. Include:

- Build version (title screen, bottom right) and platform/device.
- Exact steps from launch to the problem.
- Expected result and actual result.
- Map, class, party size and quality/control settings.
- Whether it repeats and whether a restart changes it.
- Screenshot or short recording, plus sanitized logs if requested.

Never include passwords, recovery codes, sign-in tokens, signing keys or the private server database. Save a copy of valuable progress before participating in any announced migration/reset test.
