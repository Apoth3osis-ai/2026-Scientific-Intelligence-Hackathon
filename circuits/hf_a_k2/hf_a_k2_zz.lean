import HeytingLean.Quantum.ProofCarrying.CircuitSpec

open HeytingLean.Quantum.ProofCarrying

def spec : CircuitSpec where
  circuitId := "hf_a_k2_zz"
  semanticProfile := "exact_clifford_t_v2"
  qubits := 2
  classicalBits := 0
  ops := [.gate .Sdg 0 0, .gate .H 0 0, .gate .Z 0 0, .gate .H 0 0, .gate .S 0 0, .gate .Sdg 1 0, .gate .H 1 0, .gate .S 1 0, .gate .Z 1 0, .gate .H 1 0, .gate .S 1 0, .gate .CX 0 1, .gate .Sdg 1 0, .gate .H 1 0, .gate .S 1 0, .gate .Z 1 0, .gate .H 1 0, .gate .S 1 0, .gate .CX 0 1]
  claims := []
  metadataScope := "LiH STO-3G (2e,2o) parity_tapered state preparation, angles m=[2, -1, -1] x 2pi/2^2, measure ZZ"

theorem spec_claims : CircuitSpec.ClaimsHold spec := by
  simp [CircuitSpec.ClaimsHold, spec]
