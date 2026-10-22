"""Compile exact Clifford+T state-preparation circuits for the 2-qubit LiH bond model.

Same circuit shape as generate_circuits.py,

    U0 q0 ; Ua q1 ; CX(q0, q1) ; Ub q1 ; CX(q0, q1)

but each single-qubit slot is an exact Clifford+T word instead of a dyadic rotation. Words are
enumerated in Matsumoto-Amano normal form, (T | e)(HT | SHT)^n C with C one of the 24 Cliffords,
up to NMAX syllables. For each slot the 5 words closest to the ideal Ry at every T count are kept:
U0 and Ua act on |0>, so only that state is matched; Ub is matched as a full unitary. Every
combination is then scored by its exact energy, and the most accurate circuit is written out.
Many combinations prepare the same state with different words, so they tie in energy; among all
combinations within TIE_HA of the lowest energy the circuit with the lowest T count, then the fewest
gates, then the first in enumeration order is chosen. This makes the choice independent of
floating-point noise.

Clifford+T circuits fall under the exact_clifford_t_v2 profile, where the exact unitary is
kernel-certified.

Writes into <outdir>: <name>_prep.lean, <name>_<basis>.lean (ZZ, XX, ZX, XZ), <name>_prep.ir.json,
<name>_report.json (the chosen words, gate and T counts, exact energy, and the full
T-count / error front).

Usage:  python generate_cliffordt.py <name> <R_angstrom> <outdir>
"""
import itertools
import json
import os
import sys

import numpy as np

from generate_circuits import BASES, hamiltonian, ir_document, lean_source, simulate

NMAX = 8
PER_T = 5
TIE_HA = 1e-9
PROFILE = "exact_clifford_t_v2"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

H = np.array([[1, 1], [1, -1]], complex) / np.sqrt(2)
MAT = {"H": H, "S": np.diag([1, 1j]), "T": np.diag([1, np.exp(1j * np.pi / 4)])}
CX = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], complex)


def word_matrix(seq):
    u = np.eye(2, dtype=complex)
    for g in seq:  # time order
        u = MAT[g] @ u
    return u


def cliffords():
    """The 24 single-qubit Cliffords mod global phase, each with its shortest H/S word."""
    out = []
    for n in range(7):
        for w in itertools.product("HS", repeat=n):
            u = word_matrix(w)
            if not any(abs(abs(np.trace(v.conj().T @ u)) - 2) < 1e-9 for _, v in out):
                out.append((list(w), u))
    assert len(out) == 24
    return out


def normal_form_words(nmax):
    words = []
    for pre in ([], ["T"]):
        for n in range(nmax + 1):
            for syl in itertools.product((["H", "T"], ["S", "H", "T"]), repeat=n):
                seq = pre + [g for s in syl for g in s]
                u = word_matrix(seq)
                for cw, cu in cliffords():
                    words.append((seq + cw, cu @ u, len(pre) + n))
    return words


PHASE = {"T": 1, "S": 2}
EXPAND = {1: ["T"], 2: ["S"], 3: ["S", "T"], 4: ["Z"], 5: ["Z", "T"], 6: ["Sdg"], 7: ["Sdg", "T"]}


def simplify(seq):
    """Merge adjacent diagonal gates (phase in units of pi/4, mod 8) and cancel H H."""
    toks = [g if g == "H" else PHASE[g] for g in seq]
    changed = True
    while changed:
        changed, out = False, []
        for t in toks:
            if out and t == "H" and out[-1] == "H":
                out.pop(); changed = True
            elif out and t != "H" and out[-1] != "H":
                out[-1] = (out[-1] + t) % 8; changed = True
            else:
                out.append(t)
        toks = [t for t in out if t != 0]
        changed = changed or len(toks) != len(out)
    return [g for t in toks for g in ([t] if t == "H" else EXPAND[t])]


def ry(t):
    return np.array([[np.cos(t / 2), -np.sin(t / 2)], [np.sin(t / 2), np.cos(t / 2)]], complex)


def circuit_energy(h, u0, ua, ub):
    s = np.zeros(4, complex)
    s[0] = 1
    s = CX @ np.kron(np.eye(2), ub) @ CX @ np.kron(u0, ua) @ s
    return float(np.real(s.conj() @ h @ s))


def main():
    name, R, outdir = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    ham = next(p for p in json.load(open(os.path.join(ROOT, "hamiltonians", "LiH_sto3g_2e2o_parity_tapered_bond_curve.json"),
                                         encoding="utf-8"))["points"] if p["R_angstrom"] == R)
    ang = next(p for p in json.load(open(os.path.join(ROOT, "results", "precision_budget.json"),
                                         encoding="utf-8"))["points"] if p["R_angstrom"] == R)["angles_rad"]
    h, e0 = hamiltonian(ham["terms"]), ham["exact_energy_hartree"]

    words = normal_form_words(NMAX)
    mats = np.array([w[1] for w in words])
    tcount = np.array([w[2] for w in words])
    glen = np.array([len(w[0]) for w in words])
    picks = []
    for key, full in (("t0", False), ("alpha", False), ("beta", True)):
        v = ry(ang[key])
        if full:
            d = 1 - np.abs(np.einsum("ij,nij->n", v.conj(), mats)) / 2
        else:
            d = 1 - np.abs(mats[:, :, 0] @ v[:, 0].conj()) ** 2
        sel = []
        for t in range(NMAX + 2):
            idx = np.where(tcount == t)[0]
            sel.extend(idx[np.argsort(d[idx] + 1e-6 * glen[idx], kind="stable")][:PER_T])
        picks.append(sel)

    front, scored = {}, []
    for i, j, k in itertools.product(*picks):
        e = circuit_energy(h, mats[i], mats[j], mats[k])
        t = int(tcount[i] + tcount[j] + tcount[k])
        if t not in front or e < front[t][0]:
            front[t] = (e, (i, j, k))
        scored.append((e, t, (i, j, k)))
    e_min = min(s[0] for s in scored)
    tied = [s for s in scored if s[0] <= e_min + TIE_HA]
    best = min(tied, key=lambda s: (s[1], sum(len(simplify(words[x][0])) for x in s[2])))  # stable: first wins

    slots = [simplify(words[x][0]) for x in best[2]]
    prep = [(g, 0) for g in slots[0]] + [(g, 1) for g in slots[1]] + [("CX", 0, 1)] + [(g, 1) for g in slots[2]] + [("CX", 0, 1)]
    s = simulate(prep)
    e_prep = float(np.real(s.conj() @ h @ s))
    assert abs(e_prep - best[0]) < 1e-12, (e_prep, best[0])

    t_total = sum(1 for o in prep if o[0] == "T")
    scope = f"LiH STO-3G (2e,2o) parity_tapered state preparation at R={R} A, exact Clifford+T synthesis, T-count {t_total}"
    for basis, tail in BASES.items():
        cid = f"{name}_{basis}"
        with open(os.path.join(outdir, f"{cid}.lean"), "w", encoding="utf-8") as fh:
            fh.write(lean_source(cid, prep + tail, PROFILE, scope + f", measure {basis.upper()}"))
    with open(os.path.join(outdir, f"{name}_prep.lean"), "w", encoding="utf-8") as fh:
        fh.write(lean_source(f"{name}_prep", prep, PROFILE, scope))
    with open(os.path.join(outdir, f"{name}_prep.ir.json"), "w", encoding="utf-8") as fh:
        json.dump(ir_document(f"{name}_prep", prep, PROFILE, scope), fh, indent=1)

    pareto, lowest = [], np.inf
    for t in sorted(front):
        if front[t][0] < lowest:
            lowest = front[t][0]
            pareto.append({"t_count": t, "dE_mHa": (front[t][0] - e0) * 1000})
    report = {"name": name, "R_angstrom": R, "semantic_profile": PROFILE, "method": "Matsumoto-Amano normal-form enumeration, "
              f"up to {NMAX} syllables per slot, {PER_T} closest words per T count per slot, exact energy scoring; "
              f"ties within {TIE_HA} Ha broken by T count, then gate count, then enumeration order",
              "tied_candidates": len(tied),
              "slot_words_time_order": {"q0_U0": slots[0], "q1_Ua": slots[1], "q1_Ub": slots[2]},
              "gate_count": len(prep), "cnot_count": 2, "t_count": t_total,
              "energy_hartree": e_prep, "exact_ground_hartree": e0, "dE_mHa": (e_prep - e0) * 1000,
              "statevector_q0q1": [[round(z.real, 12), round(z.imag, 12)] for z in s],
              "t_count_front": pareto}
    with open(os.path.join(outdir, f"{name}_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({k: report[k] for k in ("name", "gate_count", "t_count", "energy_hartree", "dE_mHa")}))
    for row in pareto:
        print(f"  T={row['t_count']:2d}  dE={row['dE_mHa']:.3f} mHa")


if __name__ == "__main__":
    main()
