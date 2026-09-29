# Inventory, auto-loot and stat update

29 September 2026

## Player changes

- Dungeon entrance signs, interaction prompts, travel choices and map information show suggested levels from the dungeon definitions. Story dungeon travel prompts also show their existing level recommendations.
- General inventory grows from 60 to 84 slots. Equipment appears in the Gear Bag; materials, keys and other supplies appear in the Utility Bag. These two views share the 84 general slots. Consumables fill a separate 16-slot Potion & Scroll Belt first and can overflow into the Utility Bag. All Bags shows both storage areas in one window. Q/E remain the two configurable quick-use bindings.
- Category buttons cover weapons, armor, accessories, ingredients, potions, scrolls, keys/quest items and all consumables. Search and rarity filters hide nonmatching items. Sorting supports rarity, category, item level, name, value and weight, with reverse order and favorites first. Sorting never puts equipment in the belt.
- Carry capacity is now 220 + 6.4 per Strength before existing capacity modifiers, twice the previous base and Strength contribution.
- Physical weapon scaling uses Strength for every weapon type, retaining each type's total coefficient (usually 1% per point; great axes 1.1%). Unarmed attacks still scale with Strength. Spell damage still uses Intelligence/Wisdom. Dexterity affects Accuracy and Critical Chance only; its former weapon/projectile damage, projectile speed, block and parry bonuses are removed.

## Auto-loot

Open **Inventory > Auto-Loot Filters** or **Settings > Gameplay > Auto-Loot Categories & Advanced Filters**.

- Select individual categories and weapon types, or use Everything, Equipment, Crafting Supplies, Potions & Scrolls, or Valuable Equipment presets.
- Set minimum rarity, equipment level and sockets; optionally accept only gear whose level and attribute requirements are met.
- Set minimum item value, value per weight, maximum drop weight, a carried-load percentage, reserved general bag slots and a total limit for each consumable type.
- Include or exclude comma-separated name fragments. Matching ignores capitalization. Exclusions take precedence.
- Optional quest and unique/set exceptions bypass item filters, but never exclusions, available space or the carrying limit.
- Preview category/item rules using carried items. Settings persist in configuration and saves. Gold retains contact pickup; excluded items remain on the ground for manual pickup.
- In-flight pickup rechecks filters, load and space, preventing simultaneous pickups from ignoring these limits.

## Compatibility

Old saves keep their items and gain the new capacity. Existing consumable stacks move into the reserved belt without losing flags or identity. Crafting, trading, equipment swaps and merchant grids account for the larger inventory and restricted belt. Multiplayer protocol is now 7 so clients with the older capacity/stat rules cannot join.

## Validation and builds

- Final focused suites: **4,551 checks, zero failures**, covering item rules, stat contributions for every weapon type, capacity, legacy migration, sorting, save roundtrips, atomic equipment/trade failures, all dungeon recommendations, and auto-loot rules/persistence.
- Broader regression run: 35,150 checks across 32 suites. A new test fixture initially offered a temporary stack already merged into starter scrolls; the fixture was corrected and the focused suites passed again. The eight remaining enemy assertions were reproduced verbatim on the unchanged `2c78f99` baseline. They concern the outdated enemy count, War Totem balance and live enemy behavior tests.
- The separate combat-balance gate remains failing: 13 of 16 assertions with the new stat rules, versus 11 of 16 on the unchanged baseline. This update does not claim class balance; the requested attribute changes alter relative weapon damage.
- Rendered and inspected All Bags, Gear, Utility, Belt, Scrolls, empty results, and both parts of the auto-loot screen. Both windows stay within their declared frame sizes.
- Godot 4.7.2 Windows release export; executable startup smoke test completes with exit code 0. Headless startup logs display-server keyboard-label warnings.
- Android APK uses debug signing because no release keystore is configured. APK signature verification passes. The build targets ARMv7 and ARM64; it has not been tested on a physical Android device in this update.

Local artifacts: `build/windows/BeyondHeroes.exe`, `build/BeyondHeroes-Windows.zip`, `build/BeyondHeroes.apk`. Checksums are written to `build/build-checksums.json`. Test logs and UI captures are kept locally under `output/`.
