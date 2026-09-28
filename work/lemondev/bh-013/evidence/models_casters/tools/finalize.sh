#!/bin/sh
# usage: finalize.sh <id> <stance> <clip,list> <headz>   build GLB + .import, evidence sheets, scratch Godot check
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
E="A:/Python/beyond-heroes/work/lemondev/bh-013/evidence/models_casters"
S="A:/Python/beyond-heroes/work/lemondev/bh-013/scratch/casters/ev"
c=$1; st=$2; cl=$3; hz=$4
cd "A:/Python/beyond-heroes/tools/blender/characters" && "$B" -b --factory-startup --python build.py -- $c 2>&1 | grep "^\[\|INFO: Finished\|Error\|rror:" > "$E/logs/build_$c.txt"
cat "$E/logs/build_$c.txt"
python "$E/tools/mkimport.py" $c
sh "$E/tools/run.sh" $c rest --stance $st --headz $hz --headviews 15:5,340:15 | grep SHEET
sh "$E/tools/run.sh" $c clips --clips $st,$cl,hit_heavy,death_back --frames 0,0.3,0.5,0.7,1 | grep SHEET
cp "$S/${c}_rest.png" "$E/${c}_rest_iso.png"; cp "$S/${c}_clips.png" "$E/${c}_clips.png"
cp "$S/${c}_metrics.json" "$E/logs/" 2>/dev/null
python "$E/tools/godot_check_casters.py" $c > "$E/logs/godot_check_$c.txt" 2>&1; cat "$E/logs/godot_check_$c.txt"
