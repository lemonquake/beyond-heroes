# Icon borders

Icon artwork has no baked frame. `IconBorder` resources describe an overlay, a normalized rectangular opening, and a tint. The official style is `aether_forged` in `game/assets/ui/borders/`. Its PNG must have genuine alpha transparency both outside the metalwork and through the opening.

Items, hotbar skills, potions, statuses, tree nodes, skill details, weapon upgrade choices, icon-bearing touch buttons, socket crystal displays and item reveals share `IconBorders`. Touch hit areas and circular button controls remain unchanged; frames stay within their existing icon area. Cooldowns, stack counts, selected state, rarity colors, socket indicators and buff/debuff colors remain live information drawn separately from the cosmetic frame.

To add a future cosmetic, create an `IconBorder` `.tres` resource with a unique `style_id`, readable `display_name`, `texture_path`, `aperture` and optional `tint`. The aperture uses fractions of the complete frame canvas; for example `Rect2(0.09, 0.09, 0.82, 0.82)`. Artwork is placed into that opening before the overlay is drawn. Use a square PNG of at least 256 pixels, no text and a transparent opening. Keep important subjects within the artwork's central 80 percent.

After the content and entitlement system confirms a style is available, call `IconBorders.register_style(resource)`. Register only owned or free styles. This registry does not authorize purchases or grant ownership. Registration emits the existing settings change signal so visible icon controls redraw. `register_style(resource, true)` deliberately replaces an installed style; accidental duplicate IDs and invalid apertures are rejected. `unregister_style(id)` removes optional content. The official style can also be replaced explicitly with `register_style(resource, true)`. Unregistering that ID restores the original official resource, so a usable fallback always remains.

Choose a style through Settings > Gameplay > Icon Border, or `Settings.set_value("icon_border_style", String(resource.style_id))`. The choice persists in device settings rather than following another hero's save. Keep style IDs stable between content revisions. An absent style falls back to the official border while retaining its saved ID, so reinstalling its content restores the preference. Additional styles should be registered before the settings window is opened.

`IconBorders.content_rect(bounds)` gives the artwork rectangle. `IconBorders.draw_frame(canvas, bounds, modulate)` draws the selected overlay. `FramedIcon` combines both for non-interactive previews; interactive widgets keep their original event behavior.

Verification: run the focused `test_icon_borders` suite with the existing Godot test runner. Physical Android device presentation remains a separate device check.
