# Playing Beyond Heroes Together

Up to **12 players** can play together. Everyone needs the same game version.

## Choose how to play

The first menu offers **Official Server**, **Offline Play**, and **Custom Games**.

| Choice | Characters and progress |
| --- | --- |
| Official Server | Sign in with your account. Characters and confirmed progress are stored on the server PC. |
| Offline Play | No internet or account needed. Play all your existing local characters and create new ones. |
| Custom Games | A new room starts fresh. Each player saves its characters locally, separately for that room. |

Characters and rewards stay separate between these choices. Importing an offline character copies it
to the official server; the offline original stays on your device and can still be played.
Later changes to either copy do not update the other.

## Join the Official Server

1. Choose **Official Server** and read the progress notice.
2. Register a UserID and password, or sign in to your existing account.
3. Save the recovery code shown during registration. You need it to reset a forgotten password.
4. Create an official character or choose an existing offline character to import to an empty slot.
5. Select your official character and play. You can explore independently while your friends play.

Official progress saves every five seconds, on experience rewards and other save triggers.
Save, Main Menu and Quit wait for server confirmation. A connection failure pauses official play.
You can retry or explicitly return to your last confirmed server save.

When the server PC shuts down, confirmed progress remains in its database. The official server is
unavailable until that PC and both services start again. **Offline Play remains available.**

For server addresses, certificates and hosting instructions, read [Official Server setup](OFFICIAL_SERVER.md).

## Host a Custom Game

1. At the first menu, enter a name and press **Create Custom Game**.
2. Read the notice explaining that this room uses separate characters.
3. Create a new custom character. The game starts hosting when your character enters the world.
4. Friends select your room from their first menu and create their own room characters.

The room appears in the LAN list and in the shared directory when the official account service is
reachable. Listing a room does not make its port reachable through a router. On the same network,
allow the game through Windows Firewall on the network you use with friends. Custom games need
no official account, and LAN games work without internet.

Use **Host Again** under saved custom games to reopen a room with its existing room characters.
A newly created room has a new identity and starts fresh. Offline and official characters cannot
enter a custom room.

## Friends in different houses

For testing, players can use the same LAN VPN network. The host's game port must be reachable.
The default custom game port is **24680 UDP**. The official service uses **8443 TCP** for accounts
and saves and **24680 UDP** for the game.

Friends can set the official address in **Server Settings**. For a custom room code or direct
address, enter a custom game first, then open **Pause → Multiplayer**. Hosts can share the room
code shown there. The shared room list provides addresses; it does not relay connections.

## While playing together

- Explore separately or meet on the same map. Nearby allies share combat and experience.
- Loot is personal. Another player cannot take your drops.
- Knight auras help nearby friends. Approach a fallen friend and use **Interact** to revive them.
- Use **Team Portal** to visit other players. Official players can choose anyone in the roster.
- Four detailed party frames fit on the HUD. Open the complete player list for the rest.
- Press **Enter** to chat; on a phone use **Chat**. The Multiplayer list shows connection latency.
- Request a trade through a player's party frame or the Multiplayer window. Both players must
  accept the same offers. Changing an offer clears acceptance. Locked, favorite and quest items
  cannot be traded. Official trades save both inventories and gold balances together on the server.

## Leaving

Use **Main Menu** or **Quit** to save and leave. Official play waits for a confirmed server save;
custom characters save on each player's device in that room's folder. Closing a custom host
disconnects its guests. They can continue those room characters when the same room returns.

## Connection problems

| What you see | What to check |
| --- | --- |
| Different game versions | Update everyone's game to the same version. |
| Room missing | Check the LAN/VPN connection, refresh the list, or use its room code. |
| Room listed but cannot connect | The host must still be playing, with a reachable UDP port. |
| Room full | Twelve players are already connected. Wait for a free space. |
| Official account service offline | Start both server services. Offline and LAN custom games still work. |
| Certificate error | Use the host address included in the certificate and the matching public certificate. |
| Official save unconfirmed | Retry while connected. Discard only if you accept losing changes after the last confirmed save. |

This official version is for a trusted friends group. Accounts and storage are centralized, while
combat and rewards still use the existing player map simulation. See the setup guide for its limits.
