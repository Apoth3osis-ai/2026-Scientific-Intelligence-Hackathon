# Run report: LiH bond curve with certified exact-gate circuits

Produced by the AgentPMT workflow *Replicate and Certify a Quantum Chemistry Result* (v1.1.0) on 2026-10-22.
All numbers below are also in `run_data.json`.

## Replication

arXiv [2606.05968v1](https://arxiv.org/abs/2606.05968v1) reports a total LiH ground-state energy of -7.857385 Ha at R = 1.696 A (frozen core, (2e,5o), Bravyi-Kitaev, 10 qubits) and calls it the FCI limit.

**Assumption: the basis set.** The paper does not state it. We assume STO-3G, which is strongly supported: all four components of the paper's energy breakdown (total, frozen-core shift, active-space energy, nuclear repulsion) match the STO-3G restricted Hartree-Fock decomposition to within 7e-7 Ha. It is still an inference.

Under that assumption, Chemistry Studio gives RHF = -7.857384707 Ha, CASCI(2e,5o) = -7.879357455 Ha and all-electron FCI = -7.879592768 Ha. **The reported total is the Hartree-Fock energy; the exact ground state of the stated active space is 21.97 mHa lower.**

**Reference state.** Under Bravyi-Kitaev, counting 1s does not count electrons, so the stated reference `|1111000000>` was decoded explicitly. Under the Fenwick-tree convention that reproduces the tool's Hartree-Fock bitstring `1000000000`, it is the 4-electron occupation `1011000100`. Under the other standard readings it is two same-spin electrons, or four electrons read as Jordan-Wigner. None is the Hartree-Fock state, but the exact implementation error is not established. Details: `../paper-replication/`.

## Bond curve (2-qubit model)

| R (A) | E_HF (Ha) | E_exact (Ha) | Certified circuit | Gates | T | E_sim (Ha) | SE (mHa) | z | Error vs exact (mHa) | HF error (mHa) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1.0 | -7.767362 | -7.767497 | `hf_a_k2` | 19 | 0 | -7.767394 | 0.037 | -0.88 | +0.102 | 0.135 |
| 1.25 | -7.844905 | -7.845064 | `hf_a_k2` | 19 | 0 | -7.844941 | 0.041 | -0.88 | +0.123 | 0.159 |
| 1.5 | -7.863358 | -7.863580 | `hf_a_k2` | 19 | 0 | -7.863399 | 0.047 | -0.88 | +0.181 | 0.222 |
| 1.75 | -7.853840 | -7.854194 | `hf_a_k2` | 19 | 0 | -7.853890 | 0.058 | -0.88 | +0.304 | 0.354 |
| 2.0 | -7.830906 | -7.831534 | `hf_a_k2` | 19 | 0 | -7.830969 | 0.073 | -0.88 | +0.564 | 0.628 |
| 2.25 | -7.801939 | -7.803167 | `hf_a_k2` | 19 | 0 | -7.802022 | 0.094 | -0.88 | +1.146 | 1.228 |
| 2.5 | -7.770874 | -7.773544 | `r2p50_ct` | 47 | 17 | -7.773021 | 0.184 | +0.90 | +0.523 | 2.670 |
| 3.0 | -7.710830 | -7.726428 | `r3p00_ct` | 47 | 17 | -7.725899 | 0.432 | +1.07 | +0.529 | 15.598 |

Every simulated energy agrees with its circuit's exact energy within shot noise (largest |z| = 1.07) and lies within chemical accuracy (1.6 mHa) of the exact model energy (largest error 1.146 mHa). Hartree-Fock misses by 2.67 mHa at 2.5 A and 15.60 mHa at 3.0 A.

From 1.0 to 2.25 A the precision budget gives K* = 2: the Hartree-Fock state is already within chemical accuracy, so the certified circuit is the 19-gate Clifford preparation of that state, and those six points share one set of counts (hence the same z). From 2.5 A on, static correlation grows, and the certified Clifford+T circuits recover it.

Equilibrium: R = 1.5 A on the exact curve and R = 1.5 A on the simulated curve (grid of 8 points). Energy rise from equilibrium to 3.0 A: 86.06 kcal/mol exact, 86.28 kcal/mol simulated. The 3.0 A point is not yet full dissociation.

## Precision study circuits (simulated and exported)

| Circuit | R (A) | Grid | E_sim (Ha) | SE (mHa) | z | Error vs exact (mHa) |
|---|---|---|---|---|---|---|
| `r1p50_k8` | 1.5 | K = 8 | -7.863549 | 0.079 | +0.12 | +0.031 |
| `r2p50_k5` | 2.5 | K = 5 | -7.773365 | 0.207 | -0.59 | +0.179 |
| `r3p00_k5` | 3.0 | K = 5 | -7.725875 | 0.442 | +1.23 | +0.553 |
| `r3p00_k8` | 3.0 | K = 8 | -7.725915 | 0.445 | +1.13 | +0.513 |

The full dyadic precision budget (K = 2..10 at every bond length) is in `precision_budget.json`; the Clifford+T T-count fronts are in `../circuits/*_ct/*_report.json`.

## Certificates

| Circuit | Kind | Certificate | Kernel-replayed theorems | Axioms |
|---|---|---|---|---|
| `hf_a_k2` | dyadic K=2 (Clifford) | `qpcert_a272d51fc2ea1e18` | claim_hf_a_k2_prep_well_formed, claim_hf_a_k2_prep_action, anti_vacuity_t_ne_tdg, anti_vacuity_measurement_changes_instrument | none |
| `r2p50_ct` | Clifford+T | `qpcert_f47b8566cf85f0c6` | claim_r2p50_ct_prep_well_formed, claim_r2p50_ct_prep_action, anti_vacuity_t_ne_tdg, anti_vacuity_measurement_changes_instrument | none |
| `r3p00_ct` | Clifford+T | `qpcert_f3f0c674daa1a372` | claim_r3p00_ct_prep_well_formed, claim_r3p00_ct_prep_action, anti_vacuity_t_ne_tdg, anti_vacuity_measurement_changes_instrument | none |

Exported programs: 14 (OpenQASM 3 and Qiskit for 7 circuits), all with `exact_readback_checked: true`. Index: `../exports/export_index.json`.

## What is proven and what is not

- **Proven (Lean kernel, no axioms):** each certified circuit is well formed in `exact_clifford_t_v2`, and its exact unitary is the one the certificate states. Every point on the curve uses a certified circuit.
- **Computed exactly (not a proof):** the energy of each circuit's state, from the Chemistry Studio Hamiltonian.
- **Observed (simulation):** the Qiskit Aer and Stim energies from 65,536 shots per basis, which agree with the exact circuit energies within shot noise.
- **Not claimed:** anything about the chemistry beyond the stated model (STO-3G, (2e,2o)), and anything about hardware execution.
