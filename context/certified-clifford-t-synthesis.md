# Certified Clifford+T Synthesis for Exact-Gate Chemistry Circuits

Companion to the Agent Context document "Proof-Carrying Quantum Chemistry Rules" (`6ada6b06e001971070f32fc7`). It is for the Complex Mathematics Engine (`689df4ac8ee2d1dd79e9035b`) and the Quantum Circuit Builder with Proof (`6a7e5036b8c970a6773201b5`). Verified 2026-10-22 against quantum service 0.2.0.

**Use it when** the precision budget needs a phase finer than level 4 (K* >= 5). `certify_circuit` accepts cyclotomic levels 2 to 4 only, so dyadic circuits at K >= 5 cannot be certified. An exact Clifford+T circuit can be certified at any precision.

## Why Clifford+T

Every Clifford+T circuit falls under `exact_clifford_t_v2`, where `exact_unitary_action` is **kernel-certified**. Clifford+T is universal, so any state preparation can be approximated to any precision by an exact Clifford+T word, and the result can be certified with the strongest claim the tool issues.

## Method

One Complex Mathematics Engine expression, verified 2026-10-22. It runs in 0.12 s on the engine, and its output is identical to the reference script `circuits/generate_cliffordt.py` in the public repo.

1. Same circuit shape as the 2-qubit exact state preparation in the rules document (section 11): `U0 q0; Ua q1; CX(q0,q1); Ub q1; CX(q0,q1)`.
2. Enumerate every single-qubit Clifford+T word in Matsumoto-Amano normal form, `(T | e)(HT | SHT)^n C`, with n <= 8 syllables and C one of the 24 Cliffords: 24,528 exact unitaries.
3. For each slot keep the 5 words closest to the ideal rotation at every T count. U0 and Ua act on |0>, so they are matched on the state; Ub is matched as a full unitary.
4. Score every combination (50 x 50 x 50) by its exact energy.
5. Many combinations prepare the same state with different words. Among combinations within 1e-9 Ha of the lowest energy, choose the lowest T count, then the fewest gates, then the first in enumeration order. The choice is deterministic.
6. Merge adjacent phase gates and cancel H H, so each slot is a short list over {H, S, Sdg, T, Z}.

## Template

Replace `HAMILTONIAN_SUM` exactly as in the precision-budget template of the rules document (section 12): `(c)*np.kron(A,B) + ...`, one product per Pauli term, A on q0 and B on q1, each I, X or Z. It returns `[E0, [t0, alpha, beta], E_circuit, dE_mHa, [q0_U0, q1_Ua, q1_Ub], front]`, where the three gate lists are in time order and `front` lists `[T count, best dE_mHa]`.

```
(lambda I,X,Z,Hd,S,T,CW,CL,EXPL,NMAX: (lambda H: (lambda w,v: (lambda g: (lambda t0,p0,p1: (lambda al,be: (lambda P: (lambda C24: (lambda A,B: (lambda Ls: (lambda blocks: (lambda M,PRE,NN,BB,CC: (lambda TC,GL: (lambda ry: (lambda d0,da,db: (lambda sel: (lambda P0,Pa,Pb: (lambda v1: (lambda v2: (lambda wq: (lambda psi: (lambda E,tsum: (lambda dec,step: (lambda passf: (lambda simp: (lambda gl: (lambda tie: (lambda ijk: (lambda gates: [w[0], [t0,al,be], E[ijk[0],ijk[1],ijk[2]], (E[ijk[0],ijk[1],ijk[2]]-w[0])*1000, gates, [[t, (np.min(E[tsum==t])-w[0])*1000] for t in np.unique(tsum)]])([(gl)(gi) for gi in [P0[ijk[0]],Pa[ijk[1]],Pb[ijk[2]]]]))(tie[np.lexsort((np.arange(tie.shape[0]), np.array([np.size(np.array((gl)(P0[r[0]])+(gl)(Pa[r[1]])+(gl)(Pb[r[2]]))) for r in tie]), np.array([tsum[r[0],r[1],r[2]] for r in tie])))[0]]))(np.argwhere(E<=np.min(E)+1e-9)))(lambda gi: [x for st in [(simp)(simp,[q if q=='H' else {'T':1,'S':2}[q] for q in [*(dec)(gi)]])] for t in st for x in EXPL[t]]))(lambda f,toks: toks if toks==(passf)(toks) else []+(f)(f,(passf)(toks))))(lambda toks: [t for t in [*(step)(step,[],toks)] if t!=0]))(lambda gi: (['T'] if PRE[gi]==1 else []) + [tok for j in np.arange(NN[gi]) for tok in [['H','T'],['S','H','T']][(BB[gi]//2**(NN[gi]-1-j))%2]] + [ch for ch in CW[CC[gi]]], lambda f,out,rest: out if rest==[] else []+(f)(f,out[:-1],rest[1:]) if out!=[] and rest[0]=='H' and out[-1]=='H' else []+(f)(f,out[:-1]+[(out[-1]+rest[0])%8],rest[1:]) if out!=[] and rest[0]!='H' and out[-1]!='H' else []+(f)(f,out+[rest[0]],rest[1:])))(np.real(np.einsum('ijkx,xy,ijky->ijk',np.conj(psi),H,psi)), TC[P0][:,None,None]+TC[Pa][None,:,None]+TC[Pb][None,None,:]))(np.concatenate([wq[:,:,:,:1,:],wq[:,:,:,1:,::-1]],axis=3).reshape(P0.shape[0],Pa.shape[0],Pb.shape[0],4)))(np.einsum('kcb,ijab->ijkac',M[Pb],v2)))(np.concatenate([v1[:,:,:1,:],v1[:,:,1:,::-1]],axis=2)))(np.einsum('ia,jb->ijab',M[P0][:,:,0],M[Pa][:,:,0])))((sel)(d0),(sel)(da),(sel)(db)))(lambda d: np.concatenate([ix[np.argsort(d[ix]+1e-6*GL[ix],kind='stable')][:5] for t in np.arange(NMAX+2) for ix in [np.where(TC==t)[0]]])))(1-np.abs(M[:,:,0]@np.conj((ry)(t0)[:,0]))**2, 1-np.abs(M[:,:,0]@np.conj((ry)(al)[:,0]))**2, 1-np.abs(np.einsum('ij,nij->n',np.conj((ry)(be)),M))/2))(lambda t: np.array([[np.cos(t/2),-np.sin(t/2)],[np.sin(t/2),np.cos(t/2)]])))(PRE+NN, PRE+2*NN+np.sum((BB[:,None]//2**np.arange(NMAX))%2,axis=1)+np.array(CL)[CC]))(np.concatenate([np.einsum('cij,wjk->wcik',C24,Ls[n]@(T if p==1 else np.eye(2))).reshape(-1,2,2) for p,n in blocks]), np.concatenate([np.full(24*2**n,p) for p,n in blocks]), np.concatenate([np.full(24*2**n,n) for p,n in blocks]), np.concatenate([np.repeat(np.arange(2**n),24) for p,n in blocks]), np.concatenate([np.tile(np.arange(24),2**n) for p,n in blocks])))([[p,n] for p in [0,1] for n in np.arange(NMAX+1)]))((lambda f: (f)(f,[np.eye(2)[None]],NMAX))(lambda f,acc,k: acc if k==0 else []+(f)(f,acc+[np.stack([A@acc[-1],B@acc[-1]],1).reshape(-1,2,2)],k-1))))(T@Hd, T@Hd@S))(np.array([(P)(P,c) for c in CW])))(lambda f,c: np.eye(2) if c=='' else {'H':Hd,'S':S}[c[-1]]@(f)(f,c[:-1])))((p0+p1)/2,(p0-p1)/2))(2*np.arctan2(np.hypot(g[2],g[3]),np.hypot(g[0],g[1])),2*np.arctan2(g[1],g[0]),2*np.arctan2(g[3],g[2]))) (v[:,0])) (*np.linalg.eigh(H))) (HAMILTONIAN_SUM)) (np.eye(2),np.array([[0.,1.],[1.,0.]]),np.diag([1.,-1.]),np.array([[1.,1.],[1.,-1.]])/np.sqrt(2),np.diag([1.,1j]),np.diag([1.,np.exp(1j*np.pi/4)]), ['', 'H', 'S', 'HS', 'SH', 'SS', 'HSH', 'HSS', 'SHS', 'SSH', 'SSS', 'HSHS', 'HSSH', 'HSSS', 'SHSS', 'SSHS', 'HSHSS', 'HSSHS', 'SHSSH', 'SHSSS', 'SSHSS', 'HSHSSH', 'HSHSSS', 'HSSHSS'],[0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6],{'H':['H'],1:['T'],2:['S'],3:['S','T'],4:['Z'],5:['Z','T'],6:['Sdg'],7:['Sdg','T']},8)
```

## Building the circuits

Write `q0_U0` on qubit 0, then `q1_Ua` on qubit 1, then `CX 0 1`, then `q1_Ub` on qubit 1, then `CX 0 1`. Lean: `.gate .H q 0`, `.gate .S q 0`, `.gate .Sdg q 0`, `.gate .T q 0`, `.gate .Z q 0`. IR: gates `h`, `s`, `sdg`, `t`, `z`. Profile `exact_clifford_t_v2` for both. Add the measurement-basis tails from the rules document (section 5). Then simulate (`execute_locally`), export (`export_provider_programs`), validate (`inspect_circuit`) and certify (`certify_circuit` with `well_formed` and `exact_unitary_action`) exactly as for any other circuit.

## Verified results

LiH STO-3G (2e,2o) parity_tapered:

| R (A) | Gates | T count | Circuit error vs exact (mHa) | Certificate |
|---|---|---|---|---|
| 2.5 | 47 | 17 | 0.357 | `qpcert_f47b8566cf85f0c6` |
| 3.0 | 47 | 17 | 0.066 | `qpcert_f3f0c674daa1a372` |

Both certificates kernel-certify `well_formed` and `exact_unitary_action` with axioms `[]`.
