#!/bin/sh
# usage: run.sh <char> <mode> [extra args]
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
D="C:/Users/LEMONP~1/AppData/Local/Temp/claude/A--Python-beyond-heroes/da74bdb3-b0af-4ea6-8de0-c14b2502dd65/scratchpad/ev"
c=$1; m=$2; shift 2
"$B" -b --factory-startup --python "$D/ev_blender.py" -- $c --out "$D/out" --mode $m "$@" 2>&1 | grep -v "^Fra:\|Saved:\|Time:\|^ *$\|Blender quit\|Blender 5" | tail -25
if [ "$m" != "metrics" ] && [ "$m" != "parts" ]; then python "$D/ev_compose.py" "$D/out/${c}_${m}.json" "$D/out/${c}_${m}.png" "$c $m"; fi
