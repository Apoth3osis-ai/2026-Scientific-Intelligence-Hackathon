"""Energies from measurement counts (simulation_runs.json) for every bond length.

<P> = sum_keys (-1)^(sum of key[i] over the support of P) * count / shots, with key[i] = qubit i.
Each Pauli term is read from the basis circuit that diagonalizes it (ZZ, XX, ZX, XZ).
The standard error combines the per-basis sample covariances of the grouped terms.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
runs = json.load(open(os.path.join(ROOT, "simulations", "simulation_runs.json"), encoding="utf-8"))
ham = {p["R_angstrom"]: p for p in json.load(open(os.path.join(ROOT, "hamiltonians", "LiH_sto3g_2e2o_parity_tapered_bond_curve.json"), encoding="utf-8"))["points"]}
budget = {p["R_angstrom"]: p for p in json.load(open(os.path.join(HERE, "precision_budget.json"), encoding="utf-8"))["points"]}

def basis_for(label):
    f = ["Z", "Z"]
    if label != "I":
        for t in label.split():
            f[int(t[1:])] = t[0]
    return "".join(f)

def term_samples(label, counts):
    """Per-shot eigenvalue samples (+1/-1) of a Pauli term, as (values, weights)."""
    support = [] if label == "I" else [int(t[1:]) for t in label.split()]
    vals, w = [], []
    for key, c in counts.items():
        vals.append((-1) ** sum(int(key[i]) for i in support)); w.append(c)
    return np.array(vals, float), np.array(w, float)

def energy(terms, by_basis):
    e, var = 0.0, 0.0
    groups = {}
    for label, c in terms:
        if label == "I":
            e += c; continue
        groups.setdefault(basis_for(label), []).append((label, c))
    for b, items in groups.items():
        counts = by_basis[b]
        shots = sum(counts.values())
        keys = list(counts)
        p = np.array([counts[k] for k in keys], float) / shots
        # per-outcome value of the grouped observable sum_c c*P
        obs = np.zeros(len(keys))
        for label, c in items:
            support = [int(t[1:]) for t in label.split()]
            obs += c * np.array([(-1) ** sum(int(k[i]) for i in support) for k in keys])
        mean = float(p @ obs)
        e += mean
        var += float(p @ (obs - mean) ** 2) / shots
    return e, var ** 0.5

circuits = {"hf_a_k2": [1.0, 1.25, 1.5, 1.75, 2.0, 2.25], "r2p50_k5": [2.5], "r3p00_k5": [3.0], "r1p50_k8": [1.5], "r3p00_k8": [3.0],
            "r2p50_ct": [2.5], "r3p00_ct": [3.0]}
rows = []
for circ, Rs in circuits.items():
    by_basis = {r["basis"]: r["counts"] for r in runs if r["circuit_id"].startswith(circ + "_")}
    if len(by_basis) < 4:
        continue
    backend = sorted({r["backend_id"] for r in runs if r["circuit_id"].startswith(circ + "_")})
    # dyadic-grid circuits (_k<K>) take their exact energy from the precision budget; Clifford+T
    # circuits (_ct) from the synthesis report written by circuits/generate_cliffordt.py
    K = int(circ.split("_k")[1]) if "_k" in circ else None
    for R in Rs:
        h = ham[R]
        e, se = energy(h["terms"], by_basis)
        if K is None:
            rep = json.load(open(os.path.join(ROOT, "circuits", circ, circ + "_report.json"), encoding="utf-8"))
            e_pred = rep["energy_hartree"]
        else:
            dEK = next(x["dE_mHa"] for x in budget[R]["by_K"] if x["K"] == K)
            e_pred = h["exact_energy_hartree"] + dEK / 1000.0
        rows.append({"R_angstrom": R, "circuit": circ, "K": K, "backend": "+".join(backend),
                     "E_hf": h["hf_energy_hartree"], "E_exact": h["exact_energy_hartree"], "E_circuit_exact": e_pred,
                     "E_simulated": e, "SE": se, "z_vs_prediction": (e - e_pred) / se if se > 0 else 0.0,
                     "error_vs_exact_mHa": (e - h["exact_energy_hartree"]) * 1000})
for r in sorted(rows, key=lambda x: (x["R_angstrom"], x["K"] or 99)):
    grid = f"K={r['K']}" if r["K"] else "C+T"
    print(f"R={r['R_angstrom']:<5} {r['circuit']:9s} {grid:3s} {r['backend']:10s} E_sim={r['E_simulated']:.6f} +/- {r['SE']*1000:.3f} mHa | E_circ(exact)={r['E_circuit_exact']:.6f} z={r['z_vs_prediction']:+.2f} | E_exact={r['E_exact']:.6f} err={r['error_vs_exact_mHa']:+.3f} mHa")
json.dump(rows, open(os.path.join(HERE, "simulated_energies.json"), "w", encoding="utf-8"), indent=1)
