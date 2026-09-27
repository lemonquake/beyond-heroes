extends Node
## Global signal bus (autoload `Events`). Gameplay emits; UI, audio, FX, quests and achievements listen.
## Every combat event carries the structured DamageResult (attacker, target, element, crit, reactions, knockback ...).

# Combat
signal damage_dealt(target: Node, result: DamageResult, position: Vector3, attacker: Node)
signal actor_died(actor: Node, killer: Node)
signal impact(position: Vector3, strength: float, surface: StringName)
signal camera_shake(trauma: float)
signal hitstop(duration: float)
signal skill_ready(skill_id: StringName)
signal status_applied(actor: Node, status_id: StringName)
# Player
signal player_spawned(player: Node)
signal player_died
signal player_respawned
signal player_leveled(level: int, gained: int)
signal xp_gained(amount: int)
# Loot / items
signal loot_dropped(item: ItemInstance, position: Vector3)
signal loot_picked(item: ItemInstance)
signal gold_picked(amount: int)
signal item_equipped(item: ItemInstance, slot: StringName)
signal item_sold(item: ItemInstance, gold: int)
signal item_bought(item: ItemInstance, gold: int)
# Enemies / bosses
signal boss_engaged(boss: Node)
signal boss_phase(boss: Node, phase: int)
signal boss_defeated(boss: Node)
signal elite_spawned(enemy: Node)
signal enemy_alerted(enemy: Node)
# World / NPCs / dialogue (quest-ready hooks)
signal map_loaded(map_id: StringName)
signal teleporter_discovered(map_id: StringName)
signal world_flag_set(flag: StringName, value: Variant)
signal talk_requested(npc: Node)
signal dialogue_started(npc_id: StringName)
signal dialogue_event(event_id: StringName, args: Dictionary)
signal dialogue_ended(npc_id: StringName)
signal shop_opened(shop_id: StringName)
signal shop_closed(shop_id: StringName)
signal guild_joined(guild_id: StringName, first_time: bool)
signal tier_changed(rank: int)
signal rested(fee: int)
# Tempos (spirit companions)
signal tempo_changed(uid: int)          # bound, released, called back, gear changed (0 = all)
signal tempo_fallen(tempo: Node)
signal tempo_spawned(tempo: Node)
# UI
signal notify(text: String, kind: StringName)
signal town_portal_changed                       # a Town Portal opened, was dispelled or expired
signal ui_toggle(panel: StringName)
signal interact_prompt(text: String)
signal tooltip_request(content: Variant, anchor: Control)
