#!/bin/sh
# usage: run.sh <char> <mode> [extra args]   (modes: rest | clips | metrics | parts)
B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
T="$(cd "$(dirname "$0")" && pwd)"
D="C:/Users/LEMONP~1/AppData/Local/Temp/claude/A--Python-beyond-heroes/2174d3af-8bc8-426c-abb3-ed04021b3f29/scratchpad/ev"
mkdir -p "$D/out"
c=$1; m=$2; shift 2
"$B" -b --factory-startup --python "$T/ev_blender.py" -- $c --out "$D/out" --mode $m "$@" 2>&1 | grep -v "^Fra:\|Saved:\|Time:\|^ *$\|Blender quit\|Blender 5" | tail -25
if [ "$m" != "metrics" ] && [ "$m" != "parts" ]; then python "$T/ev_compose.py" "$D/out/${c}_${m}.json" "$D/out/${c}_${m}.png" "$c $m"; fi
