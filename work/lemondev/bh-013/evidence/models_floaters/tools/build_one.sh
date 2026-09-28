#!/bin/sh
# usage: build_one.sh <id> "<Title>"  -> builds the GLB, preview tiles, and both contact sheets
ID=$1; TITLE=$2
R=/a/Python/beyond-heroes
EV=$R/work/lemondev/bh-013/evidence/models_floaters
SC=$R/work/lemondev/bh-013/scratch/floaters
mkdir -p $EV/logs
cd $R/tools/blender/creatures
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python build_$ID.py -- --preview "$(cygpath -w $SC)" > $EV/logs/build_$ID.log 2>&1
grep "^\[$ID\]\|Error\|Traceback" $EV/logs/build_$ID.log | head -30
python $EV/tools/ev_compose.py $SC/${ID}_iso.json $EV/${ID}_rest_iso.png "$TITLE - gameplay camera (54 deg pitch)"
python $EV/tools/ev_compose.py $SC/${ID}_views.json $EV/${ID}_views.png "$TITLE - views"
