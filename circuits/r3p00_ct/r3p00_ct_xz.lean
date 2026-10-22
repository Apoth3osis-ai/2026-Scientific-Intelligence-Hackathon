import HeytingLean.Quantum.ProofCarrying.CircuitSpec

open HeytingLean.Quantum.ProofCarrying

def spec : CircuitSpec where
  circuitId := "r3p00_ct_xz"
  semanticProfile := "exact_clifford_t_v2"
  qubits := 2
  classicalBits := 0
  ops := [.gate .H 0 0, .gate .T 0 0, .gate .H 0 0, .gate .S 0 0, .gate .T 0 0, .gate .H 0 0, .gate .T 0 0, .gate .H 0 0, .gate .T 0 0, .gate .H 0 0, .gate .T 0 0, .gate .H 0 0, .gate .T 0 0, .gate .H 0 0, .gate .S 0 0, .gate .T 0 0, .gate .H 0 0, .gate .Z 0 0, .gate .T 0 0, .gate .H 0 0, .gate .Z 0 0, .gate .H 1 0, .gate .T 1 0, .gate .H 1 0, .gate .Sdg 1 0, .gate .CX 0 1, .gate .S 1 0, .gate .T 1 0, .gate .H 1 0, .gate .T 1 0, .gate .H 1 0, .gate .S 1 0, .gate .T 1 0, .gate .H 1 0, .gate .T 1 0, .gate .H 1 0, .gate .S 1 0, .gate .T 1 0, .gate .H 1 0, .gate .T 1 0, .gate .H 1 0, .gate .T 1 0, .gate .H 1 0, .gate .T 1 0, .gate .H 1 0, .gate .Sdg 1 0, .gate .CX 0 1, .gate .H 0 0]
  claims := []
  metadataScope := "LiH STO-3G (2e,2o) parity_tapered state preparation at R=3.0 A, exact Clifford+T synthesis, T-count 17, measure XZ"

theorem spec_claims : CircuitSpec.ClaimsHold spec := by
  simp [CircuitSpec.ClaimsHold, spec]
