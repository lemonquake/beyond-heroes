#!/bin/bash
# Run the Godot project with the real renderer. On a machine without a display (CI / cloud container) this uses
# Xvfb + Mesa lavapipe (software Vulkan): images are correct but frame times are NOT representative.
#   tools/render.sh res://tests/tools/capture_maps.tscn -- --maps=sanctuary --out=/tmp/out
cd "$(dirname "$0")/../game"
GODOT="${GODOT:-$(command -v godot)}"
if [ -z "$DISPLAY" ] && command -v xvfb-run > /dev/null; then
	export VK_ICD_FILENAMES="${VK_ICD_FILENAMES:-/usr/share/vulkan/icd.d/lvp_icd.json}"
	exec xvfb-run -a -s "-screen 0 3840x2160x24" "$GODOT" --path . "$@"
fi
exec "$GODOT" --path . "$@"
