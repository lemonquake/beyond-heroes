#!/usr/bin/env bash
# Compile GDScript files with the project's autoloads loaded (map-design pass). Usage: tools/gdcheck.sh game/src/a.gd ...
# Prints SCRIPT ERROR lines and exits 1 if any script fails, so a broken test never reaches the hanging runner.
G="${GODOT:-/c/Users/Lemon PC/Desktop/Godot.exe}"
list=""
for f in "$@"; do list="$list,res://${f#game/}"; done
out=$(timeout 120 "$G" --headless --path game res://tests/tools/map_design_probe.tscn -- --cmd=check --scripts="${list#,}" 2>&1)
echo "$out" | grep -E "SCRIPT ERROR|Parse Error|Compile Error" && exit 1
echo "$out" | grep -q '": false' && { echo "$out" | grep '": false'; exit 1; }
echo "ok: $#"
