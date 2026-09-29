#!/bin/sh
# prev.sh <char> <tag> <extra args...>: render with legend_preview.py in Blender (quiet)
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
c=$1; t=$2; shift 2
"$B" -b --factory-startup --python legend_preview.py -- $c --tag $t "$@" 2>&1 | grep -E "Error|Traceback|File \"|RENDERED|missing"
