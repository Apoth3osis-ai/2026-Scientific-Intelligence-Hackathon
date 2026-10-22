"""Append one execute_locally receipt summary to simulations/simulation_runs.json."""
import json, sys, os
path = os.path.join(os.path.dirname(__file__), "simulation_runs.json")
runs = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
rec = json.loads(sys.argv[1])
runs = [r for r in runs if r["task_id"] != rec["task_id"]] + [rec]
json.dump(runs, open(path, "w", encoding="utf-8"), indent=1)
print(len(runs), "runs recorded")
