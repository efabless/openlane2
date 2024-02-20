import os
import glob
import subprocess

__dir__ = os.path.dirname(__file__)

pngs = glob.glob(os.path.join(__dir__, "[!b]**", "*.png"), recursive=True)

for png in pngs:
    subprocess.check_call(["convert", png, png.replace(".png", ".webp")])
    os.unlink(png)
