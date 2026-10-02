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
signal item_crafted(recipe_id: StringName, items: Array)
signal weapon_upgraded(item: ItemInstance, kind: StringName)   # an Enchantment or Fore-Tech step was applied (bh-017)
signal recipe_learned(recipe_id: StringName)
signal herb_gathered(base_id: StringName, count: int)
# Enemies / bosses
signal boss_engaged(boss: Node)
signal boss_phase(boss: Node, phase: int)
signal boss_defeated(boss: Node)
signal elite_spawned(enemy: Node)
signal enemy_alerted(enemy: Node)
# Stages and minibosses (bh-007): a camp wiped out, every camp of a combat map cleared this visit, a named champion down
signal camp_cleared(map_id: StringName, zone: String, left: int, total: int)
signal stage_cleared(map_id: StringName)
signal miniboss_defeated(miniboss_id: StringName)
signal clears_changed(count: int)               # the hero's clear counter moved (Olivar's merchants restock)
# World / NPCs / dialogue (quest-ready hooks)
signal map_loaded(map_id: StringName)
signal teleporter_discovered(map_id: StringName)
signal world_flag_set(flag: StringName, value: Variant)
signal talk_requested(npc: Node)
signal dialogue_started(npc_id: StringName)
signal dialogue_event(event_id: StringName, args: Dictionary)
# bh-021: cinematic cutscenes (CutscenePlayer)
signal cutscene_started(id: StringName)
signal cutscene_finished(id: StringName)
signal dialogue_ended(npc_id: StringName)
signal shop_opened(shop_id: StringName)
signal shop_closed(shop_id: StringName)
signal guild_joined(guild_id: StringName, first_time: bool)
signal profile_picture_changed(peer: int)          # bh-030: a hero's picture changed (0 = this machine's own hero)
signal debug_unlocked                            # bh-030: `azrin azrael` unlocked the Debug console for this hero
signal quake_team_changed                       # a Quake Team ally was called or dismissed (bh-017)
signal guild_customised                          # the hero renamed their guild or changed its banner (bh-017)
signal tier_changed(rank: int)
signal rank_tracker_changed                      # bh-033: the hero showed, minimized or hid the next-rank tracker
signal guild_changed                             # bh-027: a guild's roster, passives, summons or the known guilds changed
signal guild_jobs_changed                        # a Guild House job was taken, moved on, handed in or dropped
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
