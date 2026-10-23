# Research notes

This is the lab notebook for the AgentPMT workflow [*Replicate and Certify a Quantum Chemistry Result: Exact-Gate Bond Curves with Lean Proofs*](https://www.agentpmt.com/agent-workflow-skills/replicate-and-certify-a-quantum-chemistry-result-exact-gate-bond-curves-with-lean-proofs). It records how we built the workflow on 2026-10-22: what we tried, what each tool turned out to do, and every design decision.

The full test run is written up in [`HOW_IT_WORKS.md`](HOW_IT_WORKS.md), and the one-page summary is [`PAPER.md`](PAPER.md).

## Goal

Build a public AgentPMT workflow that lets any AI agent:

1. find new quantum-chemistry papers;
2. reproduce the paper's chemistry and check its numbers;
3. model a chemical bond with exact-gate quantum circuits, simulated in Qiskit;
4. ship every circuit with a Lean-kernel proof and runnable OpenQASM 3 and Qiskit programs.

The workflow is public and attached to the public **Quantum Circuit Building Agent** on AgentPMT.

## Scientific framing

**Flagship system: the LiH bond curve.** LiH has a real chemical bond and is a standard benchmark for quantum chemistry on qubits. Freezing the Li 1s core and keeping 2 electrons in 2 orbitals gives a 2-qubit model of the sigma bond. That model is small enough that every circuit energy can be checked exactly against classical diagonalization.

We considered Li+ and Li alone and set them aside. Neither has a bond, and in a reduced model both come down to a 2x2 matrix problem.

The workflow brings three things to a chemistry result:

1. **Independent replication.** It recomputes a paper's energies from first principles at the paper's own settings. This catches errors in energies, reference states and conventions.
2. **Proof-carrying, runnable artifacts.** Every circuit has a Lean-kernel certificate that anyone can replay, plus Qiskit and OpenQASM 3 programs.
3. **A precision budget in an exact gate set.** The quantum tool uses exact gates only: Clifford+T and exact phases at 2^k-th roots of unity. The workflow therefore measures how finely each rotation angle must be set to reach chemical accuracy (1.6 mHa) along the bond.

## Design decisions

| Decision | Choice | Reason |
|---|---|---|
| Form | An AgentPMT workflow, attached to the Quantum Circuit Building Agent | A fixed, repeatable order of steps, with the agent as the chat front end |
| Visibility | Everything public: the workflow, both context documents and every tool it uses | Any agent can run it and anyone can check it |
| Paper search | Valency | Semantic search across arXiv, chemRxiv, PubMed and more |
| Full text | Live Web Page Browser on `arxiv.org/html/<id>` | Valency returns metadata and abstracts; the HTML gives the full text, appendices included |
| Hamiltonians | Chemistry Studio, from the paper's settings | Papers publish settings and energies, not qubit-Hamiltonian coefficients (see below) |
| Output | A bond curve of 8 points | Gives the equilibrium bond length and shows where electron correlation grows |
| Circuits | Exact state preparation of the classically computed ground state | A workflow is an acyclic graph, so the exact state is computed once instead of running a variational loop |
| Certification | An exact-unitary claim for every point on the curve | The exact claim is the scientifically meaningful one |
| Fine angles | Exact Clifford+T synthesis | Keeps every point in the profile where the exact unitary is kernel-certified |
| Qiskit | Simulation on the tool's Qiskit Aer backend, plus exported Qiskit and OpenQASM 3 programs | Anyone can rerun every circuit |
| Scheduling | Quantum-tool jobs run one at a time with `resource_class: standard` | About 10 s per job once warm |
| Storage | File Management, with file expiry extended | Certificates and programs outlive the 7-day default |

## Tools

All tools are used through AgentPMT over MCP.

| Tool | ID | Role |
|---|---|---|
| Valency Research Paper Library | `6ada7145e001971070f33005` | Paper search |
| Live Web Page Browser | `69644454288e0324fa542102` | Full text of the chosen paper |
| Chemistry Studio | `6ada6971e001971070f32f9a` | Qubit Hamiltonians, HF/CASCI/FCI energies, bond scans |
| Complex Mathematics Engine | `689df4ac8ee2d1dd79e9035b` | Exact ground states, precision budgets, Clifford+T synthesis |
| Quantum Circuit Builder with Proof | `6a7e5036b8c970a6773201b5` | Simulation, export, Lean-kernel certificates |
| File Management | `6948b078b54506f955d789ed` | Stores the report, data and certificates |
| Workflow Creator | AgentPMT MCP tool | Builds, validates and publishes the workflow |
| Agent Context Manager | `6a389fd44cde57baf7edba1b` | Holds the two public context documents |
| Agent Builder | `69ed32a83ccc082ef9976212` | Attaches the workflow, tools and documents to the agent |

## How the quantum tool works

Small test circuits fixed every convention the workflow relies on. All of them are written into the public rules document ([`context/`](context/)).

- **Gate set.** `id h x y z s sdg t tdg cx cz swap`, plus measurement, reset, barrier and exact phase gates. Angles are exact rational multiples of pi and are never rounded. The exported programs keep them as exact syntax, for example `ry((2 * 1 * pi / 8))`.
- **Simulator.** `execute_locally` runs Qiskit Aer 0.17.2 (qiskit 2.5.0, Python 3.12.3), statevector in double precision, with precommitted seeds.
  - Clifford circuits are routed to Stim 1.16.0.
  - The runtime also bundles Cirq/qsim and Braket local simulators.
  - Fixed seeds make reruns bit-identical: a repeated test circuit returned exactly the same counts.
- **Angle convention (test circuit 1).** One qubit, `.rot .ry 8 1`, 8,192 shots.
  - Measured P(1) = 0.14917. Qiskit `ry(pi/4)` predicts sin^2(pi/8) = 0.14645 (z = +0.70).
  - So `.rot .ry h e` is Qiskit `ry(2*pi*e/h)`. The receipt agrees (`angle_scale: 2`).
- **Bit order (test circuit 2).** Two qubits: X on qubit 0, and on qubit 1 a Ry(pi/8) built from phase gates.
  - Counts: `10: 7888`, `11: 304`. Count keys put qubit 0 leftmost, the same order Chemistry Studio uses for its Hartree-Fock bitstrings.
  - P(q1 = 1) = 0.03711 against sin^2(pi/16) = 0.03806 (z = -0.45), so the phase-gate rotation simulates correctly.
  - `.rot .phase h e` is Qiskit `p(pi*e/h)`.
- **Exact rotations from phase gates.** Ry(theta) = S H P(theta) H Sdg, applied in time order `sdg, h, P, h, s`.
  - In the certificate IR, `rzk` at level k is P(2*pi/2^k).
  - Any dyadic angle 2*pi*m/2^K is a product of phase gates that follows the binary digits of m.
  - The tool's exact-unitary view of the test rotation decodes to Ry(pi/8) exactly, up to global phase.
- **One gate list everywhere.** Each circuit is written twice, op for op: as a Lean `CircuitSpec` for simulation and export, and as a canonical IR document for validation and certification. So the simulated, exported and certified circuits are the same circuit.
- **Certification.** `certify_circuit` issues a qpcert whose claims the Lean kernel replays with no axioms.
  - Under `exact_clifford_t_v2`, both `well_formed` and `exact_unitary_action` are kernel-certified.
  - Certification accepts phase levels 2 to 4, which is angles down to 2*pi/16.
  - Where a bond length needs finer angles, the workflow synthesizes an exact Clifford+T circuit instead (below), so every point keeps the strongest certificate.
- **Exports.** OpenQASM 3 and Qiskit; Cirq and Braket are also available. Every program is read back and checked against the circuit (`exact_readback_checked: true`), along with ISA, timing and topology checks.
- **Results.** A completed task returns a `result_file`, which is a File Management JSON. The workflow downloads it and reads `result.result`.

## Finding a paper

- **Valency** searches semantically across arXiv, chemRxiv, PubMed and other sources, in about half a second per query. Our LiH searches from 2026-01 onward returned 48 unique papers ([`paper-replication/valency_search_results.json`](paper-replication/valency_search_results.json)).
- **Candidates.** Our searches turned up these recent LiH papers, among others:
  - 2606.05968v1: ADAPT-VQE on LiH, HF and H2O under Bravyi-Kitaev;
  - 2608.02119v2: basis-set optimization, with LiH potential energy curves;
  - 2606.13387: ADAPT-VQE measurement overhead;
  - 2606.05865v1: symmetry-adapted qubit encoding with a complete active space and Bravyi-Kitaev;
  - 2606.26912v2: a Givens-exchange ansatz for molecular variational eigensolvers.
- **Papers publish settings, not Hamiltonians.** We read two recent LiH papers in full, 2606.05968v1 and 2608.02119v2. Both give the geometry, basis, active space, mapping and energies, but no qubit-Hamiltonian coefficients. The workflow therefore builds each Hamiltonian in Chemistry Studio from the paper's settings and checks the reported numbers against it.
- **Choice: arXiv 2606.05968v1.** It has full HTML text and reports the molecule, bond length, active space, mapping, qubit count and an energy breakdown. Its appendix run log, encoded in base64, gives the reference state.

## Chemistry Studio

- **Actions:** `lookup_molecule`, `calculate_energy` (hf, dft, mp2, ccsd, ccsd_t, casci, casscf, fci), `build_hamiltonian`, `export_integrals` (FCIDUMP), `scan_bond`, `optimize_geometry`, `calculate_excited_states` and `get_task`.
- **`build_hamiltonian`** supports the Jordan-Wigner, Bravyi-Kitaev, parity and tapered-parity mappings with any active space. It returns:
  - the Hartree-Fock bitstring, qubit 0 first, which matches the quantum tool's count keys;
  - the exact active-space energy;
  - a constant that includes nuclear repulsion and the frozen core.
- **Correlation grows as the bond stretches.** LiH at 1.595 A in STO-3G:

  | Model | Qubits | Pauli terms | HF (Ha) | Exact (Ha) | Correlation |
  |---|---|---|---|---|---|
  | (2e,2o), parity_tapered | 2 | 9 | -7.862023860 | -7.862285534 | 0.26 mHa |
  | (2e,3o), parity_tapered | 4 | 52 | -7.862023860 | -7.863077754 | 1.05 mHa |

  Near equilibrium, Hartree-Fock is already within chemical accuracy. At 3.0 A the 2-qubit model's correlation is 15.60 mHa. The precision of the circuit matters most along the stretched bond, which is why the bond curve is the core experiment.

## Replicating arXiv 2606.05968v1

The paper is in the repo ([`paper-replication/2606.05968v1.pdf`](paper-replication/2606.05968v1.pdf)). The full table is [`paper-replication/replication_table.md`](paper-replication/replication_table.md).

- **Stated settings:** LiH at R = 1.696 A, Li 1s frozen, 2 active electrons in 5 active orbitals, Bravyi-Kitaev, 10 qubits.
- **Stated results:** a total ground-state energy of -7.857385 Ha, described as the FCI limit, and the reference state `|1111000000>` (from the Appendix A.1 run log).
- **Basis assumption.** The paper does not state its basis set. We assume STO-3G:
  - Frozen-core LiH with 5 active orbitals implies 6 basis functions, the STO-3G count for LiH.
  - Every component of the paper's energy breakdown matches the STO-3G restricted Hartree-Fock decomposition within its six-decimal rounding: nuclear repulsion 0.936045 Ha, frozen-core shift -7.758831 Ha, active-space energy -1.034598 Ha and total -7.857385 Ha.

  Every conclusion below holds under this assumption.

**Finding 1: the reported "FCI" energy is the Hartree-Fock energy.**

| Quantity (STO-3G, Chemistry Studio) | Energy (Ha) |
|---|---|
| RHF | -7.857384707 |
| CASCI(2e,5o), the exact ground state of the stated active space | **-7.879357455** |
| All-electron FCI | -7.879592768 |

The exact active-space ground state lies **21.97 mHa** below the paper's reported total, about 14 times chemical accuracy. The CASCI energy also equals the lowest eigenvalue of the 276-term Bravyi-Kitaev qubit Hamiltonian to 1e-12 Ha.

**Finding 2: the stated reference state is not the Hartree-Fock state, under standard encodings.** Under Bravyi-Kitaev each qubit stores a parity, so counting 1s does not count electrons. We decoded the bitstring explicitly ([`paper-replication/decode_reference.py`](paper-replication/decode_reference.py)):

- **Bravyi-Kitaev, qubit 0 first.** This Fenwick-tree convention reproduces Chemistry Studio's Hartree-Fock bitstring `1000000000`. Under it, `1111000000` decodes to the 4-electron occupation `1011000100`.
- **Bravyi-Kitaev, qubit 0 last.** It decodes to two same-spin electrons.
- **Jordan-Wigner occupation.** It is a 4-electron state.

None of these is the Hartree-Fock state `1100000000`. The paper's code is not available, so the exact implementation error is not established.

## The bond-curve model and the precision budget

- **Model.** STO-3G, Li 1s frozen, 2 electrons in 2 orbitals, `parity_tapered`: **2 qubits and 9 Pauli terms**.
  - Chemistry Studio's `scan_bond` gave FCI, CASCI and HF curves from 1.0 to 4.0 A, with the FCI minimum at 1.5 A.
  - The curve uses 8 points: 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5 and 3.0 A.
- **Exact state preparation.** Ry(t0) on qubit 0, Ry(alpha) on qubit 1, CX, Ry(beta) on qubit 1, CX. The angles come directly from the ground-state amplitudes, so the fidelity is exactly 1 before rounding.
- **Measurement.** Four bases (ZZ, XX, ZX and XZ) cover all 9 terms, at 65,536 shots each.
- **Precision budget.** Each angle is rounded to the grid 2*pi*m/2^K and the energy error of the rounded circuit is computed exactly. The whole budget runs as one numpy expression in the Complex Mathematics Engine (6.5 ms) and matches local numpy to 1e-12 ([`results/precision_budget.json`](results/precision_budget.json)).

  | K | dE at 2.5 A (mHa) | dE at 3.0 A (mHa) |
  |---|---|---|
  | 2 | 2.670 | 48.786 |
  | 3 | 2.670 | 2.145 |
  | 4 | 3.301 | 2.160 |
  | **5** | **0.302** | **0.008** |
  | 6 | 0.007 | 0.079 |
  | 7 | 0.005 | 0.041 |
  | 8 | 0.004 | 0.009 |
  | 9 | 0.0004 | 0.0002 |
  | 10 | 0.001 | 0.0004 |

- **The K\* rule.** The error does not fall monotonically with K, because each angle is rounded independently. So the budget is reported as K\*: the smallest K for which that grid and every finer one stay within chemical accuracy.
  - K\* = 2 from 1.0 to 2.25 A, where the Hartree-Fock state is already within chemical accuracy.
  - K\* = 5 at 2.5 and 3.0 A.

## Certified Clifford+T synthesis

K\* = 5 needs phases of 2*pi/32, finer than the certifiable levels. Clifford+T is universal, so the workflow writes each rotation as an exact Clifford+T word instead. This puts the circuit under `exact_clifford_t_v2`, where the exact unitary is kernel-certified. The search works as follows:

- **Enumerate.** Every single-qubit word in Matsumoto-Amano normal form (T | e)(HT | SHT)^n C, with n <= 8 and C one of the 24 Cliffords: 24,528 exact unitaries.
- **Shortlist.** For each of the three rotation slots, keep the 5 closest words at every T count.
- **Score.** Rate every combination by its exact energy.
- **Break ties deterministically.** Many combinations prepare the same state: 52 at 2.5 A and 64 at 3.0 A lie within 1e-9 Ha of the best. Among those, take the lowest T count, then the fewest gates, then the first in enumeration order. The same input then gives the same circuit on any machine.
- **Simplify.** Merge adjacent phase gates and cancel HH.

The whole search runs as **one Complex Mathematics Engine expression in 0.117 s**. It returns the same gate list as the reference script [`circuits/generate_cliffordt.py`](circuits/generate_cliffordt.py), and [`workflow/cliffordt_expression.py`](workflow/cliffordt_expression.py) builds the expression and checks it.

The T-count fronts show how accuracy grows with T gates (`circuits/*_ct/*_report.json`):

| T count | Error at 2.5 A (mHa) | Error at 3.0 A (mHa) |
|---|---|---|
| 0 (Hartree-Fock) | 2.670 | 15.598 |
| 7 | 0.716 | |
| 8 | 0.716 | 0.782 |
| 13 | | 0.242 |
| 17 | **0.357** | **0.066** |

The certified circuits are 47 gates with 17 T gates at both bond lengths. At 3.0 A, chemical accuracy is already reached with 8 T gates.

**Writing Complex Mathematics Engine expressions.** These rules are in the rules document, so any agent can write engine expressions on the first try:

- Write ternaries without a parenthesis after a keyword, because `if (`, `else (` and `in (` read as calls.
- Call custom lambdas as `(name)(args)`, including recursion `(f)(f, ...)`. After `else`, write `[] + (f)(...)`.
- Use `//` and `%` for bit arithmetic.
- Use `np.arange` in place of `range`.

## Building the workflow

1. **First version (16 steps).** Valency search, shortlist, full text, claim extraction, Chemistry Studio reproduction, a consistency check and circuit-model choice, and the reference bond curve. Then a loop over each bond length (Hamiltonian, precision budget, circuits, energy from counts), followed by assembly, File Management and the final report.
2. **Rules document.** *Proof-Carrying Quantum Chemistry Rules* (`6ada6b06e001971070f32fc7`, public) holds every convention above:
   - Valency usage and Chemistry Studio conventions;
   - the state-preparation method and the K\* rule;
   - the Math Engine expression rules and the precision-budget template;
   - job scheduling and retries.

   A new agent learns the method by reading it.
3. **Synthesis step (17 steps).** A new loop step, `point-cliffordt`, runs between the precision budget and the circuit step. The circuit step chooses the certified route for each point and reuses identical circuits: the Hartree-Fock circuit serves six bond lengths with one set of counts, programs and certificate. The synthesis template has its own public document, *Certified Clifford+T Synthesis for Exact-Gate Chemistry Circuits* (`6ada99f0e001971070f333a0`).
4. **Test run.** The full run used workflow version 1.1.0. The public release, 1.1.1, has the same steps.

## Full test run

The complete record is in [`HOW_IT_WORKS.md`](HOW_IT_WORKS.md), and the numbers are in [`results/REPORT.md`](results/REPORT.md).

- **28 simulation runs** at 65,536 shots on Qiskit Aer and Stim, each about 10 s once warm ([`simulations/simulation_runs.json`](simulations/simulation_runs.json)).
- **Every point on the curve is within chemical accuracy** of the exact model energy, with a largest error of 1.15 mHa.
- **Every certified circuit's simulated energy agrees with its exact energy within shot noise** (|z| <= 1.07).
- **Equilibrium** is at 1.5 A on both the exact and the simulated curve.
- **At 3.0 A**, Hartree-Fock misses by 15.6 mHa, while the 47-gate certified Clifford+T circuit lands 0.53 mHa from exact in simulation.
- **3 certificates cover all 8 bond lengths:** `qpcert_a272d51fc2ea1e18` (Hartree-Fock circuit, 1.0 to 2.25 A), `qpcert_f47b8566cf85f0c6` (2.5 A) and `qpcert_f3f0c674daa1a372` (3.0 A). Each kernel-certifies `well_formed` and `exact_unitary_action` with no axioms, and each was checked against its SHA-256 on download ([`certificates/`](certificates/)).
- **14 exported programs**, OpenQASM 3 and Qiskit for 7 circuits, all exact-readback checked ([`exports/`](exports/)).
- **Reproducibility.** During development the 3.0 A state was also synthesized as a 49-gate Clifford+T word. Simulated with the same seeds, it gave counts bit-identical in all four bases to the final 47-gate circuit: two certified gate sequences, one state, the same samples.
- **Storage.** File Management stored the report and data and extended every certificate's expiry. The run closed with outcome `completed`, 8 of 8 tracked steps.

## Release

- **Repository:** https://github.com/Apoth3osis-ai/2026-Scientific-Intelligence-Hackathon
- **Workflow (public):** https://www.agentpmt.com/agent-workflow-skills/replicate-and-certify-a-quantum-chemistry-result-exact-gate-bond-curves-with-lean-proofs
- **Quantum Circuit Building Agent (public):** carries the workflow, its six tools and both context documents. Anyone can chat with it on AgentPMT.
- **Run it yourself:** the [README](README.md) explains the free AgentPMT sign-up and how to connect an agent over MCP.

## Next directions

- **Larger active spaces.** The circuit path supports up to 4 qubits. LiH (2e,3o) with tapered parity is 4 qubits and 52 terms.
- **The paper's other molecules:** HF and H2O.
- **The "symmetry trap."** The paper reports that fixed-ansatz UCCSD under Bravyi-Kitaev stalls at zero gradient. To test whether this comes from its reference state, we will run UCCSD from `|1111000000>` and from the true Hartree-Fock state.
- **Certified measurement distributions.** The certificate ledger also supports `exact_zero_state_observation`, which fixes a circuit's complete outcome distribution in the certificate. With one per measurement basis, the energy becomes an exact function of certified data.
- **Materials.** Battery and catalyst molecules in small active spaces.
