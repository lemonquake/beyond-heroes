#!/bin/sh
# usage: run.sh <char> <mode> [extra args]   (modes: rest | clips | metrics | parts)
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
T="A:/Python/beyond-heroes/work/lemondev/bh-012/evidence/models_deeps/tools"
D="A:/Python/beyond-heroes/work/lemondev/bh-012/scratch/deeps/ev"
c=$1; m=$2; shift 2
"$B" -b --factory-startup --python "$T/ev_blender.py" -- $c --out "$D" --mode $m "$@" 2>&1 | grep -v "^Fra:\|Saved:\|Time:\|^ *$\|Blender quit\|Blender 5" | tail -25
if [ "$m" != "metrics" ] && [ "$m" != "parts" ]; then python "$T/ev_compose.py" "$D/${c}_${m}.json" "$D/${c}_${m}.png" "$c $m"; fi
