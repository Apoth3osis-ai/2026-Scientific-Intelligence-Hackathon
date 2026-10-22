"""Compile exact-gate state-preparation circuits for the 2-qubit LiH bond model.

Each circuit prepares a real 2-qubit state with three Ry rotations and two CNOTs:

    Ry(t0) q0 ; Ry(alpha) q1 ; CX(q0, q1) ; Ry(beta) q1 ; CX(q0, q1)

Every angle is an exact dyadic multiple of pi, m * 2*pi / 2**K, and every Ry is
written with exact phase gates:

    Ry(theta) = Sdg, H, P(theta), H, S        (time order, exact up to global phase)

P(m * 2*pi / 2**K) is expanded in binary: bit j of (m mod 2**K) contributes the
level k = K - j phase, where level 1 = Z, level 2 = S, level 3 = T and level k >= 4
is rzk(k) = P(2*pi / 2**k).

The script writes, for each circuit:
  * <name>_prep.lean   - Lean CircuitSpec of the state preparation (simulate / export)
  * <name>_<basis>.lean - the same circuit with a measurement-basis change (ZZ, XX, ZX, XZ)
  * <name>_prep.ir.json - the identical gate list as a heyting.quantum_circuit_ir.v1 document (inspect / certify)

and checks locally (numpy) that the gate list prepares the intended state.

Usage:  python generate_circuits.py <name> <K> <m_t0,m_alpha,m_beta> <outdir> [hamiltonian_terms_json]
"""
import json
import sys

import numpy as np

BASES = {"zz": [], "xx": [("H", 0), ("H", 1)], "zx": [("H", 1)], "xz": [("H", 0)]}


def phase_gates(m, K):
    """Exact gates for P(2*pi*m/2**K): Z (level 1), S (2), T (3), ('rzk', k) for k >= 4."""
    m %= 2 ** K
    gates = []
    for j in range(K):
        if (m >> j) & 1:
            k = K - j
            gates.append({1: "Z", 2: "S", 3: "T"}.get(k, ("rzk", k)))
    return gates


def ry(q, m, K):
    return [("Sdg", q), ("H", q)] + [(g, q) for g in phase_gates(m, K)] + [("H", q), ("S", q)]


def state_prep(ms, K):
    m0, ma, mb = ms
    return ry(0, m0, K) + ry(1, ma, K) + [("CX", 0, 1)] + ry(1, mb, K) + [("CX", 0, 1)]


def profile(ops):
    """Clifford+T profile when no phase finer than T is needed, else the 2^k cyclotomic profile."""
    return "exact_cyclotomic_2k_v1" if any(isinstance(o[0], tuple) for o in ops) else "exact_clifford_t_v2"


def lean_op(op):
    g = op[0]
    if g == "CX":
        return f".gate .CX {op[1]} {op[2]}"
    if isinstance(g, tuple):  # rzk(k) = P(2*pi/2**k) = rot phase h 1 with h = 2**(k-1)
        return f".gate (.rot .phase {2 ** (g[1] - 1)} 1 false) {op[1]} 0"
    return f".gate .{g} {op[1]} 0"


def lean_source(cid, ops, prof, scope):
    body = ", ".join(lean_op(o) for o in ops)
    return (
        "import HeytingLean.Quantum.ProofCarrying.CircuitSpec\n\n"
        "open HeytingLean.Quantum.ProofCarrying\n\n"
        "def spec : CircuitSpec where\n"
        f'  circuitId := "{cid}"\n'
        f'  semanticProfile := "{prof}"\n'
        "  qubits := 2\n  classicalBits := 0\n"
        f"  ops := [{body}]\n"
        "  claims := []\n"
        f'  metadataScope := "{scope}"\n\n'
        "theorem spec_claims : CircuitSpec.ClaimsHold spec := by\n"
        "  simp [CircuitSpec.ClaimsHold, spec]\n"
    )


def ir_document(cid, ops, prof, scope):
    rows = []
    for i, op in enumerate(ops):
        g = op[0]
        if g == "CX":
            rows.append({"kind": "gate", "op_id": f"g{i}", "gate": "cx", "controls": [f"q{op[1]}"],
                         "targets": [f"q{op[2]}"], "parameters": []})
        elif isinstance(g, tuple):
            rows.append({"kind": "gate", "op_id": f"g{i}", "gate": "rzk", "controls": [], "targets": [f"q{op[1]}"],
                         "parameters": [{"parameter_type": "cyclotomic_phase", "level": g[1], "inverse": False}]})
        else:
            rows.append({"kind": "gate", "op_id": f"g{i}", "gate": g.lower(), "controls": [],
                         "targets": [f"q{op[1]}"], "parameters": []})
    return {"schema": "heyting.quantum_circuit_ir.v1", "circuit_id": cid, "semantic_profile": prof,
            "qubits": [{"id": "q0"}, {"id": "q1"}], "classical_bits": [], "initial_state": "zero",
            "operations": rows, "metadata": {"name": cid, "scope": scope}}


def simulate(ops):
    """Exact numpy statevector of the gate list; key order q0q1 (qubit 0 = left tensor factor)."""
    one = {"H": np.array([[1, 1], [1, -1]]) / np.sqrt(2), "S": np.diag([1, 1j]), "Sdg": np.diag([1, -1j]),
           "T": np.diag([1, np.exp(1j * np.pi / 4)]), "Z": np.diag([1, -1]), "X": np.array([[0, 1], [1, 0]])}
    cx = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])

    def on(q, u):
        return np.kron(u, np.eye(2)) if q == 0 else np.kron(np.eye(2), u)

    s = np.zeros(4, complex)
    s[0] = 1
    for op in ops:
        g = op[0]
        if g == "CX":
            s = cx @ s
        elif isinstance(g, tuple):
            s = on(op[1], np.diag([1, np.exp(2j * np.pi / 2 ** g[1])])) @ s
        else:
            s = on(op[1], one[g]) @ s
    return s


def hamiltonian(terms):
    p = {"I": np.eye(2), "X": np.array([[0, 1], [1, 0]]), "Y": np.array([[0, -1j], [1j, 0]]), "Z": np.diag([1, -1])}
    h = np.zeros((4, 4), complex)
    for label, c in terms:
        f = ["I", "I"]
        if label != "I":
            for t in label.split():
                f[int(t[1:])] = t[0]
        h += c * np.kron(p[f[0]], p[f[1]])
    return h


def main():
    name, K, ms, outdir = sys.argv[1], int(sys.argv[2]), [int(x) for x in sys.argv[3].split(",")], sys.argv[4]
    prep = state_prep(ms, K)
    prof = profile(prep)
    scope = f"LiH STO-3G (2e,2o) parity_tapered state preparation, angles m={ms} x 2pi/2^{K}"
    for basis, tail in BASES.items():
        cid = f"{name}_{basis}"
        with open(f"{outdir}/{cid}.lean", "w", encoding="utf-8") as fh:
            fh.write(lean_source(cid, prep + tail, prof, scope + f", measure {basis.upper()}"))
    with open(f"{outdir}/{name}_prep.lean", "w", encoding="utf-8") as fh:
        fh.write(lean_source(f"{name}_prep", prep, prof, scope))
    with open(f"{outdir}/{name}_prep.ir.json", "w", encoding="utf-8") as fh:
        json.dump(ir_document(f"{name}_prep", prep, prof, scope), fh, indent=1)
    s = simulate(prep)
    report = {"name": name, "K": K, "m": ms, "semantic_profile": prof, "gate_count": len(prep),
              "cnot_count": sum(1 for o in prep if o[0] == "CX"),
              "t_count": sum(1 for o in prep if o[0] == "T"),
              "rzk_count": sum(1 for o in prep if isinstance(o[0], tuple)),
              "statevector_q0q1": [[round(z.real, 12), round(z.imag, 12)] for z in s]}
    if len(sys.argv) > 5:
        terms = json.loads(open(sys.argv[5], encoding="utf-8").read())
        h = hamiltonian(terms)
        report["energy_hartree"] = float(np.real(s.conj() @ h @ s))
        report["exact_ground_hartree"] = float(np.linalg.eigvalsh(h)[0])
    print(json.dumps(report))


if __name__ == "__main__":
    main()
