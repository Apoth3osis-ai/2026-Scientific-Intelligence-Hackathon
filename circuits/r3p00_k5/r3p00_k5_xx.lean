import HeytingLean.Quantum.ProofCarrying.CircuitSpec

open HeytingLean.Quantum.ProofCarrying

def spec : CircuitSpec where
  circuitId := "r3p00_k5_xx"
  semanticProfile := "exact_cyclotomic_2k_v1"
  qubits := 2
  classicalBits := 0
  ops := [.gate .Sdg 0 0, .gate .H 0 0, .gate (.rot .phase 16 1 false) 0 0, .gate .T 0 0, .gate .S 0 0, .gate .H 0 0, .gate .S 0 0, .gate .Sdg 1 0, .gate .H 1 0, .gate .T 1 0, .gate .S 1 0, .gate .Z 1 0, .gate .H 1 0, .gate .S 1 0, .gate .CX 0 1, .gate .Sdg 1 0, .gate .H 1 0, .gate (.rot .phase 8 1 false) 1 0, .gate .S 1 0, .gate .Z 1 0, .gate .H 1 0, .gate .S 1 0, .gate .CX 0 1, .gate .H 0 0, .gate .H 1 0]
  claims := []
  metadataScope := "LiH STO-3G (2e,2o) parity_tapered state preparation, angles m=[13, -4, 26] x 2pi/2^5, measure XX"

theorem spec_claims : CircuitSpec.ClaimsHold spec := by
  simp [CircuitSpec.ClaimsHold, spec]
