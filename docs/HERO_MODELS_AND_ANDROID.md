# Hero models and Android controls

New heroes start with a class model from Warriors of Aether. Change Look lets you choose **Class model** or **Custom hero**. Editing a body or face control switches to Custom hero so the control visibly changes your character. Existing saved heroes retain their custom appearance.

| Class | Model | Reason |
| --- | --- | --- |
| Knight | Emelrich | Plate armor and a clear melee silhouette suit the shield and heavy-weapon role. |
| Mage | Azrin | Hooded robes and staff poses fit a spellcaster. |
| Hunter | Blood Ranger | The source look, hair, outfit and actual bow motion fit the ranged role. |
| Shadowblade | Caziel | A hooded coat and dual-weapon poses fit the assassin role. |

Class outfits are fixed cosmetics. Equipped weapons, shield crystals and special equipment effects still follow the actual equipped items. Custom hero keeps fitted clothing and appearance sliders. Source motion is fitted to the existing attack-release timestamps; combat damage timing is unchanged. Source arm repairs are applied consistently to compatible hero rigs, including the shared Hunter/Custom body, so appearance load order does not change poses.

In touch mode, tap an inventory item to select it and hold it for its options. Options use the same availability rules as the action bar. Hold a shop stack to choose a quantity. Hold a skill or talent node to refund a rank. Hold a belt slot to choose its consumable. Sliding, a second finger, closing a window or losing application focus cancels a pending hold. Moving and aiming can use different fingers, and held actions release when play is interrupted.

Efficiency Mode uses a small scene with one class hero for the main menu, avoiding the full town and its gameplay objects before Play. The desktop backdrop retains the town and all four class models.

Video settings offer 30, 60, 90, 120, 144, 165 and 240 FPS caps, plus Unlimited. Quality changes retain the selected cap. A new mobile installation targets 60 FPS with lighter rendering; an existing saved cap is preserved. Choose 30 FPS to reduce power use or a higher cap for a faster display. On compatible Android versions the game also requests the chosen display rate; Android still decides according to the display, battery and temperature. A cap is a limit, not a promised measured speed.

The Windows and Android build scripts require the local Blood Ranger animation resource. It is kept out of loose public source distribution. See [asset credits and extraction instructions](../game/assets/characters/roles/CREDITS.md). Model and source-motion hashes are recorded beside the assets. Build products are in `build/`; QA reports and screenshots are in `output/hero-port-20261026/`.

The local Android release preset includes ARMv7, ARM64 and x86_64 libraries. The x86_64 library supports compatible Android emulators and Chromebooks without ARM translation. The APK uses the project's existing debug signing setup for direct installation.
