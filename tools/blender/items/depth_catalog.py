"""Author the depth equipment catalog and Blender specifications from one source.
Run with system Python; then dump_items.tscn and build_items.py all <ids>.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
rows=[]; specs={}
families={
 'sword':['Copperleaf Backsword','Saltglass Cutlass','Rootguard Falchion','Lantern Rapier','Cinderhook Saber','Frostbell Broadsword','Hollowfin Estoc','Moonwell Flamberge','Starfall Spatha','Deepwatch Messer','Sunken Oathblade','Crownless Longsword'],
 'greatsword':['Basalt Zweihander','Briar Executioner','Astral Greatblade','Vaultbreaker Claymore'],
 'staff':['Glowcap Crook','Tidal Forkstaff','Cinder Lanternstaff','Rime Shardstaff','Thornseed Branchstaff','Orrery Starstaff','Voidcage Scepter','Dawnspire Staff'],
 'wand':['Sporebud Wand','Shellsong Wand','Embercrown Wand','Icepetal Wand','Gravebell Wand','Moonhook Wand','Prismcoil Wand','Sunwheel Wand'],
 'bow':['Rootbend Shortbow','Saltwind Recurve','Cinderhorn Bow','Icebranch Longbow','Thornwing Bow','Starbridge Bow','Nightglass Warbow','Dawnfeather Bow'],
 'javelin':['Sporeleaf Javelin','Keelspike Javelin','Furnace Barb','Rimefork Javelin','Briarfin Javelin','Starshard Javelin','Gloomspear','Suncrest Javelin'],
 'dagger':['Rootfang Skinner','Keelhook Knife','Emberwave Kris','Iceglass Stiletto','Briar Talon','Moonfang Kukri','Voidpetal Dagger','Dawnthorn Knife'],
 'claw':['Rootrake Claws','Keelgrip Talons','Furnace Knives','Rimefang Claws','Briarhook Claws','Starweb Talons','Voidreaver Claws','Dawnrake Claws']}
classes={'sword':'knight','greatsword':'knight','staff':'mage','wand':'mage','bow':'ranger','javelin':'ranger','dagger':'shadowblade','claw':'shadowblade'}
aps={'sword':1.45,'greatsword':.92,'staff':1.0,'wand':1.6,'bow':1.08,'javelin':1.18,'dagger':2.0,'claw':1.85}
metals=['bronze','moonsteel','darksteel','silver','blackiron','blued','bright','sunsteel']
gems=['emerald','tide','ember','ice','ruby','aether','onyx','holy']
# All design variations alter geometry as well as their materials.
for wt,names in families.items():
 for i,name in enumerate(names):
  level=([25,28,32,35,38,41,44,47,50,53,56,60] if len(names)==12 else [25,35,50,60] if len(names)==4 else [25,30,35,40,45,50,55,60])[i]
  iid='depth_'+name.lower().replace(' ','_');cls=classes[wt];j=i%8
  element= [4,6,1,2,4,7,8,7][j] if wt in ['staff','wand'] else [0,6,1,2,0,7,8,7][j]
  stat=['stagger_power','crit_chance','status_power','pen_armor'][i%4]
  val=[.12,.025,.12,.04][i%4]
  rows.append([iid,name,wt,cls,level,round(aps[wt]*(.9+.04*(i%6)),3),element,stat,val,'',round({'sword':3.4,'greatsword':8.5,'staff':3.6,'wand':1.,'bow':2.6,'javelin':2.3,'dagger':1.2,'claw':1.8}[wt]*(.83+.053*i),2)])
  m=metals[j];gem=gems[j]
  if wt in ['sword','greatsword']:
   s={'len':(.66+.042*i) if wt=='sword' else 1.05+.09*i,'w':[.037+.007*(i%5),.019+.008*(i%4)],'shape':['straight','sabre','falchion','waisted','leaf'][i%5], 'guard':['bar','disc','winged','swept'][i%4], 'guard_half':.065+.013*(i%7),'guard_curve':-.02+.015*(i%5),'blade':m,'guard_mat':metals[(j+3)%8], 'pommel':['ring','disc','spike','round'][i%4],'grip_len':.16 if wt=='sword' else .29,'glow':gem,'wave':.012 if i==7 else 0,'lugs':i in [4,9],'serrate':i in [2,10],'ricasso':m if i%2 else None}
   builder='sword'
  elif wt=='staff':
   s={'head':['crook','fork','orb','shards','branch','star','prongs','star'][j],'wood':['darkwood','ash','redwood','bone'][j%4],'metal':m,'gem':gem,'band':m,'wobble':.005+.006*j};builder=wt
  elif wt=='wand':
   s={'head':['branch','shell','claw','crescent','skull','crescent','orb','sun'][j],'wood':['darkwood','ash','redwood','bone'][j%4],'orn':m,'gem':gem};builder=wt
  elif wt=='bow':
   s={'len':.45+.04*j,'recurve':.02+.018*(j%4),'bend':.07+.015*j,'limb_w':.015+.003*(j%3),'wood':['darkwood','ash','redwood','bone'][j%4],'glow':gem,'wraps':['leather','redleather','tan','navy'][j%4],'leaf_tips':m if j%2 else None,'thick_riser':m if j>4 else None};builder=wt
  elif wt=='javelin':
   s={'shaft_top':.6+.035*j,'shaft_bot':-.65-.025*j,'head_len':.17+.025*j,'head_w':.035+.007*(j%4),'head':['leaf','barbed','leaf','fork','leaf','barbed','leaf','fork'][j],'head_mat':m,'shaft_mat':['darkwood','ash','redwood','bone'][j%4],'band_mat':metals[(j+3)%8],'glow':gem,'fins':m if j%2 else None};builder=wt
  elif wt=='dagger':
   s={'len':.22+.024*j,'w':[.028+.005*(j%4),.017+.004*(j%3)],'shape':['skinner','crescent','kris','straight','crescent','kukri','kris','straight'][j],'blade':m,'guard':['bar','wide','disc'][j%3],'guard_mat':metals[(j+3)%8],'glow':gem,'pommel':['round','ring','disc','spike'][j%4]};builder=wt
  else:
   s={'len':.19+.018*j,'blades':2+j%4,'spacing':.027+.004*(j%3),'hook':.01+.018*(j%4),'blade':m,'frame_mat':metals[(j+3)%8],'glow':gem,'spikes':j%2==1,'scales':m if j>4 else None};builder=wt
  specs[iid]=[builder,s]
for ci,cls in enumerate(['knight','mage','ranger','shadowblade']):
 for i,(cat,noun) in enumerate([('armor','Coat'),('helm','Crown'),('gloves','Grips'),('boots','Treads')]):
  title=['Deepwarden','Prismkeeper','Vaultpath','Gloomthread'][ci];name=f'{title} {noun}';iid='depth_'+name.lower().replace(' ','_');level=[25,38,50,60][i]
  power=([['valorous','echoing_guard'],['overflow','frostbite'],['m_frostguard','a_crit_lightning'],['bloodthirst','relentless']][ci][0 if i==0 else 1]) if i in [0,2] else ''
  rows.append([iid,name,cat,cls,level,0,0,['max_hp','max_mana','evasion','move_speed'][ci],[35.,24.,20.,.12][ci],power,0])
  color=['blued','violet','forest','black'][ci];trim=['bronze','silver','copper','moonsteel'][ci]
  if cat=='armor':builder='chest';s={'kind':['plate','robe','brigandine','vest'][ci],'mat':color,'trim':trim,'len':.74+.065*ci,'belt':'darkleather','rivet':trim,'glow':gems[ci]}
  elif cat=='helm':builder='helm' if ci==0 else 'hood';s={'mat':color,'trim':trim,'gem':gems[ci],'glow':gems[ci],'kind':'greathelm','peak':.55+.45*ci}
  elif cat=='gloves':builder='glove';s={'mat':color,'trim':trim,'runes':gems[ci],'cuff':trim,'plate':trim if ci==0 else None,'spikes':trim if ci==3 else None}
  else:builder='boot';s={'mat':color,'h':.25+.035*ci,'flare':.006+.005*ci,'cuff':trim,'glow':gems[ci],'plate':trim if ci==0 else None,'straps':'darkleather'}
  specs[iid]=[builder,s]
(HERE/'depth_specs.json').write_text(json.dumps(specs,indent=2)+'\n')
header='''class_name DataDepthEquipment
## Generated catalog; edit tools/blender/items/depth_catalog.py and regenerate.
## 64 weapons and 16 armor pieces; eight named relics have guaranteed functional powers.
const ROWS := '''
code=header+'[\n'+',\n'.join('\t'+json.dumps(row) for row in rows)+'\n]'+'''

static func bases() -> Array:
	var out := []
	for r in ROWS:
		var weapon: bool = r[2] in ["sword", "greatsword", "staff", "wand", "bow", "javelin", "dagger", "claw"]
		var cls := StringName(r[3])
		var level := int(r[4])
		var attr: StringName = &"str" if cls == &"knight" else (&"int" if cls == &"mage" else &"dex")
		var req := {attr: 12 + level}
		var b := DataItems._b(StringName(r[0]), r[1], &"weapon" if weapon else StringName(r[2]), "", {
			"level_req": level, "drop_level": level, "class_hint": cls, "requirements": req,
			"value": 40 + level * 5, "tier": 3, "weight_class": &"heavy" if cls == &"knight" else &"cloth"})
		b.icon = DataItems.ICON3D % b.id
		b.model = ItemBaseDef.ITEM_MODEL % b.id
		b.implicit = [StatModifier.inc(StringName(r[7]), float(r[8])) if r[7] in ["stagger_power", "status_power", "move_speed"] else StatModifier.flat(StringName(r[7]), float(r[8]))]
		if b.category == &"boots" and r[7] != "move_speed":
			b.implicit.append(StatModifier.inc(&"move_speed", 0.08))
		if weapon:
			b.weapon_type = StringName(r[2])
			b.attacks_per_second = float(r[5])
			if b.weapon_type == &"staff":
				b.implicit.append(StatModifier.inc(&"magic_damage", 0.10 + level * 0.0045))
			var damage := DataItems.roster_damage(b.weapon_type, level, b.attacks_per_second)
			b.damage_min = damage.x
			b.damage_max = damage.y
			b.element = int(r[6])
			b.element_share = (1.0 if cls == &"mage" else 0.25) if b.element != Elements.PHYSICAL else 0.0
		else:
			var factor := 1.0 if cls == &"knight" else 0.6
			b.defense = (12.0 + level * 1.5) * factor * (1.0 if b.category == &"armor" else 0.5)
		b.weight = float(r[10]) if weapon else DataItems.default_weight(b)
		b.flavor = "Recovered from the deeper halls. " + ("A fast weapon trades damage per strike for speed." if weapon and b.attacks_per_second > 1.5 else "Made for long journeys below the surface.")
		if r[9] != "":
			b.unique_name = b.display_name
			b.fixed_rarity = BH.Rarity.MYTHICAL if level < 50 else BH.Rarity.LEGENDARY
			b.fixed_powers = [StringName(r[9])]
			b.drop_weight = 0
		out.append(b)
	return out

## Guardians target the new relics for the receiving class, with exact level gates.
static func special(rng: RandomNumberGenerator, ilvl: int, cls: StringName) -> ItemBaseDef:
	var pool := []
	for r in ROWS:
		var b := DB.item_base(StringName(r[0]))
		if b and b.unique_name != "" and b.drop_level <= ilvl and b.class_hint == cls:
			pool.append(b)
	return pool[rng.randi_range(0, pool.size() - 1)] if not pool.is_empty() else null
'''
(ROOT/'game/src/data/data_depth_equipment.gd').write_text(code,encoding='utf-8')
print(f'{len(rows)} equipment designs written')
