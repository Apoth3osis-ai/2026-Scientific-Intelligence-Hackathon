"""Assemble the run report (REPORT.md) and the data file (run_data.json) from the saved results.

Every number comes from a file in this repo: the Chemistry Studio Hamiltonians and scans, the Math Engine
precision budget, the Clifford+T synthesis reports, the simulation counts (via simulated_energies.json),
the certificate receipts and the export index.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HA_KCAL = 627.509474


def load(*p):
    return json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))


ham = {p["R_angstrom"]: p for p in load("hamiltonians", "LiH_sto3g_2e2o_parity_tapered_bond_curve.json")["points"]}
budget = {p["R_angstrom"]: p for p in load("results", "precision_budget.json")["points"]}
sim = load("results", "simulated_energies.json")
exports = load("exports", "export_index.json")
CERTS = {"hf_a_k2": ("qpcert_a272d51fc2ea1e18", "certify_hf_a_k2_prep.json", "dyadic K=2 (Clifford)"),
         "r2p50_ct": ("qpcert_f47b8566cf85f0c6", "certify_r2p50_ct_prep.json", "Clifford+T"),
         "r3p00_ct": ("qpcert_f3f0c674daa1a372", "certify_r3p00_ct_prep.json", "Clifford+T")}
CERTIFIED_AT = {1.0: "hf_a_k2", 1.25: "hf_a_k2", 1.5: "hf_a_k2", 1.75: "hf_a_k2", 2.0: "hf_a_k2", 2.25: "hf_a_k2",
                2.5: "r2p50_ct", 3.0: "r3p00_ct"}


def circuit_facts(name):
    if name.endswith("_ct"):
        rep = load("circuits", name, name + "_report.json")
        return {"gates": rep["gate_count"], "t_count": rep["t_count"], "rzk_count": 0, "profile": rep["semantic_profile"]}
    s = next(c for c in load("circuits", "circuit_summary.json") if c["name"] == name)
    return {"gates": s["gate_count"], "t_count": s["t_count"], "rzk_count": s["rzk_count"], "profile": s["semantic_profile"]}


def receipt(name):
    cid, fname, kind = CERTS[name]
    r = json.load(open(os.path.join(ROOT, "certificates", "receipts", fname), encoding="utf-8"))

    def find(o):
        if isinstance(o, dict):
            if "replayed_theorems" in o:
                return o["replayed_theorems"]
            o = list(o.values())
        if isinstance(o, list):
            for v in o:
                got = find(v)
                if got is not None:
                    return got
        return None

    replayed = find(r) or []
    return {"certificate_id": cid, "kind": kind, "receipt": fname,
            "replayed_theorems": [t["theorem"].rsplit(".", 1)[1] for t in replayed],
            "axioms_used": sorted({a for t in replayed for a in t["axioms"]})}


rows = []
for R in sorted(ham):
    h, b = ham[R], budget[R]
    c = CERTIFIED_AT[R]
    s = next(x for x in sim if x["circuit"] == c and x["R_angstrom"] == R)
    rows.append({"R_angstrom": R, "E_hf": h["hf_energy_hartree"], "E_exact": h["exact_energy_hartree"],
                 "K_star": b["K_star"], "certified_circuit": c, **circuit_facts(c),
                 "E_circuit_exact": s["E_circuit_exact"], "E_simulated": s["E_simulated"], "SE": s["SE"],
                 "z": s["z_vs_prediction"], "error_vs_exact_mHa": s["error_vs_exact_mHa"],
                 "hf_error_mHa": (h["hf_energy_hartree"] - h["exact_energy_hartree"]) * 1000})
study = [s for s in sim if s["circuit"] in ("r1p50_k8", "r2p50_k5", "r3p00_k5", "r3p00_k8")]

eq_exact = min(rows, key=lambda r: r["E_exact"])
eq_sim = min(rows, key=lambda r: r["E_simulated"])
rise_exact = (rows[-1]["E_exact"] - eq_exact["E_exact"]) * HA_KCAL
rise_sim = (rows[-1]["E_simulated"] - eq_sim["E_simulated"]) * HA_KCAL
certs = {name: receipt(name) for name in CERTS}

data = {"workflow": "Replicate and Certify a Quantum Chemistry Result (AgentPMT 6ada7c48e001971070f3313a)",
        "model": "LiH, STO-3G, Li 1s frozen, 2 electrons in 2 orbitals, parity_tapered, 2 qubits",
        "bond_curve": rows, "precision_study_circuits": study, "certificates": certs, "exports": exports,
        "equilibrium": {"exact_R": eq_exact["R_angstrom"], "simulated_R": eq_sim["R_angstrom"]},
        "rise_to_3A_kcal_mol": {"exact": rise_exact, "simulated": rise_sim}}
json.dump(data, open(os.path.join(HERE, "run_data.json"), "w", encoding="utf-8"), indent=1)

L = ["# Run report: LiH bond curve with certified exact-gate circuits", "",
     "Produced by the AgentPMT workflow *Replicate and Certify a Quantum Chemistry Result* (v1.1.0) on 2026-10-22.",
     "All numbers below are also in `run_data.json`.", "",
     "## Replication", "",
     "arXiv [2606.05968v1](https://arxiv.org/abs/2606.05968v1) reports a total LiH ground-state energy of -7.857385 Ha at R = 1.696 A "
     "(frozen core, (2e,5o), Bravyi-Kitaev, 10 qubits) and calls it the FCI limit.", "",
     "**Assumption: the basis set.** The paper does not state it. We assume STO-3G, which is strongly supported: all four components "
     "of the paper's energy breakdown (total, frozen-core shift, active-space energy, nuclear repulsion) match the STO-3G "
     "restricted Hartree-Fock decomposition to within 7e-7 Ha. It is still an inference.", "",
     "Under that assumption, Chemistry Studio gives RHF = -7.857384707 Ha, CASCI(2e,5o) = -7.879357455 Ha and "
     "all-electron FCI = -7.879592768 Ha. **The reported total is the Hartree-Fock energy; the exact ground state of the stated "
     "active space is 21.97 mHa lower.**", "",
     "**Reference state.** Under Bravyi-Kitaev, counting 1s does not count electrons, so the stated reference `|1111000000>` was "
     "decoded explicitly. Under the Fenwick-tree convention that reproduces the tool's Hartree-Fock bitstring `1000000000`, it is "
     "the 4-electron occupation `1011000100`. Under the other standard readings it is two same-spin electrons, or four electrons "
     "read as Jordan-Wigner. None is the Hartree-Fock state, but the exact implementation error is not established. "
     "Details: `../paper-replication/`.", "",
     "## Bond curve (2-qubit model)", "",
     "| R (A) | E_HF (Ha) | E_exact (Ha) | Certified circuit | Gates | T | E_sim (Ha) | SE (mHa) | z | Error vs exact (mHa) | HF error (mHa) |",
     "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append(f"| {r['R_angstrom']} | {r['E_hf']:.6f} | {r['E_exact']:.6f} | `{r['certified_circuit']}` | {r['gates']} | {r['t_count']} | "
             f"{r['E_simulated']:.6f} | {r['SE']*1000:.3f} | {r['z']:+.2f} | {r['error_vs_exact_mHa']:+.3f} | {r['hf_error_mHa']:.3f} |")
L += ["", f"Every simulated energy agrees with its circuit's exact energy within shot noise (largest |z| = {max(abs(r['z']) for r in rows):.2f}) "
      f"and lies within chemical accuracy (1.6 mHa) of the exact model energy (largest error {max(r['error_vs_exact_mHa'] for r in rows):.3f} mHa). "
      f"Hartree-Fock misses by {rows[-2]['hf_error_mHa']:.2f} mHa at 2.5 A and {rows[-1]['hf_error_mHa']:.2f} mHa at 3.0 A.", "",
      "From 1.0 to 2.25 A the precision budget gives K* = 2: the Hartree-Fock state is already within chemical accuracy, so the certified circuit "
      "is the 19-gate Clifford preparation of that state, and those six points share one set of counts (hence the same z). "
      "From 2.5 A on, static correlation grows, and the certified Clifford+T circuits recover it.", "",
      f"Equilibrium: R = {eq_exact['R_angstrom']} A on the exact curve and R = {eq_sim['R_angstrom']} A on the simulated curve (grid of 8 points). "
      f"Energy rise from equilibrium to 3.0 A: {rise_exact:.2f} kcal/mol exact, {rise_sim:.2f} kcal/mol simulated. "
      "The 3.0 A point is not yet full dissociation.", "",
      "## Precision study circuits (simulated and exported)", "",
      "| Circuit | R (A) | Grid | E_sim (Ha) | SE (mHa) | z | Error vs exact (mHa) |", "|---|---|---|---|---|---|---|"]
for s in sorted(study, key=lambda x: (x["R_angstrom"], x["K"])):
    L.append(f"| `{s['circuit']}` | {s['R_angstrom']} | K = {s['K']} | {s['E_simulated']:.6f} | {s['SE']*1000:.3f} | {s['z_vs_prediction']:+.2f} | {s['error_vs_exact_mHa']:+.3f} |")
L += ["", "The full dyadic precision budget (K = 2..10 at every bond length) is in `precision_budget.json`; the Clifford+T T-count fronts are in `../circuits/*_ct/*_report.json`.", "",
      "## Certificates", "", "| Circuit | Kind | Certificate | Kernel-replayed theorems | Axioms |", "|---|---|---|---|---|"]
for name, c in certs.items():
    L.append(f"| `{name}` | {c['kind']} | `{c['certificate_id']}` | {', '.join(c['replayed_theorems'])} | {c['axioms_used'] or 'none'} |")
L += ["", f"Exported programs: {len(exports)} (OpenQASM 3 and Qiskit for 7 circuits), all with `exact_readback_checked: true`. Index: `../exports/export_index.json`.", "",
      "## What is proven and what is not", "",
      "- **Proven (Lean kernel, no axioms):** each certified circuit is well formed in `exact_clifford_t_v2`, and its exact unitary is the one the certificate states. Every point on the curve uses a certified circuit.",
      "- **Computed exactly (not a proof):** the energy of each circuit's state, from the Chemistry Studio Hamiltonian.",
      "- **Observed (simulation):** the Qiskit Aer and Stim energies from 65,536 shots per basis, which agree with the exact circuit energies within shot noise.",
      "- **Not claimed:** anything about the chemistry beyond the stated model (STO-3G, (2e,2o)), and anything about hardware execution."]
open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
