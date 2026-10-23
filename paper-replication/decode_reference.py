"""Decode the paper's reference bitstring |1111000000> into orbital occupations.

Under the Bravyi-Kitaev (BK) encoding a qubit stores a parity of several occupation numbers, so the number
of 1s in a BK bitstring is not the number of electrons. This script inverts the encoding explicitly.

BK convention: the Fenwick-tree form (as in OpenFermion), where qubit j stores the parity of modes
(j - lowbit(j+1), j]. Under this convention, with qubit 0 first and interleaved spin orbitals, the 2-electron
Hartree-Fock occupation 1100000000 encodes to 1000000000, which is exactly the HF bitstring Chemistry Studio
returns for this system. The script also reports the reversed qubit order, block spin order and a plain
Jordan-Wigner (occupation) reading, so the conclusion does not hang on one convention.
"""
import json
import os

import numpy as np

N_MODES = 10
PAPER_REF = "1111000000"


def bk_matrix(n):
    B = np.zeros((n, n), dtype=int)
    for j in range(n):
        low = (j + 1) & -(j + 1)
        B[j, j - low + 1: j + 1] = 1
    return B


def gf2_inverse(M):
    n = len(M)
    A = np.concatenate([M % 2, np.eye(n, dtype=int)], axis=1)
    for c in range(n):
        p = next(r for r in range(c, n) if A[r, c])
        A[[c, p]] = A[[p, c]]
        for r in range(n):
            if r != c and A[r, c]:
                A[r] ^= A[c]
    return A[:, n:]


def describe(occ, spin_order):
    if spin_order == "interleaved":
        alpha = [m // 2 for m in range(N_MODES) if occ[m] and m % 2 == 0]
        beta = [m // 2 for m in range(N_MODES) if occ[m] and m % 2 == 1]
    else:  # block: modes 0..4 spin-up, 5..9 spin-down
        h = N_MODES // 2
        alpha = [m for m in range(h) if occ[m]]
        beta = [m - h for m in range(h, N_MODES) if occ[m]]
    return {"occupation": "".join(map(str, occ)), "electrons": int(sum(occ)), "alpha_orbitals": alpha,
            "beta_orbitals": beta, "Sz": (len(alpha) - len(beta)) / 2}


def main():
    B = bk_matrix(N_MODES)
    Binv = gf2_inverse(B)
    hf_occ = np.array([1, 1] + [0] * (N_MODES - 2))
    hf_bk = "".join(map(str, B @ hf_occ % 2))
    assert hf_bk == "1000000000", hf_bk  # matches Chemistry Studio's BK Hartree-Fock bitstring
    bits = np.array([int(c) for c in PAPER_REF])
    readings = {}
    for order in ("qubit 0 first", "qubit 0 last"):
        b = bits if order == "qubit 0 first" else bits[::-1]
        occ = Binv @ b % 2
        for spin in ("interleaved", "block"):
            readings[f"Bravyi-Kitaev, {order}, {spin} spin order"] = describe(list(occ), spin)
    readings["Jordan-Wigner occupation reading, qubit 0 first, interleaved"] = describe(list(bits), "interleaved")
    out = {"paper_reference_state": PAPER_REF, "active_space": "2 electrons in 5 spatial orbitals (10 spin orbitals)",
           "hartree_fock_occupation": "1100000000 (orbital 0 alpha and beta)",
           "hartree_fock_bk_bitstring_check": hf_bk, "readings": readings}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_state_decoding.json"), "w",
                        encoding="utf-8"), indent=1)
    for k, v in readings.items():
        print(f"{k:62s} occupation {v['occupation']}  N={v['electrons']}  alpha {v['alpha_orbitals']} beta {v['beta_orbitals']}  Sz={v['Sz']:+.1f}")


if __name__ == "__main__":
    main()
