import os
import subprocess
import sys
import platform

if platform.system() != "Darwin":
    exit(0)

args = sys.argv[1:]

rpath = args[0]
so_path = args[1]
klayout_bin = args[2]

flags = ["-add_rpath", rpath]

top_level_dylibs = [dylib for dylib in os.listdir(rpath) if dylib.endswith(".dylib")]
for dylib in top_level_dylibs:
    flags += ["-change", dylib, f"@rpath/{dylib}"]

targets = (
    [os.path.join(rpath, x) for x in top_level_dylibs]
    + [os.path.join(so_path, x) for x in os.listdir(so_path) if x.endswith(".so")]
    + [klayout_bin]
)

print(f"Patching with command 'install_name_tool {' '.join(flags)}'.")

for target in targets:
    if os.path.islink(target):
        continue
    print(f"Patching dylibs for '{target}'…")
    subprocess.check_call(["install_name_tool"] + flags + [target])
