"""Render the AgentPMT workflow graph (workflow.json) as a readable markdown document."""
import json
import sys

TOOL_LINKS = {
    "6ada7145e001971070f33005": "Valency Research Paper Library",
    "69644454288e0324fa542102": "Live Web Page Browser",
    "6ada6971e001971070f32f9a": "Chemistry Studio",
    "689df4ac8ee2d1dd79e9035b": "Complex Mathematics Engine",
    "6a7e5036b8c970a6773201b5": "Quantum Circuit Builder with Proof",
    "6948b078b54506f955d789ed": "File Management",
}


def main(src, dst):
    wf = json.load(open(src, encoding="utf-8"))
    nodes = {n["id"]: n for n in wf["nodes"]}
    nxt, loop = {}, {}
    for e in wf["edges"]:
        if e.get("sourceHandle") == "loop":
            loop[e["from"]] = e["to"]
        else:
            nxt.setdefault(e["from"], e["to"])
    order, seen = [], set()

    def walk(nid, depth):
        while nid and nid not in seen:
            seen.add(nid)
            order.append((nid, depth))
            if nid in loop:
                walk(loop[nid], depth + 1)
            nid = nxt.get(nid)

    walk(wf["nodes"][0]["id"], 0)
    out = [f"# {wf['name']}", "", wf["description"], "",
           "**Platform:** AgentPMT workflow (skill chain) `6ada7c48e001971070f3313a`, published as v1.1.0.",
           "**Attached context documents** (copies in `../context/`):",
           "- Proof-Carrying Quantum Chemistry Rules (Agent Context `6ada6b06e001971070f32fc7`)",
           "- Certified Clifford+T Synthesis for Exact-Gate Chemistry Circuits (Agent Context `6ada99f0e001971070f333a0`)", "",
           "## Tools", ""]
    used = []
    for n in wf["nodes"]:
        if n["type"] == "tool" and n["tool"]["product_id"] not in used:
            used.append(n["tool"]["product_id"])
    for pid in used:
        out.append(f"- **{TOOL_LINKS.get(pid, pid)}** (`{pid}`)")
    out += ["", "## Steps", ""]
    step = 0
    for nid, depth in order:
        n = nodes[nid]
        step += 1
        ind = "  " * depth
        kind = {"tool": "Tool", "prompt": "Reasoning", "for_each": "Loop"}[n["type"]]
        title = f"{ind}### {step}. {n['label']}" if depth == 0 else f"{ind}#### {step}. {n['label']} (inside the loop)"
        out.append(title)
        out.append("")
        if n["type"] == "tool":
            out.append(f"{ind}*{kind}: {TOOL_LINKS.get(n['tool']['product_id'], n['tool']['product_name'])}*")
            out.append("")
            out.append(n["tool"].get("instructions", ""))
        elif n["type"] == "prompt":
            p = n["prompt"]
            out.append(f"{ind}*{kind} step*")
            out.append("")
            for key in ("goal", "inputs", "outputs", "constraints", "success_criteria"):
                if p.get(key):
                    out.append(f"**{key.replace('_', ' ').capitalize()}:**")
                    out.append("")
                    out.append(p[key])
                    out.append("")
        else:
            out.append(f"{ind}*{kind} over `{n['for_each']['item_alias']}`*")
            out.append("")
            out.append(n["for_each"].get("instructions", ""))
        out.append("")
    out += ["## Graph", "", "```mermaid", "flowchart TD"]
    for n in wf["nodes"]:
        label = n["label"].replace('"', "'")
        out.append(f'  {n["id"].replace("-", "_")}["{label}"]')
    for e in wf["edges"]:
        tag = f"|{e['sourceHandle']}|" if e.get("sourceHandle") else ""
        out.append(f"  {e['from'].replace('-', '_')} -->{tag} {e['to'].replace('-', '_')}")
    out += ["```", ""]
    open(dst, "w", encoding="utf-8").write("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
