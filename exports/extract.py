"""Write the provider programs from a downloaded export_provider_programs result file.

For each artifact (openqasm3, qiskit_python) the exact canonical source is written unchanged,
and exports/export_index.json records the target, the legalization checks (exact readback, ISA,
timing, topology) and the source digest.

Usage:  python extract.py <result_file.json> <circuit_name> <task_id>
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = {"openqasm3": ".qasm", "qiskit_python": "_qiskit.py"}

path, name, task_id = sys.argv[1], sys.argv[2], sys.argv[3]
res = json.load(open(path, encoding="utf-8"))["result"]["result"]
index_path = os.path.join(HERE, "export_index.json")
index = json.load(open(index_path, encoding="utf-8")) if os.path.exists(index_path) else []
index = [x for x in index if not (x["circuit"] == name and x["task_id"] == task_id)]
for art in res["artifacts"]:
    target = art["target"]
    src = art["canonical_source"]
    fname = name + EXT[target]
    with open(os.path.join(HERE, fname), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    leg = art["legalization"]
    index.append({"circuit": name, "target": target, "file": fname, "task_id": task_id,
                  "source_sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
                  "exact_readback_checked": leg.get("exact_readback_checked"),
                  "isa_checked": leg.get("isa_checked"), "timing_checked": leg.get("timing_checked"),
                  "topology_checked": leg.get("topology_checked"),
                  "hardware_submission": res.get("hardware_submission")})
    print(fname, len(src), "chars", {k: leg.get(k) for k in ("exact_readback_checked", "isa_checked")})
json.dump(index, open(index_path, "w", encoding="utf-8"), indent=1)
