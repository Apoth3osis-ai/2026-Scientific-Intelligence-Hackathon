"""Read a saved execute_locally get_task response and append its summary to simulation_runs.json.

Usage:  python ingest.py <saved get_task response>
        python ingest.py <downloaded result_file> <task_id> <date_created> <date_updated>
The second form is for tasks whose get_task returns the result as a File Manager file.
"""
import json, os, sys

def load(path):
    o = json.load(open(path, encoding="utf-8"))
    if isinstance(o, list):
        o = json.loads(o[0]["text"])
    return o

def summarize(o, task=None):
    if task:  # result_file: {"action", "result"}; task metadata comes from get_task
        out = dict(zip(("task_id", "date_created", "date_updated"), task))
        r = o["result"]
    else:
        out = o["result"]["output"]
        r = out["outputs"][0]["result"]
    res = r["result"]
    prov = res["backend_provenance"]
    cid = res["canonical_circuit"]["circuit_id"]
    return {"circuit_id": cid, "basis": cid.rsplit("_", 1)[1].upper(), "task_id": out["task_id"],
            "submitted": out["date_created"][:19] + "Z", "completed": out["date_updated"][:19] + "Z",
            "backend_id": res["backend_id"], "simulator_method": prov.get("simulator_method"),
            "backend_versions": prov.get("backend_package_versions"), "precision": prov.get("precision"),
            "semantic_profile": res["canonical_circuit"]["semantic_profile"],
            "precommitted_seed": prov.get("precommitted_seed"), "simulator_seed": prov.get("simulator_seed"),
            "execution_input_sha256": prov.get("execution_input_sha256"),
            "canonical_request_sha256": r.get("canonical_request_sha256"),
            "shots": res["shots"], "counts": res["counts"], "key_order": "qubit 0 leftmost",
            "service_version": r.get("service_version")}

if __name__ == "__main__":
    rec = summarize(load(sys.argv[1]), sys.argv[2:5] if len(sys.argv) > 2 else None)
    path = os.path.join(os.path.dirname(__file__), "simulation_runs.json")
    runs = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    runs = [x for x in runs if x["task_id"] != rec["task_id"]] + [rec]
    json.dump(runs, open(path, "w", encoding="utf-8"), indent=1)
    print(rec["circuit_id"], rec["backend_id"], rec["counts"], f"({len(runs)} runs recorded)")
