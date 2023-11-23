from math import inf
import os
import sys
import glob
import json
import argparse

cmd = argparse.ArgumentParser()
cmd.add_argument("-o", "--output", required=True)
cmd.add_argument("run_dir")
args = cmd.parse_args()

state_out_jsons = sorted(glob.glob(os.path.join(args.run_dir, "*", "state_out.json")))
latest_time = -inf
latest_json = None
for state_out_json in state_out_jsons:
    time = os.path.getmtime(state_out_json)
    if time > latest_time:
        latest_time = time
        latest_json = state_out_json

if latest_json is None:
    print("Flow did not produce any output states", file=sys.stderr)
    json.dump({}, open(args.output, "w", encoding="utf8"))
    exit(1)

print(f"Using '{latest_json}'…")
state_out = json.load(open(latest_json, encoding="utf8"))

metrics = state_out["metrics"]

json.dump(metrics, open(args.output, "w", encoding="utf8"))
