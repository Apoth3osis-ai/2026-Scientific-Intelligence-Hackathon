import HeytingLean.Quantum.ProofCarrying.CircuitSpec

open HeytingLean.Quantum.ProofCarrying

def spec : CircuitSpec where
  circuitId := "r1p50_k8_zz"
  semanticProfile := "exact_cyclotomic_2k_v1"
  qubits := 2
  classicalBits := 0
  ops := [.gate .Sdg 0 0, .gate .H 0 0, .gate (.rot .phase 64 1 false) 0 0, .gate (.rot .phase 32 1 false) 0 0, .gate (.rot .phase 16 1 false) 0 0, .gate (.rot .phase 8 1 false) 0 0, .gate .T 0 0, .gate .S 0 0, .gate .H 0 0, .gate .S 0 0, .gate .Sdg 1 0, .gate .H 1 0, .gate (.rot .phase 128 1 false) 1 0, .gate (.rot .phase 32 1 false) 1 0, .gate (.rot .phase 16 1 false) 1 0, .gate .S 1 0, .gate .Z 1 0, .gate .H 1 0, .gate .S 1 0, .gate .CX 0 1, .gate .Sdg 1 0, .gate .H 1 0, .gate (.rot .phase 32 1 false) 1 0, .gate (.rot .phase 16 1 false) 1 0, .gate .S 1 0, .gate .Z 1 0, .gate .H 1 0, .gate .S 1 0, .gate .CX 0 1]
  claims := []
  metadataScope := "LiH STO-3G (2e,2o) parity_tapered state preparation, angles m=[126, -51, -52] x 2pi/2^8, measure ZZ"

theorem spec_claims : CircuitSpec.ClaimsHold spec := by
  simp [CircuitSpec.ClaimsHold, spec]
