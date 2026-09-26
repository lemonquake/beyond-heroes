#!/bin/bash
# Headless test runner. Refreshes the script class cache / imports first (new class_name scripts), then runs the suite.
cd 'A:/Python/beyond-heroes/game'
GODOT='/a/Installer/Godot_v4.4.1-stable_win64.exe/Godot_v4.4.1-stable_win64_console.exe'
timeout 300 "$GODOT" --headless --path . --import > /dev/null 2>&1
timeout 300 "$GODOT" --headless --path . res://tests/run_tests.tscn 2>&1 | grep -vE "^\s*$|^Godot Engine|^OpenGL|^Vulkan|RID allocations|leaked at exit|resources still in use|^\s+at: |BUG: Unreferenced" | head -${1:-80}
