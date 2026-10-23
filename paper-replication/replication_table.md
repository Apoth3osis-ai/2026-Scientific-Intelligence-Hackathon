# Independent reproduction: arXiv 2606.05968v1 (LiH, ADAPT-VQE, Bravyi-Kitaev)

This table was produced by the workflow "Replicate and Certify a Quantum Chemistry Result" on 2026-10-22. It used Chemistry Studio (`build_hamiltonian` and `calculate_energy`) at the paper's stated settings:

- LiH at R = 1.696 Angstrom
- frozen Li 1s core
- 2 active electrons in 5 active orbitals
- Bravyi-Kitaev mapping, 10 qubits

## Assumption: the basis set is inferred

**The paper does not state its basis set. We assume STO-3G.** The assumption rests on two kinds of evidence:

- **Orbital count.** Frozen-core LiH with 5 active spatial orbitals implies 6 basis functions, which is the STO-3G count for LiH.
- **Energy breakdown.** Every component of the paper's energy decomposition matches the restricted Hartree-Fock (RHF) decomposition at STO-3G to within the paper's six-decimal rounding ([`energy_decomposition_check.json`](energy_decomposition_check.json)):

| Quantity | Paper | Chemistry Studio, STO-3G | Difference (Ha) |
|---|---|---|---|
| Nuclear repulsion (Ha) | 0.936045 | 0.936044595 | -4.1e-7 |
| Frozen-core shift (Ha) | -7.758831 | -7.758830639 (frozen Li 1s core energy) | +3.6e-7 |
| Active-space energy (Ha) | -1.034598 | -1.034598663 (RHF energy within the active space) | -6.6e-7 |
| Reported total ground-state energy (Ha) | -7.857385 | -7.857384707 (RHF total) | +2.9e-7 |

This match strongly supports STO-3G, but it is an inference, not a statement from the paper. Every conclusion below holds under this assumption.

## Finding 1: the reported "FCI" energy is the Hartree-Fock energy

| Quantity (STO-3G) | Energy (Ha) | Below the reported total |
|---|---|---|
| Paper's reported total, described as the FCI limit | -7.857385 | |
| RHF | -7.857384707 | 0.0003 mHa (equal within rounding) |
| Exact ground state of the stated active space, CASCI(2e,5o) | **-7.879357455** | **21.97 mHa** |
| All-electron FCI | -7.879592768 | 22.21 mHa |

The CASCI(2e,5o) value also equals the lowest eigenvalue of the 276-term Bravyi-Kitaev qubit Hamiltonian ([`../hamiltonians/LiH_R1.696_sto3g_2e5o_bravyi_kitaev.json`](../hamiltonians/LiH_R1.696_sto3g_2e5o_bravyi_kitaev.json)) to 1e-12 Ha. The paper's active-space energy matches the RHF active-space energy, not the exact one. The exact active-space ground state lies 21.97 mHa lower, about 14 times chemical accuracy (1.6 mHa).

## Finding 2: the stated reference state is not the Hartree-Fock state, under standard encodings

The paper's run log (Appendix A.1, base64-encoded in the HTML) gives the reference state as `|1111000000>`.

**Counting 1s does not count electrons under Bravyi-Kitaev.** Each BK qubit stores a parity of several occupation numbers. We therefore decoded the bitstring explicitly by inverting the BK transform ([`decode_reference.py`](decode_reference.py), output in [`reference_state_decoding.json`](reference_state_decoding.json)). We used the Fenwick-tree BK convention (as in OpenFermion), with qubit 0 first and interleaved spin orbitals. Under this convention the 2-electron Hartree-Fock occupation `1100000000` encodes to `1000000000`, which is exactly the Hartree-Fock bitstring Chemistry Studio returns for this system.

| Reading of `1111000000` | Decoded occupation | Electrons | Sz |
|---|---|---|---|
| BK, qubit 0 first (the convention that reproduces Chemistry Studio's HF bitstring) | `1011000100` | 4 | 0 |
| BK, qubit 0 last | `0000001010` | 2 | +1 or -1 (depending on spin order) |
| Read as a Jordan-Wigner occupation string | `1111000000` | 4 | 0 |
| **Hartree-Fock state of the stated active space** | **`1100000000`** | **2** | **0** |

Under none of these standard readings is `|1111000000>` the Hartree-Fock state of a 2-electron active space. Under the convention that reproduces the tool's Hartree-Fock bitstring, it decodes to a 4-electron determinant, which is the wrong particle number for the stated active space. Read as a Jordan-Wigner occupation, it is the closed-shell 4-electron occupation of the two lowest spatial orbitals.

**What is not established.** The paper's code is not available to us, so the exact implementation error is not established. Two possibilities fit the evidence equally well:

- a 4-electron Jordan-Wigner occupation string applied to a frozen-core Bravyi-Kitaev register;
- a different bit-ordering or encoding convention from the ones above.

The decoding supports the criticism under standard conventions. It does not identify the bug.

## Files

- Inputs and reported values, each marked stated or inferred: [`extracted_inputs.json`](extracted_inputs.json)
- Energy decomposition check: [`energy_decomposition_check.json`](energy_decomposition_check.json)
- Reference-state decoding: [`decode_reference.py`](decode_reference.py) and [`reference_state_decoding.json`](reference_state_decoding.json)
- Full Bravyi-Kitaev Hamiltonian (276 Pauli terms): [`../hamiltonians/LiH_R1.696_sto3g_2e5o_bravyi_kitaev.json`](../hamiltonians/LiH_R1.696_sto3g_2e5o_bravyi_kitaev.json)
