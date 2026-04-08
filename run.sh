#!/bin/bash
# Auto-generated wrapper for Genus AI
cd "/home/lex/Genus"
export DISPLAY=":0"
export WAYLAND_DISPLAY="wayland-0"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
exec /usr/bin/python "/home/lex/Genus/genus.py" >> "/home/lex/Genus/genus_startup.log" 2>&1
