#!/bin/sh
# usage: finalize.sh <id>   build GLB + .import, copy sheets into evidence, scratch Godot check (Builder B2 brutes)
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
E="A:/Python/beyond-heroes/work/lemondev/bh-013/evidence/models_brutes"
S="A:/Python/beyond-heroes/work/lemondev/bh-013/scratch/brutes"
c=$1
cd "A:/Python/beyond-heroes/tools/blender/characters" && "$B" -b --factory-startup --python build.py -- $c 2>&1 | grep "^\[\|INFO: Finished\|Error\|rror:" > "$E/logs/build_$c.txt"
cat "$E/logs/build_$c.txt"
python "A:/Python/beyond-heroes/work/lemondev/bh-013/evidence/models_casters/tools/mkimport.py" $c
cp "$S/${c}_rest.png" "$E/${c}_rest_iso.png"; cp "$S/${c}_clips.png" "$E/${c}_clips.png"
GC_PROJ=godot_$c python "$E/tools/godot_check_brutes.py" $c > "$E/logs/godot_check_$c.txt" 2>&1; cat "$E/logs/godot_check_$c.txt"
