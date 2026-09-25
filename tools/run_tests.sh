#!/bin/bash
cd 'A:/Python/beyond-heroes/game'
GODOT='/a/Installer/Godot_v4.4.1-stable_win64.exe/Godot_v4.4.1-stable_win64_console.exe'
timeout 300 "$GODOT" --headless --path . res://tests/run_tests.tscn 2>&1 | grep -vE "^\s*$|^Godot Engine|^OpenGL|^Vulkan" | head -${1:-80}
