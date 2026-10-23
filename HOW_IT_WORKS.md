# How it works: the full test run, step by step

This is the complete record of one end-to-end run of the AgentPMT workflow **Replicate and Certify a Quantum Chemistry Result: Exact-Gate Bond Curves with Lean Proofs** (workflow `6ada7c48e001971070f3313a`, v1.1.0), run on 2026-10-22. Every number here comes from a file in this repo; the short version is in [`results/REPORT.md`](results/REPORT.md).

## The toolchain

The workflow is a 17-step AgentPMT skill chain (graph in [`workflow/workflow.json`](workflow/workflow.json), readable form in [`workflow/WORKFLOW.md`](workflow/WORKFLOW.md)). It uses five tools and two public context documents:

| Tool | Product ID | Role |
|---|---|---|
| Valency Research Paper Library | `6ada7145e001971070f33005` | Semantic search over arXiv, chemRxiv, PubMed and more |
| Live Web Page Browser | `69644454288e0324fa542102` | Full text of the chosen paper (`arxiv.org/html/<id>`) |
| Chemistry Studio | `6ada6971e001971070f32f9a` | Qubit Hamiltonians, HF/CASCI/FCI energies, bond scans |
| Complex Mathematics Engine | `689df4ac8ee2d1dd79e9035b` | Exact ground states, precision budgets, Clifford+T synthesis |
| Quantum Circuit Builder with Proof | `6a7e5036b8c970a6773201b5` | Simulation, OpenQASM 3 / Qiskit export, Lean-kernel certificates |
| File Management | `6948b078b54506f955d789ed` | Stores the report, data and certificates |

Context documents (copies in [`context/`](context/)):

- *Proof-Carrying Quantum Chemistry Rules* (`6ada6b06e001971070f32fc7`): every convention the agent needs, verified by direct tool runs.
- *Certified Clifford+T Synthesis for Exact-Gate Chemistry Circuits* (`6ada99f0e001971070f333a0`): the one-expression synthesis template.

## 1. Find and read a paper

**Valency** searched semantically for recent LiH qubit-Hamiltonian work (for example "lithium hydride LiH molecular qubit Hamiltonian variational quantum eigensolver bond dissociation potential energy curve small active space", from 2026-01 onward). Each search took about half a second, and together they returned 48 unique papers from arXiv, chemRxiv and PubMed ([`paper-replication/valency_search_results.json`](paper-replication/valency_search_results.json)). The workflow shortlisted papers that report a molecule, a basis, an active space, a mapping and numerical energies, and chose **arXiv [2606.05968v1](https://arxiv.org/abs/2606.05968v1)**, an ADAPT-VQE study of LiH, HF and H2O under the Bravyi-Kitaev mapping.

The **browser** read the full HTML text (the PDF is in the repo: [`paper-replication/2606.05968v1.pdf`](paper-replication/2606.05968v1.pdf)). The extraction step recorded every input with its status ([`paper-replication/extracted_inputs.json`](paper-replication/extracted_inputs.json)):

- stated: LiH at R = 1.696 A, Li 1s frozen, 2 active electrons in 5 active orbitals, Bravyi-Kitaev, 10 qubits, a 24-operator ADAPT pool
- stated in the base64-encoded run log of Appendix A.1, which the agent decoded: reference state `|1111000000>`
- stated: total ground-state energy -7.857385 Ha, called the FCI limit
- **not stated: the basis set.** We assume STO-3G. Frozen-core LiH with 5 active orbitals implies 6 basis functions, the STO-3G count for LiH. Every conclusion below holds under this assumption.

## 2. Reproduce the chemistry independently

**Chemistry Studio** rebuilt the paper's model at the same settings, with the assumed STO-3G basis. It reproduced every component of the paper's energy breakdown within the paper's six-decimal rounding:

| Quantity | Paper | Chemistry Studio, STO-3G | Difference (Ha) |
|---|---|---|---|
| Nuclear repulsion (Ha) | 0.936045 | 0.936044595 | -4.1e-7 |
| Frozen-core shift (Ha) | -7.758831 | -7.758830639 (frozen Li 1s core) | +3.6e-7 |
| Active-space energy (Ha) | -1.034598 | -1.034598663 (RHF, within the active space) | -6.6e-7 |
| Reported total ground state (Ha) | -7.857385 | -7.857384707 (RHF total) | +2.9e-7 |
| Exact active-space ground state, CASCI(2e,5o) (Ha) | | **-7.879357455** | |
| All-electron FCI (Ha) | | -7.879592768 | |

**Basis assumption.** The match of all four components strongly supports STO-3G. It remains an inference, because the paper omits the basis ([`paper-replication/energy_decomposition_check.json`](paper-replication/energy_decomposition_check.json)).

**Finding 1.** Under that assumption, the paper's reported total and its active-space energy are the restricted Hartree-Fock values. The exact ground state of the stated active space is **21.97 mHa lower** (about 14 times chemical accuracy), and all-electron FCI is 22.21 mHa lower. The CASCI energy also agrees with exact diagonalization of the 276-term qubit Hamiltonian to 1e-12 Ha.

**Finding 2.** The stated reference `|1111000000>` is not the Hartree-Fock state under standard encodings. Under Bravyi-Kitaev a qubit stores a parity, so counting 1s does not count electrons. The workflow therefore decoded the bitstring explicitly ([`paper-replication/decode_reference.py`](paper-replication/decode_reference.py)):

- **BK, qubit 0 first.** This Fenwick-tree convention reproduces Chemistry Studio's Hartree-Fock bitstring `1000000000`. Under it, the reference decodes to the 4-electron occupation `1011000100`, the wrong particle number for a 2-electron active space.
- **BK, qubit 0 last.** It decodes to two same-spin electrons.
- **Jordan-Wigner occupation reading.** It is a 4-electron state.

None of these is the Hartree-Fock state `1100000000`. The decoding supports the criticism under standard conventions. The paper's code is not available, so the exact implementation error is not established.

Files: [`paper-replication/replication_table.md`](paper-replication/replication_table.md), [`hamiltonians/LiH_R1.696_sto3g_2e5o_bravyi_kitaev.json`](hamiltonians/LiH_R1.696_sto3g_2e5o_bravyi_kitaev.json).

## 3. Choose the circuit model and compute the reference curve

The circuit model is the minimal description of the Li-H sigma bond: STO-3G, Li 1s frozen, 2 electrons in 2 orbitals, `parity_tapered` mapping, **2 qubits and 9 Pauli terms** (I, Z0, Z1, Z0Z1, X0, X1, X0X1, Z0X1, X0Z1). Chemistry Studio's `scan_bond` gave FCI, CASCI(2e,2o) and HF curves from 1.0 to 4.0 A in 0.1 A steps ([`results/reference_curves_LiH_sto3g.json`](results/reference_curves_LiH_sto3g.json)); the FCI minimum is at 1.5 A. The bond curve uses 8 points: 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5 and 3.0 A ([`hamiltonians/LiH_sto3g_2e2o_parity_tapered_bond_curve.json`](hamiltonians/LiH_sto3g_2e2o_parity_tapered_bond_curve.json)).

## 4. For each bond length

### 4a. Exact state and precision budget (Math Engine)

One numpy expression per bond length builds the 4x4 Hamiltonian, diagonalizes it, and computes the exact two-CNOT state preparation

$$|\psi\rangle = \mathrm{CX}\,(I\otimes R_y(\beta))\,\mathrm{CX}\,(R_y(\theta_0)\otimes R_y(\alpha))\,|00\rangle,$$

with $\theta_0 = 2\,\mathrm{atan2}(\lVert(a_{10},a_{11})\rVert, \lVert(a_{00},a_{01})\rVert)$, $\alpha=(\varphi_0+\varphi_1)/2$, $\beta=(\varphi_0-\varphi_1)/2$, $\varphi_0 = 2\,\mathrm{atan2}(a_{01},a_{00})$ and $\varphi_1 = 2\,\mathrm{atan2}(a_{11},a_{10})$. It then rounds each angle to the grid $\theta = 2\pi m/2^K$ for $K = 2,\dots,10$ and reports the energy error of every rounded circuit. $K^*$ is the smallest $K$ for which that grid and every finer one stay within chemical accuracy (1.6 mHa). The result matches local numpy to 1e-12 ([`results/precision_budget.json`](results/precision_budget.json)).

| R (A) | 1.0 to 2.25 | 2.5 | 3.0 |
|---|---|---|---|
| $K^*$ | 2 (the Hartree-Fock state is already within chemical accuracy) | 5 | 5 |

### 4b. Certified Clifford+T synthesis (Math Engine, when $K^* \ge 5$)

Exact Clifford+T circuits carry the strongest certificate the quantum tool issues: a kernel-checked exact unitary. Clifford+T is universal, so the workflow synthesizes each rotation as an exact Clifford+T word. One Math Engine expression (0.12 s) does the whole search:

1. Enumerate every single-qubit word in Matsumoto-Amano normal form $(T\mid\varepsilon)(HT\mid SHT)^n C$ with $n \le 8$ and $C$ one of the 24 Cliffords: 24,528 exact unitaries.
2. For each of the three rotation slots, keep the 5 words closest to the ideal rotation at every T count (the first two slots act on $|0\rangle$ and are matched on the state; the third is matched as a full unitary).
3. Score all 125,000 combinations by exact energy.
4. Many combinations prepare the same state with different words. Among those within 1e-9 Ha of the best energy, take the lowest T count, then the fewest gates, then the first in enumeration order. The result is deterministic.
5. Merge adjacent phase gates and cancel $HH$.

The engine output is identical, gate for gate, to the reference script [`circuits/generate_cliffordt.py`](circuits/generate_cliffordt.py); [`workflow/cliffordt_expression.py`](workflow/cliffordt_expression.py) builds the expression and checks it. Results:

| R (A) | Gates | T count | Circuit energy error vs exact (mHa) |
|---|---|---|---|
| 2.5 | 47 | 17 | 0.357 |
| 3.0 | 47 | 17 | 0.066 |

The full T-count fronts are in `circuits/*_ct/*_report.json`. At 3.0 A, chemical accuracy is already reached with 8 T gates (0.78 mHa).

### 4c. Simulate, export and certify (Quantum Circuit Builder with Proof)

Each circuit is written twice from one gate list: as a Lean `CircuitSpec` (for simulation and export) and as a canonical IR document (for validation and certification), op for op.

**Simulation.** `execute_locally` ran each circuit in four measurement bases (ZZ, XX, ZX and XZ, by appending H gates) at 65,536 shots. The service routes each circuit automatically: Clifford circuits to **Stim 1.16.0** (`tableau_sampler`) and everything else to **Qiskit Aer 0.17.2** (qiskit 2.5.0), statevector, complex128, with precommitted seeds. Every receipt records the backend, versions, seeds and the execution-input digest ([`simulations/simulation_runs.json`](simulations/simulation_runs.json)). Warm runs take about 10 s.

**Energies.** Each Pauli term is read from the basis that diagonalizes it:

$$\langle P\rangle = \sum_{\text{keys}} (-1)^{\sum_{i\in \mathrm{supp}(P)} k_i}\,\frac{n_k}{N},\qquad E = c_I + \sum_P c_P \langle P\rangle,$$

with the standard error from the per-basis sample variance of the grouped observable ([`results/energies.py`](results/energies.py)).

**Export.** `export_provider_programs` produced OpenQASM 3 and Qiskit programs for 7 circuits (14 programs, [`exports/`](exports/)). Every program carries `exact_readback_checked: true` plus ISA, timing and topology checks, and dyadic angles stay exact symbolic multiples of $\pi$, for example `p((1 * 1 * pi / 16))`.

**Certification.** `inspect_circuit` validated each IR document (profile admissibility and the `circuit_subject_sha256` digest), and `certify_circuit` produced a qpcert proving two claims bound to that digest: `well_formed` and `exact_unitary_action` (the exact $\mathbb{D}[\omega]$ matrix of the circuit, unitary up to global phase). The Lean kernel replays each claim with **no axioms**, together with two anti-vacuity theorems. Each certificate was downloaded and checked against its reported SHA-256 ([`certificates/`](certificates/)).

| Circuit | Used for | Gates | Certificate | Certified claims |
|---|---|---|---|---|
| `hf_a_k2` | 1.0 to 2.25 A | 19 (Clifford) | `qpcert_a272d51fc2ea1e18` | well_formed, exact_unitary_action |
| `r2p50_ct` | 2.5 A | 47 (T = 17) | `qpcert_f47b8566cf85f0c6` | well_formed, exact_unitary_action |
| `r3p00_ct` | 3.0 A | 47 (T = 17) | `qpcert_f3f0c674daa1a372` | well_formed, exact_unitary_action |

The certified Hartree-Fock circuit is identical at 1.0 to 2.25 A, so the workflow runs it once and reuses its counts, programs and certificate.

**Precision study.** The dyadic circuits at $K = 5$ and $K = 8$ (`r2p50_k5`, `r3p00_k5`, `r1p50_k8`, `r3p00_k8`) were also simulated and exported, to show the precision budget at work.

## 5. Results

| R (A) | Certified circuit | E_sim (Ha) | SE (mHa) | z vs circuit's exact energy | Error vs exact (mHa) | HF error (mHa) |
|---|---|---|---|---|---|---|
| 1.0 | `hf_a_k2` | -7.767394 | 0.037 | -0.88 | +0.102 | 0.135 |
| 1.25 | `hf_a_k2` | -7.844941 | 0.041 | -0.88 | +0.123 | 0.159 |
| 1.5 | `hf_a_k2` | -7.863399 | 0.047 | -0.88 | +0.181 | 0.222 |
| 1.75 | `hf_a_k2` | -7.853890 | 0.058 | -0.88 | +0.304 | 0.354 |
| 2.0 | `hf_a_k2` | -7.830969 | 0.073 | -0.88 | +0.564 | 0.628 |
| 2.25 | `hf_a_k2` | -7.802022 | 0.094 | -0.88 | +1.146 | 1.228 |
| 2.5 | `r2p50_ct` | -7.773021 | 0.184 | +0.90 | +0.523 | 2.670 |
| 3.0 | `r3p00_ct` | -7.725899 | 0.432 | +1.07 | +0.529 | 15.598 |

- Every point on the curve is covered by a Lean-certified circuit.
- Every simulated energy agrees with its circuit's exact energy within shot noise.
- Every point is within chemical accuracy of the exact model energy. Where Hartree-Fock fails (2.67 mHa at 2.5 A and 15.6 mHa at 3.0 A), the certified Clifford+T circuits recover the static correlation.
- The equilibrium bond length is 1.5 A on both the exact and the simulated curve.

Precision-study circuits:

| Circuit | E_sim (Ha) | SE (mHa) | z | Error vs exact (mHa) |
|---|---|---|---|---|
| `r1p50_k8` (1.5 A) | -7.863549 | 0.079 | +0.12 | +0.031 |
| `r2p50_k5` (2.5 A) | -7.773365 | 0.207 | -0.59 | +0.179 |
| `r3p00_k5` (3.0 A) | -7.725875 | 0.442 | +1.23 | +0.553 |
| `r3p00_k8` (3.0 A) | -7.725915 | 0.445 | +1.13 | +0.513 |

**Reproducibility check.** During development the 3.0 A state was also synthesized as a longer, 49-gate Clifford+T word. Simulated with the same seeds, it gave **bit-identical counts in all four bases** to the final 47-gate circuit: two different certified gate sequences, one state, the same samples.

## 6. Save and report

The assemble step wrote [`results/REPORT.md`](results/REPORT.md) and [`results/run_data.json`](results/run_data.json); File Management stored both and extended the expiry of every certificate. The run was closed with outcome `completed`, 8 of 8 tracked steps.

## What the certificates prove

- **Proven by the Lean kernel, with no axioms:** each certified circuit is well formed in its semantic profile, and its exact unitary is the one the certificate states.
- **Computed exactly:** the energy of each circuit's state under the Chemistry Studio Hamiltonian.
- **Observed in simulation:** the sampled energies, which agree with the exact circuit energies within shot noise.

The chemistry itself (basis set, active space, model) is a modelling choice stated above; certificates cover the circuits.

## Reproduce it

Everything runs from this repo with Python and numpy (matplotlib for figures):

```
python circuits/generate_circuits.py <name> <K> <m_t0,m_alpha,m_beta> <outdir>   # dyadic circuits
python circuits/generate_cliffordt.py <name> <R> <outdir>                        # Clifford+T circuits
python workflow/cliffordt_expression.py check                                    # engine expression == script
python results/energies.py                                                       # energies from counts
python results/assemble_report.py                                                # REPORT.md and run_data.json
python figures/make_figures.py                                                   # figures
python workflow/export_markdown.py workflow/workflow.json workflow/WORKFLOW.md   # workflow as markdown
```

The certificates in [`certificates/`](certificates/) can be re-verified with the quantum tool's `verify_certificate` action.
