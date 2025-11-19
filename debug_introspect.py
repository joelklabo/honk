#!/usr/bin/env python3
"""Debug script to see what introspect returns."""

import subprocess
import json

result = subprocess.run(
    ["honk", "introspect", "--json"],
    capture_output=True,
    text=True,
)

data = json.loads(result.stdout)
commands = data["commands"]

print(f"Total commands: {len(commands)}\n")

# Group by top-level
from collections import defaultdict
top_level_groups = defaultdict(list)

for cmd in commands:
    if len(cmd["full_path"]) >= 2:
        top_level = cmd["full_path"][1]
        top_level_groups[top_level].append(cmd["full_path"])

print("Top-level commands/groups:")
for name in sorted(top_level_groups.keys()):
    paths = top_level_groups[name]
    print(f"\n  {name}: ({len(paths)} commands)")
    for path in sorted(paths)[:5]:  # Show first 5
        print(f"    {' '.join(path)}")
    if len(paths) > 5:
        print(f"    ... and {len(paths) - 5} more")

print(f"\n\nFound top-level: {sorted(top_level_groups.keys())}")

expected = {"version", "info", "introspect", "help-json", "doctor", "demo", 
            "watchdog", "system", "auth", "notes", "agent", "release"}
found = set(top_level_groups.keys())
missing = expected - found

if missing:
    print(f"\n❌ Missing: {sorted(missing)}")
else:
    print(f"\n✅ All expected commands found!")
