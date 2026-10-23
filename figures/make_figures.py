"""Figures for the LiH bond-curve run (matplotlib, static PNG).

fig1_bond_curve.png      (a) LiH STO-3G potential energy curve: 2-qubit model exact (CASCI(2e,2o)),
                         Hartree-Fock, and the simulated energy of each certified circuit.
                         (b) error against the model exact energy, with chemical accuracy marked.
fig2_precision.png       (a) dyadic rotation grid: energy error against K at 2.5 and 3.0 A.
                         (b) exact Clifford+T synthesis: energy error against T count.
fig3_circuit_r3p00_ct.png the certified 49-gate Clifford+T state preparation at 3.0 A.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"
CHEM_ACC = 1.6

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED, "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "legend.labelcolor": INK2, "axes.titlecolor": INK, "axes.titlesize": 9.5, "axes.titleweight": "bold",
    "axes.titlelocation": "left",
})


def load(*p):
    return json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))


ref = {p["R_angstrom"]: p for p in load("hamiltonians", "LiH_sto3g_2e2o_parity_tapered_bond_curve.json")["points"]}
scan = [row.split(",") for row in open(os.path.join(ROOT, "results", "reference_curves_LiH_sto3g.csv"), encoding="utf-8").read().split("\n")[1:] if row]
R_scan = [float(r[0]) for r in scan]
E_cas = [float(r[2]) for r in scan]
E_hf = [float(r[3]) for r in scan]
sim = load("results", "simulated_energies.json")
CERTIFIED = {"hf_a_k2", "r2p50_ct", "r3p00_ct"}
cert = sorted([s for s in sim if s["circuit"] in CERTIFIED], key=lambda s: s["R_angstrom"])


def fig1():
    fig, (a, b) = plt.subplots(2, 1, figsize=(6.4, 5.6), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]})
    a.plot(R_scan, E_cas, color=BLUE, lw=2, label="Exact, 2-qubit model (CASCI(2e,2o))", zorder=2)
    a.plot(R_scan, E_hf, color=ORANGE, lw=2, label="Hartree-Fock", zorder=2)
    a.plot([s["R_angstrom"] for s in cert], [s["E_simulated"] for s in cert], "o", ms=7, mfc=INK, mec=SURFACE,
           mew=1.5, label="Certified circuit, simulated (Qiskit Aer / Stim)", zorder=3)
    a.set_xlim(0.9, 3.2)
    a.set_ylim(-7.89, -7.69)
    a.set_ylabel("Energy (Ha)")
    a.set_title("a  LiH bond curve, STO-3G, 2 qubits")
    a.legend(loc="lower right", fontsize=8)

    b.axhspan(0, CHEM_ACC, color="#cde2fb", alpha=0.6, lw=0, zorder=0)
    b.text(0.95, CHEM_ACC - 0.12, "chemical accuracy (1.6 mHa)", color=INK2, fontsize=8, va="top")
    Rh = sorted(ref)
    hf_err = [(ref[r]["hf_energy_hartree"] - ref[r]["exact_energy_hartree"]) * 1000 for r in Rh]
    b.plot(Rh, hf_err, color=ORANGE, lw=2, marker="s", ms=5, mfc=ORANGE, mec=SURFACE, label="Hartree-Fock", zorder=2)
    b.errorbar([s["R_angstrom"] for s in cert], [s["error_vs_exact_mHa"] for s in cert],
               yerr=[s["SE"] * 1000 for s in cert], fmt="o", ms=7, mfc=INK, mec=SURFACE, mew=1.5, ecolor=INK,
               elinewidth=1.2, capsize=3, label="Certified circuit, simulated (1 SE)", zorder=3)
    b.set_ylim(-0.5, 4.0)
    b.text(2.62, 3.55, f"HF reaches {hf_err[-1]:.1f} mHa at 3.0 Å", color=ORANGE, fontsize=8)
    b.set_xlabel("Li–H distance R (Å)")
    b.set_ylabel("Error vs exact (mHa)")
    b.set_title("b  Error against the exact model energy")
    b.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig1_bond_curve.png"), dpi=200)


def fig2():
    budget = {p["R_angstrom"]: p for p in load("results", "precision_budget.json")["points"]}
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.4, 2.9), sharey=True)
    for R, col in ((2.5, BLUE), (3.0, ORANGE)):
        ks = [x["K"] for x in budget[R]["by_K"]]
        de = [max(x["dE_mHa"], 1e-4) for x in budget[R]["by_K"]]
        a.plot(ks, de, color=col, lw=2, marker="o", ms=5, mec=SURFACE, label=f"R = {R} Å")
        rep = load("circuits", "r2p50_ct" if R == 2.5 else "r3p00_ct", ("r2p50_ct" if R == 2.5 else "r3p00_ct") + "_report.json")
        front = rep["t_count_front"]
        b.plot([f["t_count"] for f in front], [f["dE_mHa"] for f in front], color=col, lw=2, marker="o", ms=5,
               mec=SURFACE, drawstyle="steps-post", label=f"R = {R} Å")
        b.plot([rep["t_count"]], [rep["dE_mHa"]], "o", ms=9, mfc="none", mec=INK, mew=1.5, zorder=4)
    for ax in (a, b):
        ax.set_yscale("log")
        ax.axhline(CHEM_ACC, color=INK2, lw=1, ls=(0, (4, 3)))
        ax.set_ylim(1e-4, 100)
    a.text(10, CHEM_ACC * 1.35, "chemical accuracy", color=INK2, fontsize=8, ha="right")
    a.set_xlabel(r"Rotation grid $K$ (angles in steps of $2\pi/2^K$)")
    a.set_ylabel("Energy error (mHa)")
    a.set_title("a  Dyadic exact rotations")
    a.legend(loc="lower left", fontsize=8)
    b.set_xlabel("T count (exact Clifford+T)")
    b.set_title("b  Certified Clifford+T synthesis")
    b.annotate("certified circuits", xy=(17, 0.07), xytext=(7.5, 0.006), color=INK2, fontsize=8,
               arrowprops={"arrowstyle": "->", "color": INK2, "lw": 1})
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig2_precision.png"), dpi=200)


def fig3():
    ir = load("circuits", "r3p00_ct", "r3p00_ct_prep.ir.json")
    col = {"q0": 0, "q1": 0}
    placed = []
    for op in ir["operations"]:
        if op["gate"] == "cx":
            c = max(col.values())
            placed.append(("cx", None, c))
            col = {"q0": c + 1, "q1": c + 1}
        else:
            q = op["targets"][0]
            placed.append((op["gate"], q, col[q]))
            col[q] += 1
    width = max(col.values())
    fig, ax = plt.subplots(figsize=(6.4, 1.35))
    ax.set_xlim(-4.2, width + 0.2)
    ax.set_ylim(-0.7, 1.7)
    ax.axis("off")
    y = {"q0": 1, "q1": 0}
    for q in y:
        ax.plot([-0.8, width - 0.4], [y[q]] * 2, color=INK2, lw=0.8, zorder=1)
        ax.text(-4.1, y[q], f"{q}  |0⟩", va="center", fontsize=7.5, color=INK2)
    label = {"h": "H", "s": "S", "sdg": "S†", "t": "T", "z": "Z"}
    for g, q, c in placed:
        if g == "cx":
            ax.plot([c, c], [0, 1], color=INK, lw=1, zorder=2)
            ax.plot(c, 1, "o", ms=3.5, color=INK, zorder=3)
            ax.plot(c, 0, "o", ms=8, mfc=SURFACE, mec=INK, mew=1, zorder=3)
            ax.plot([c - 0.2, c + 0.2], [0, 0], color=INK, lw=1, zorder=4)
            ax.plot([c, c], [-0.2, 0.2], color=INK, lw=1, zorder=4)
        else:
            fc = "#fde3d8" if g == "t" else "#e8f1fc"
            ec = ORANGE if g == "t" else BLUE
            ax.add_patch(plt.Rectangle((c - 0.38, y[q] - 0.3), 0.76, 0.6, fc=fc, ec=ec, lw=0.8, zorder=2))
            ax.text(c, y[q], label[g], ha="center", va="center", fontsize=6, color=INK, zorder=3)
    n_t = sum(1 for op in ir["operations"] if op["gate"] == "t")
    ax.text(-4.1, 1.55, f"Certified 3.0 Å state preparation: {len(ir['operations'])} gates, T count {n_t}, qpcert_f3f0c674daa1a372",
            fontsize=7.5, color=INK, fontweight="bold")
    fig.tight_layout(pad=0.2)
    fig.savefig(os.path.join(HERE, "fig3_circuit_r3p00_ct.png"), dpi=220)


def fig_workflow():
    """The workflow graph: reasoning steps in grey, tool steps coloured with the tool named."""
    wf = load("workflow", "workflow.json")
    tool_name = {"6ada7145e001971070f33005": "Valency", "69644454288e0324fa542102": "Web Browser",
                 "6ada6971e001971070f32f9a": "Chemistry Studio", "689df4ac8ee2d1dd79e9035b": "Math Engine",
                 "6a7e5036b8c970a6773201b5": "Quantum Circuit\nBuilder with Proof", "6948b078b54506f955d789ed": "File Management"}
    short = {"set-question": "Set the question", "find-papers": "Find papers", "shortlist": "Shortlist",
             "read-paper": "Read full text", "extract-claims": "Extract inputs\nand claims", "reproduce": "Reproduce\nthe chemistry",
             "consistency": "Check the\npaper's numbers", "reference-curve": "Reference\nbond curve",
             "point-hamiltonian": "Qubit\nHamiltonian", "point-budget": "Precision\nbudget", "point-cliffordt": "Clifford+T\nsynthesis",
             "point-circuits": "Simulate, export,\ncertify", "point-energy": "Energy from\ncounts", "assemble": "Assemble\nreport",
             "save-files": "Save files", "final-report": "Report"}
    nodes = {n["id"]: n for n in wf["nodes"]}
    rows = [["set-question", "find-papers", "shortlist", "read-paper"],
            ["extract-claims", "reproduce", "consistency", "reference-curve"],
            ["point-hamiltonian", "point-budget", "point-cliffordt", "point-circuits", "point-energy"],
            ["assemble", "save-files", "final-report"]]
    fig, ax = plt.subplots(figsize=(6.4, 4.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.4)
    ax.axis("off")
    W, Hh = 1.72, 1.05
    ys = [7.2, 5.25, 3.1, 0.95]
    pos = {}
    for r, ids in enumerate(rows):
        n = len(ids)
        gap = (10 - 0.4 - n * W) / (n - 1) if n > 1 else 0
        for i, nid in enumerate(ids):
            pos[nid] = (0.2 + i * (W + gap), ys[r])
    loop_ids = rows[2]
    x0 = pos[loop_ids[0]][0] - 0.12
    x1 = pos[loop_ids[-1]][0] + W + 0.12
    ax.add_patch(matplotlib.patches.FancyBboxPatch((x0, ys[2] - 0.62), x1 - x0, Hh + 0.95, boxstyle="round,pad=0.02,rounding_size=0.15",
                                                   fc="#f4f8fe", ec=BLUE, lw=0.9, ls=(0, (3, 2)), zorder=0))
    ax.text(x1 - 0.1, ys[2] + Hh + 0.12, "For each bond length", fontsize=7.5, color=BLUE, fontweight="bold", ha="right")
    for nid, (x, y) in pos.items():
        n = nodes[nid]
        is_tool = n["type"] == "tool"
        fc, ec = ("#e8f1fc", BLUE) if is_tool else ("#f0efec", AXIS)
        ax.add_patch(matplotlib.patches.FancyBboxPatch((x, y - Hh / 2), W, Hh, boxstyle="round,pad=0.02,rounding_size=0.08",
                                                       fc=fc, ec=ec, lw=1.0, zorder=2))
        if is_tool:
            ax.text(x + W / 2, y + 0.17, short[nid], ha="center", va="center", fontsize=6.6, color=INK, zorder=3, linespacing=1.05)
            ax.text(x + W / 2, y - 0.33, tool_name[n["tool"]["product_id"]], ha="center", va="center", fontsize=5.6,
                    color=BLUE, fontweight="bold", zorder=3, linespacing=1.0)
        else:
            ax.text(x + W / 2, y, short[nid], ha="center", va="center", fontsize=6.6, color=INK2, zorder=3, linespacing=1.05)
    arrow = {"arrowstyle": "-|>", "color": INK2, "lw": 0.9, "shrinkA": 0, "shrinkB": 0, "mutation_scale": 7}
    for ids in rows:
        for a, b in zip(ids, ids[1:]):
            (xa, ya), (xb, yb) = pos[a], pos[b]
            ax.annotate("", xy=(xb, yb), xytext=(xa + W, ya), arrowprops=arrow, zorder=1)
    for ra, rb in zip(rows, rows[1:]):
        (xa, ya), (xb, yb) = pos[ra[-1]], pos[rb[0]]
        mid = (ya - Hh / 2 + ys[2] + Hh + 0.33) / 2 if rb is rows[2] else (ya - Hh / 2 + yb + Hh / 2) / 2
        ax.plot([xa + W / 2, xa + W / 2, xb + W / 2], [ya - Hh / 2, mid, mid], color=INK2, lw=0.9, zorder=1)
        ax.annotate("", xy=(xb + W / 2, yb + Hh / 2 + (0.05 if rb is not rows[2] else 0.0)), xytext=(xb + W / 2, mid), arrowprops=arrow, zorder=1)
    ax.add_patch(matplotlib.patches.Rectangle((0.2, 8.05), 0.32, 0.22, fc="#e8f1fc", ec=BLUE, lw=1.0))
    ax.text(0.6, 8.16, "AgentPMT tool step", fontsize=7, color=INK2, va="center")
    ax.add_patch(matplotlib.patches.Rectangle((3.0, 8.05), 0.32, 0.22, fc="#f0efec", ec=AXIS, lw=1.0))
    ax.text(3.4, 8.16, "Agent reasoning step", fontsize=7, color=INK2, va="center")
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(HERE, "fig0_workflow.png"), dpi=220)


if __name__ == "__main__":
    fig_workflow()
    fig1()
    fig2()
    fig3()
    print("wrote fig0_workflow.png, fig1_bond_curve.png, fig2_precision.png, fig3_circuit_r3p00_ct.png")
