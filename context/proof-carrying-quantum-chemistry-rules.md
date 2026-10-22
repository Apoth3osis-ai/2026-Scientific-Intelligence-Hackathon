# Proof-Carrying Quantum Chemistry: Rules for Exact-Gate Molecular Circuits

These rules are for five tools:

- Quantum Circuit Builder with Proof (product `6a7e5036b8c970a6773201b5`)
- Valency Research Paper Library (`6ada7145e001971070f33005`)
- Chemistry Studio (`6ada6971e001971070f32f9a`)
- Live Web Page Browser (`69644454288e0324fa542102`)
- Complex Mathematics Engine (`689df4ac8ee2d1dd79e9035b`)

Every fact below was verified by direct tool runs on 2026-10-22, against quantum service version 0.2.0. Version 3. It adds certified Clifford+T synthesis (section 14).

## 1. Honesty rules (always)

- A qpcert proves properties of a **circuit**. It never proves a molecular energy, a bond length or anything about the chemistry. Say so in every report.
- A simulation from `execute_locally` is observational evidence, not proof.
- Problems that fit in 4 qubits or fewer are easy for classical computers. Never claim quantum advantage or new chemistry. The value of this work lies in four things:
  - replication
  - consistency checking
  - proof-carrying, runnable artifacts
  - precision budgets
- Never invent Hamiltonian coefficients, geometries or reported energies. If a paper does not publish what a step needs, say so and stop that step.
- Report rejections, failures and timeouts verbatim.

## 2. What the tool does (verified)

- **`execute_locally`** runs **Qiskit Aer 0.17.2 (qiskit 2.5.0)**: statevector method, double precision, fixed seeds. The receipt names the backend. It takes Lean source only, up to 4 qubits with `resource_class: standard`.
- **`export_provider_programs`** turns Lean source into OpenQASM 3, Qiskit, Cirq or Braket programs. Angles stay exact rational multiples of pi, and the output is readback-checked. It takes Lean source only.
- **`certify_circuit`** takes a normalized circuit (IR JSON) and a claim ledger and produces a qpcert in File Manager. It takes seconds.
- **`certify_from_lean` rejects any circuit containing a parameterized rotation.** The error is `gate_shape_mismatch` ("gate Rzk/Ry requires controls=0, targets=1, parameters=1"). Use `certify_circuit` for rotation circuits.
- **`get_task` results arrive as a File Manager file.** A completed task lists `result_file` (and, for certification, `certificate_file`) with a `signed_url`. Download the JSON from the signed URL. The run, export or certificate data is under `result.result`, e.g. `result.result.counts` for `execute_locally` and `result.result.artifacts[].canonical_source` for exports. Never publish a signed URL: it is a short-lived bearer link.
- **`certify_circuit` accepts cyclotomic phase levels 2 to 4** (P(2*pi/4) to P(2*pi/16)). A circuit with any `rzk` of level 5 or finer is rejected with `cyclotomic_kernel_level_not_contracted`. Simulation and export accept finer levels. To certify a circuit that needs finer angles, use exact Clifford+T synthesis (section 14).
- **`inspect_circuit` draws a PNG for circuits of up to 20 operations.** For longer circuits, call it without `image_format` (validation and `circuit_subject_sha256` work at any size).
- **File Manager files expire after 7 days.** Extend the expiry of certificates and reports with File Management, and tell the user to download them.

## 3. Bit order of count keys

Count keys from `execute_locally` put **qubit 0 in the leftmost character**. Example: X on q0 of a 2-qubit circuit gives `"10"`. This is the reverse of native Qiskit bitstrings. Read `key[i]` as qubit i.

## 4. Writing rotations exactly

Only exact dyadic angles are allowed. Use **one gate list** for simulation, export and certification.

**Rotations in terms of the phase gate P:**

- Ry(theta), in time order: `Sdg, H, P(theta), H, S`. This is exact up to global phase.
- Rx(theta), in time order: `H, P(theta), H`. This is exact up to global phase.

**The phase gate itself:**

| Phase | Lean | IR |
|---|---|---|
| P(2*pi/2^k) | `.gate (.rot .phase h 1 false) q 0` with h = 2^(k-1) | gate `"rzk"`, `parameters: [{"parameter_type":"cyclotomic_phase","level":k,"inverse":false}]` |
| P(-2*pi/2^k) | `.gate (.rot .phase h (2*h-1) false) q 0` | `rzk` with `"inverse": true` |

**General dyadic angles.** For theta = 2*pi*m/2^K, write m in binary and use one P(2*pi/2^k) for each set bit. Phases add, and so do Ry rotations about the same axis. Keep K as small as the precision target allows.

**Semantic profile:**

- `exact_cyclotomic_2k_v1` when any phase is finer than pi/4.
- `exact_clifford_t_v2` when every phase is a multiple of pi/4.

**Rotations to avoid.** Don't use Lean `.rot .ry` or `.rot .rx` in circuits that must be certified. They simulate and export correctly (`.rot .ry h e` = Qiskit `ry(2*pi*e/h)`), but they can't be certified.

**Lean ops:**

- Single-qubit gates: `.gate .H q 0`, `.gate .X q 0`, `.gate .S q 0`, `.gate .Sdg q 0`.
- Two-qubit gates: `.gate .CX control target`, `.gate .CZ a b`, `.gate .SWAP a b`.

**IR ops:**

- Single-qubit: `{"kind":"gate","op_id":"g0","gate":"h","controls":[],"targets":["q0"],"parameters":[]}`.
- CNOT: gate `"cx"` with `"controls":["q0"]` and `"targets":["q1"]`.
- IR gate names: `i h x y z s sdg t tdg rx ry cry rz rzk crk cx cy cz ch sx swap`.

Example Lean source for Ry(pi/8) on q0:

```lean
import HeytingLean.Quantum.ProofCarrying.CircuitSpec

open HeytingLean.Quantum.ProofCarrying

def spec : CircuitSpec where
  circuitId := "example_ry_pi8"
  semanticProfile := "exact_cyclotomic_2k_v1"
  qubits := 1
  classicalBits := 0
  ops := [.gate .Sdg 0 0, .gate .H 0 0, .gate (.rot .phase 8 1 false) 0 0, .gate .H 0 0, .gate .S 0 0]
  claims := []
  metadataScope := "Ry(pi/8) as Sdg H P(pi/8) H S"

theorem spec_claims : CircuitSpec.ClaimsHold spec := by
  simp [CircuitSpec.ClaimsHold, spec]
```

The IR twin of that example uses `sdg, h, rzk(level 4), h, s`. Its exact_unitary lens equals Ry(pi/8) up to global phase (verified).

## 5. Measuring a qubit Hamiltonian

Write H = sum over Pauli strings P of c_P * P.

1. Group the strings that are diagonal in the same per-qubit basis.
2. For each group, build a measurement circuit: state preparation, then a basis change, then terminal Z. `classicalBits := 0` adds terminal Z on all qubits automatically. The basis change for each qubit:
   - X: append `H`.
   - Y: append `Sdg`, then `H`.
   - Z or I: nothing.
3. Compute each expectation value: <P> = sum over keys of (-1)^(sum of key[i] for i in the support of P) * count / shots.
4. Compute the energy: E = sum of c_P * <P>. Include the identity coefficient, plus any frozen-core or nuclear constants the paper includes.
5. Take the standard error from the per-group sample variance. Use at least 8192 shots per group.

## 6. Classical reference (Complex Mathematics Engine)

- Build the 2^n x 2^n matrix from the Pauli terms with numpy `kron`. Make qubit 0 the leftmost tensor factor, matching the key order.
- Take `eigvalsh` for the exact ground energy.
- Compute exactly:
  - the ansatz energy E(theta)
  - the best angle theta*
  - for each precision level K, the rounded theta_K (nearest multiple of 2*pi/2^K)
  - the rounding error dE_K = E(theta_K) - E(theta*)
- Chemical accuracy is 0.0016 Ha.
- The simulated energy must agree with the exact E(theta_K) within shot error. If it doesn't, stop and report.

## 7. Certification and claim choice

1. Call `inspect_circuit` on the IR gate list. Keep `circuit_subject_sha256` and the exact_unitary lens.
2. Call `certify_circuit`. The ledger always includes a `well_formed` claim. For gate-only state-preparation circuits, also request:
   `{"claim_type":"circuit_property","predicate":{"namespace":"HeytingLean.Quantum.ProofCarrying","name":"exact_unitary_action","version":"v1"},"parameters":{},"relation":"same_unitary_up_to_global_phase"}`
3. Choose the circuit to certify:
   - If K* <= 4 (no phase finer than level 4), certify the dyadic K* state preparation.
   - If K* >= 5, run the Clifford+T synthesis (section 14) and certify its circuit. Simulate that circuit in all four bases as well, so the certified circuit is also the measured one. The dyadic K* circuit can still be simulated and exported as part of the precision study.
4. Read `certified_claim_ids`. Report exactly which claims are kernel-certified:
   - Under `exact_cyclotomic_2k_v1`, `exact_unitary_action` is evaluated in exact arithmetic ("satisfied") but is **not** kernel-replayed. Only `well_formed` is kernel-certified.
   - Under `exact_clifford_t_v2`, the exact unitary is kernel-certified.
5. As an extra check, compare the exact_unitary lens matrix with the intended matrix computed in the Math Engine.

## 8. Operating rules

- Use `resource_class: standard`.
- Run Lean jobs (`execute_locally`, `export_provider_programs`) **one at a time**. Concurrent Lean jobs queue, and they can hit the 300 s Lean emit limit.
- For background tasks, poll `get_task` with `wait_seconds: 60`. Never resubmit a task that is still processing.
- If a task fails with `timed_out: true`, `PCQ_TRANSPORT_FAILED` (503) or HTTP 500, resubmit it once as a new task after about 30 s. If it fails again, report it and continue with the other bond lengths.
- A cold start (the first job after about 15 minutes idle) can take 2 to 10 minutes (`warming_service`, then `waiting_on_kernel`). Warm jobs take about 10 s.

## 9. Finding and reading papers

- **Search** with Valency:
  - `semantic_search_papers` with `query`, `start_date` (e.g. "2026-01"), `limit` 25, `include_abstract` true, `enrich_citations` false and `max_authors` 5.
  - `search_by_abstract` for exact molecule names.
  - `get_paper_by_id` for a known id. Accepts `2606.05968`, `2606.05968v1` or a PMC id.
  - Sources include arxiv, chemrxiv and pubmed.
  - Valency returns metadata and abstracts, not full text. Valency needs the user's own Valency account connection.
- **Full text:** Live Web Page Browser `get_url_markdown` on `https://arxiv.org/html/<id with version>`. Some papers are PDF-only, so say so.
- **Appendices may contain base64-encoded run logs.** Decode them, because they often contain the reference state and settings.
- **Extract:**
  - molecule and every geometry (bond lengths)
  - basis set
  - frozen core and active space
  - fermion-to-qubit mapping, qubit count and tapering
  - reference-state bitstring and ansatz
  - reported energies, with units and the constants they include
  - Pauli coefficients, if printed
- **Check internal consistency where possible.** For example: is the stated reference bitstring the Hartree-Fock state under the stated mapping? Do the energy components sum to the reported total?
- Most recent papers do not print qubit-Hamiltonian coefficients. If the paper or a Hamiltonian tool doesn't supply coefficients, don't build circuits. Report what is missing.

## 10. Chemistry Studio conventions

- **`build_hamiltonian`** returns:
  - `terms` as `[label, coefficient]` pairs, in sparse labels such as `"X0 Z1"`
  - `constant_hartree`, which includes nuclear repulsion and the frozen core
  - `hf_state.bitstring` with **qubit 0 first**, the same order as the quantum tool's count keys
  - `reference_energies.hf_energy_hartree` and `exact_energy_hartree` (exact in the active space)
  - Over 600 terms, the full list goes to `hamiltonian_file`.
- **`parity_tapered`** always uses block spin order and removes 2 qubits. (2e,2o) gives 2 qubits, and (2e,3o) gives 4 qubits.
- **`calculate_energy`** methods: hf, dft, mp2, ccsd, ccsd_t, casci or casscf (both need an active space), and fci. Use RHF, CASCI and FCI to cross-check a paper.
- **`scan_bond`**: `atom_indices` `[anchor, moving]`, `start_distance`, `end_distance`, `points` (2-40) and `method`. Use fci or casci for bond breaking.
- Calculations over about 45 s return `status: processing`. Poll `get_task` with `wait_seconds` 55.
- Verified for LiH STO-3G at 1.595 A:
  - (2e,2o) parity_tapered: 2 qubits, 9 terms, HF bitstring "10".
  - (2e,3o) parity_tapered: 4 qubits, 52 terms, HF bitstring "1100".
- At equilibrium the correlation in these small active spaces is below 1.6 mHa. Angle precision matters mainly on the stretched part of the bond curve.

## 11. Exact state preparation and precision budget (2 qubits)

- Take the ground-state vector g = (a00, a01, a10, a11), in key order q0q1, from `eigh` of the 4x4 Hamiltonian. Fix the global sign so it is real.
- Angles:
  - t0 = 2*atan2(hypot(a10,a11), hypot(a00,a01))
  - phi0 = 2*atan2(a01,a00)
  - phi1 = 2*atan2(a11,a10)
  - alpha = (phi0+phi1)/2
  - beta = (phi0-phi1)/2
- Circuit: `Ry(t0) q0; Ry(alpha) q1; CX(q0,q1); Ry(beta) q1; CX(q0,q1)`. This prepares g exactly. All the Ry gates are uncontrolled, so the global phases from the decomposition and from wrapping angles mod 2*pi are harmless.
- Precision level K: round each angle to m*2*pi/2^K, with m an integer. Expand P(m*2*pi/2^K) in binary over m mod 2^K: bit j adds the level k = K-j phase, where level 1 = Z, level 2 = S, level 3 = T and level k >= 4 = rzk(k). In Lean, rzk(k) is `.rot .phase 2^(k-1) 1`.
- The energy error dE_K = E(rounded) - E0 is **not monotonic** in K, because each angle is rounded independently. Report the full table for K = 2..10.
- K* is the smallest K for which this K and every finer K are within 1.6 mHa.
- Example, LiH STO-3G (2e,2o) at R = 3.0 A:
  - dE: 48.8 mHa (K=2), 2.14 (K=3), 2.16 (K=4), 0.0083 (K=5), and at most 0.08 for K = 6..10. So K* = 5.
  - Gate list: 23 gates.
  - Predicted ZZ probabilities (00, 01, 10, 11): 0.0260, 0.0583, 0.8809, 0.0349.

## 12. Complex Mathematics Engine expression rules

- One expression only: no newlines or semicolons. Use nested `lambda`.
- `float()` and `int()` are blocked. Return numpy values.
- The filter reads `in (` as a function call. Write `for a in [x, y]`, not `in (x, y)`.
- Use `np.arange` instead of `range`.
- Call your own lambdas as `(name)(args)`, not `name(args)`. This includes recursion: write `(f)(f, ...)`.
- The filter reads any keyword followed by `(` as a function call: `if (`, `else (`, `in (`, `and (`. Write `x if cond else y` without parentheses after the keyword. Where a branch starts with a recursive call, prefix it: `else []+(f)(f, ...)` for lists, `else 0+(f)(f, ...)` for numbers.
- The bitwise operator `&` fails at run time. Use `//` and `%` for bit arithmetic.
- Also verified to work: list comprehensions with several `for` clauses, `[*x]`, dict literals, string slicing, `np.einsum`, `np.lexsort`, `np.argwhere`, `np.unravel_index`, `np.unique`, `np.full`, `np.tile`, `np.repeat`, `np.stack`, `np.argsort(..., kind='stable')`.
- Allowed numpy functions include `np.kron`, `np.linalg.eigh`, `np.arctan2`, `np.hypot`, `np.round`, `np.cos`, `np.sin`, `np.array`, `np.eye`, `np.diag` and `np.arange`.
- The full LiH budget expression (about 1.1 k characters) ran in 6.5 ms, and its result matched local numpy to 1e-12.

- **Verified template.** Replace `HAMILTONIAN_SUM` with `(c)*np.kron(A,B) + ...`, one product per term, where A is the Pauli on q0 and B the Pauli on q1, each I, X or Z. The template covers I, X and Z terms only. 2-qubit `parity_tapered` (2e,2o) Hamiltonians have no Y terms. If a term contains Y, stop and report.
  - It returns `[E0, [t0, alpha, beta], rows]`.
  - Each row is `[K, m_t0, m_alpha, m_beta, dE_mHa]`, for K = 2..10.

```
(lambda I,X,Z,CX: (lambda H: (lambda w,v: (lambda g: (lambda t0,p0,p1: (lambda al,be,ry: (lambda st: [w[0], np.array([t0,al,be]), np.array([[K] + [np.round(a/(2*np.pi/2.0**K)) for a in [t0,al,be]] + [(1000*((lambda s: s@H@s)((st)(*[np.round(a/(2*np.pi/2.0**K))*(2*np.pi/2.0**K) for a in [t0,al,be]])) - w[0]))] for K in np.arange(2,11)])])(lambda a,b,c: CX@np.kron(I,(ry)(c))@CX@np.kron(I,(ry)(b))@np.kron((ry)(a),I)@np.array([1.,0.,0.,0.])))((p0+p1)/2,(p0-p1)/2,lambda t: np.array([[np.cos(t/2),-np.sin(t/2)],[np.sin(t/2),np.cos(t/2)]])))(2*np.arctan2(np.hypot(g[2],g[3]),np.hypot(g[0],g[1])),2*np.arctan2(g[1],g[0]),2*np.arctan2(g[3],g[2])))(v[:,0]))(*np.linalg.eigh(H)))(HAMILTONIAN_SUM))(np.eye(2),np.array([[0.,1.],[1.,0.]]),np.diag([1.,-1.]),np.array([[1.,0,0,0],[0,1.,0,0],[0,0,0,1.],[0,0,1.,0]]))
```

## 13. What a report must contain

- The paper: arXiv id, version and date.
- The extracted inputs and any consistency findings.
- The exact classical results.
- The circuits, with gate counts, T counts and precision level, and which circuit was certified (dyadic or Clifford+T).
- The simulated energies with their errors.
- A precision-budget table.
- Certificate file IDs, with the certified claim IDs.
- The exported programs.
- A plain statement of what is and is not proven.
- The File Manager expiry date.

## 14. Certified Clifford+T synthesis (when K* >= 5)

Every Clifford+T circuit falls under `exact_clifford_t_v2`, where `exact_unitary_action` is **kernel-certified**. Clifford+T is universal, so any state preparation can be approximated to any precision by an exact Clifford+T word and certified with the strongest claim the tool issues.

The synthesis runs as one Complex Mathematics Engine expression (0.12 s on the engine). It enumerates all 24,528 single-qubit Clifford+T words in Matsumoto-Amano normal form with up to 8 syllables, keeps the 5 closest words per T count for each rotation slot, scores every combination by its exact energy, and breaks exact ties by T count, then gate count. It returns three gate lists over {H, S, Sdg, T, Z}. **The full template and the rules for building circuits from it are in the companion context document "Certified Clifford+T Synthesis for Exact-Gate Chemistry Circuits" (`6ada99f0e001971070f333a0`).**

Verified on LiH STO-3G (2e,2o): 2.5 A, 47 gates, T count 17, 0.357 mHa, `qpcert_f47b8566cf85f0c6`; 3.0 A, 47 gates, T count 17, 0.066 mHa, `qpcert_f3f0c674daa1a372`. Both certify `well_formed` and `exact_unitary_action` with axioms `[]`.
