# Independent reproduction: arXiv 2606.05968v1 (LiH, ADAPT-VQE, Bravyi-Kitaev)

This table was produced by the workflow "Replicate and Certify a Quantum Chemistry Result" on 2026-10-22. It used Chemistry Studio (`build_hamiltonian` and `calculate_energy`) at the paper's stated settings:

- LiH, with R = 1.696 Angstrom
- frozen Li 1s core
- 2 active electrons in 5 active orbitals
- Bravyi-Kitaev mapping, giving 10 qubits
- basis STO-3G (inferred from the orbital and qubit counts, then confirmed by the matching RHF energy)

| Quantity | Paper | Chemistry Studio | Difference |
|---|---|---|---|
| Nuclear repulsion (Ha) | 0.936045 | 0.936044595 | < 1e-6 (match) |
| Qubits | 10 | 10 | match |
| Hamiltonian terms (BK) | n/a | 276 | n/a |
| RHF energy (Ha) | n/a | -7.857384707 | n/a |
| Reported total ground-state energy (Ha) | -7.857385 | equals the RHF energy above | 3e-7 |
| Exact active-space ground state, CASCI(2e,5o) (Ha) | n/a | **-7.879357455** | 21.97 mHa below the reported total |
| All-electron FCI (Ha) | n/a | -7.879592768 | 22.21 mHa below the reported total |
| Hartree-Fock reference bitstring (qubit 0 first) | `1111000000` | BK `1000000000` (JW `1100000000`) | different |

**How the workflow reads this:**

- The reported total matches the Hartree-Fock energy to 3e-7 Ha.
- The exact ground state of the stated active space lies 21.97 mHa lower, which is about 14 times chemical accuracy (1.6 mHa).
- The tool's HF bitstring for 2 active electrons has one set qubit under Bravyi-Kitaev, and two under Jordan-Wigner.

The calculations are fully reproducible from the inputs in `extracted_inputs.json`. The full Bravyi-Kitaev Hamiltonian (276 Pauli terms) is in `../hamiltonians/LiH_R1.696_sto3g_2e5o_bravyi_kitaev.json`.
