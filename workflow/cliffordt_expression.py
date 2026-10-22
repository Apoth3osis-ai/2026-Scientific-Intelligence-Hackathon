"""Build the one-line Complex Mathematics Engine expression for exact Clifford+T synthesis.

The expression is the in-workflow version of circuits/generate_cliffordt.py: the same normal-form
enumeration, the same per-slot candidate selection, the same exact-energy scoring and the same tie
rule (within 1e-9 Ha of the lowest energy: lowest T count, then fewest gates, then enumeration
order), so it returns the same gate lists. It obeys the engine's expression rules (one line, nested lambdas, no float(),
int(), range or "in (").

It returns [E0, [t0, alpha, beta], E_circuit, dE_mHa, [q0_U0, q1_Ua, q1_Ub], front], where the three
gate lists are in time order over {H, S, Sdg, T, Z} and front is [[T count, dE_mHa], ...], the best
error found at each total T count.

Usage:
  python cliffordt_expression.py template               print the template (HAMILTONIAN_SUM placeholder)
  python cliffordt_expression.py <R_angstrom>           print the filled expression for one bond length
  python cliffordt_expression.py check                  evaluate it locally for 2.5 and 3.0 A and compare
                                                        with circuits/<name>/<name>_report.json
"""
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CW = ['', 'H', 'S', 'HS', 'SH', 'SS', 'HSH', 'HSS', 'SHS', 'SSH', 'SSS', 'HSHS', 'HSSH', 'HSSS', 'SHSS', 'SSHS',
      'HSHSS', 'HSSHS', 'SHSSH', 'SHSSS', 'SSHSS', 'HSHSSH', 'HSHSSS', 'HSSHSS']

BODY = """
(lambda I,X,Z,Hd,S,T,CW,CL,EXPL,NMAX:
 (lambda H:
  (lambda w,v:
   (lambda g:
    (lambda t0,p0,p1:
     (lambda al,be:
      (lambda P:
       (lambda C24:
        (lambda A,B:
         (lambda Ls:
          (lambda blocks:
           (lambda M,PRE,NN,BB,CC:
            (lambda TC,GL:
             (lambda ry:
              (lambda d0,da,db:
               (lambda sel:
                (lambda P0,Pa,Pb:
                 (lambda v1:
                  (lambda v2:
                   (lambda wq:
                    (lambda psi:
                     (lambda E,tsum:
                      (lambda dec,step:
                       (lambda passf:
                        (lambda simp:
                         (lambda gl:
                          (lambda tie:
                           (lambda ijk:
                            (lambda gates:
                             [w[0], [t0,al,be], E[ijk[0],ijk[1],ijk[2]], (E[ijk[0],ijk[1],ijk[2]]-w[0])*1000, gates,
                              [[t, (np.min(E[tsum==t])-w[0])*1000] for t in np.unique(tsum)]]
                            )([(gl)(gi) for gi in [P0[ijk[0]],Pa[ijk[1]],Pb[ijk[2]]]])
                           )(tie[np.lexsort((np.arange(tie.shape[0]), np.array([np.size(np.array((gl)(P0[r[0]])+(gl)(Pa[r[1]])+(gl)(Pb[r[2]]))) for r in tie]), np.array([tsum[r[0],r[1],r[2]] for r in tie])))[0]])
                          )(np.argwhere(E<=np.min(E)+1e-9))
                         )(lambda gi: [x for st in [(simp)(simp,[q if q=='H' else {'T':1,'S':2}[q] for q in [*(dec)(gi)]])] for t in st for x in EXPL[t]])
                        )(lambda f,toks: toks if toks==(passf)(toks) else []+(f)(f,(passf)(toks)))
                       )(lambda toks: [t for t in [*(step)(step,[],toks)] if t!=0])
                      )(lambda gi: (['T'] if PRE[gi]==1 else []) + [tok for j in np.arange(NN[gi]) for tok in [['H','T'],['S','H','T']][(BB[gi]//2**(NN[gi]-1-j))%2]] + [ch for ch in CW[CC[gi]]],
                        lambda f,out,rest: out if rest==[] else []+(f)(f,out[:-1],rest[1:]) if out!=[] and rest[0]=='H' and out[-1]=='H' else []+(f)(f,out[:-1]+[(out[-1]+rest[0])%8],rest[1:]) if out!=[] and rest[0]!='H' and out[-1]!='H' else []+(f)(f,out+[rest[0]],rest[1:]))
                     )(np.real(np.einsum('ijkx,xy,ijky->ijk',np.conj(psi),H,psi)), TC[P0][:,None,None]+TC[Pa][None,:,None]+TC[Pb][None,None,:])
                    )(np.concatenate([wq[:,:,:,:1,:],wq[:,:,:,1:,::-1]],axis=3).reshape(P0.shape[0],Pa.shape[0],Pb.shape[0],4))
                   )(np.einsum('kcb,ijab->ijkac',M[Pb],v2))
                  )(np.concatenate([v1[:,:,:1,:],v1[:,:,1:,::-1]],axis=2))
                 )(np.einsum('ia,jb->ijab',M[P0][:,:,0],M[Pa][:,:,0]))
                )((sel)(d0),(sel)(da),(sel)(db))
               )(lambda d: np.concatenate([ix[np.argsort(d[ix]+1e-6*GL[ix],kind='stable')][:5] for t in np.arange(NMAX+2) for ix in [np.where(TC==t)[0]]]))
              )(1-np.abs(M[:,:,0]@np.conj((ry)(t0)[:,0]))**2, 1-np.abs(M[:,:,0]@np.conj((ry)(al)[:,0]))**2, 1-np.abs(np.einsum('ij,nij->n',np.conj((ry)(be)),M))/2)
             )(lambda t: np.array([[np.cos(t/2),-np.sin(t/2)],[np.sin(t/2),np.cos(t/2)]]))
            )(PRE+NN, PRE+2*NN+np.sum((BB[:,None]//2**np.arange(NMAX))%2,axis=1)+np.array(CL)[CC])
           )(np.concatenate([np.einsum('cij,wjk->wcik',C24,Ls[n]@(T if p==1 else np.eye(2))).reshape(-1,2,2) for p,n in blocks]),
             np.concatenate([np.full(24*2**n,p) for p,n in blocks]), np.concatenate([np.full(24*2**n,n) for p,n in blocks]),
             np.concatenate([np.repeat(np.arange(2**n),24) for p,n in blocks]), np.concatenate([np.tile(np.arange(24),2**n) for p,n in blocks]))
          )([[p,n] for p in [0,1] for n in np.arange(NMAX+1)])
         )((lambda f: (f)(f,[np.eye(2)[None]],NMAX))(lambda f,acc,k: acc if k==0 else []+(f)(f,acc+[np.stack([A@acc[-1],B@acc[-1]],1).reshape(-1,2,2)],k-1)))
        )(T@Hd, T@Hd@S)
       )(np.array([(P)(P,c) for c in CW]))
      )(lambda f,c: np.eye(2) if c=='' else {'H':Hd,'S':S}[c[-1]]@(f)(f,c[:-1]))
     )((p0+p1)/2,(p0-p1)/2)
    )(2*np.arctan2(np.hypot(g[2],g[3]),np.hypot(g[0],g[1])),2*np.arctan2(g[1],g[0]),2*np.arctan2(g[3],g[2])))
   (v[:,0]))
  (*np.linalg.eigh(H)))
 (HAMILTONIAN_SUM))
(np.eye(2),np.array([[0.,1.],[1.,0.]]),np.diag([1.,-1.]),np.array([[1.,1.],[1.,-1.]])/np.sqrt(2),np.diag([1.,1j]),np.diag([1.,np.exp(1j*np.pi/4)]),
 CW_LIST,CL_LIST,{'H':['H'],1:['T'],2:['S'],3:['S','T'],4:['Z'],5:['Z','T'],6:['Sdg'],7:['Sdg','T']},8)
"""


def template():
    one = " ".join(line.strip() for line in BODY.strip().splitlines())
    one = one.replace("( ", "(").replace(" )", ")")
    return (one.replace("CW_LIST", json.dumps(CW).replace('"', "'"))
               .replace("CL_LIST", json.dumps([len(c) for c in CW])))


def ham_sum(terms):
    parts = []
    for label, c in terms:
        f = ["I", "I"]
        if label != "I":
            for t in label.split():
                f[int(t[1:])] = t[0]
        parts.append(f"({c!r})*np.kron({f[0]},{f[1]})")
    return "+".join(parts)


def filled(R):
    p = next(p for p in json.load(open(os.path.join(ROOT, "hamiltonians", "LiH_sto3g_2e2o_parity_tapered_bond_curve.json"),
                                       encoding="utf-8"))["points"] if p["R_angstrom"] == R)
    return template().replace("HAMILTONIAN_SUM", ham_sum(p["terms"]))


def check(circuits_root=os.path.join(ROOT, "circuits")):
    t = template()
    for banned in ("float(", "int(", "in (", "\n", ";"):
        assert banned not in t, banned
    assert "range(" not in t.replace("np.arange(", ""), "range("
    # the engine's filter reads a keyword followed by "(" as a function call
    bad = re.findall(r"\b(?:if|else|in|and|or|not)\s*\(", t)
    assert not bad, bad
    # and it allows calls only to numpy functions, methods, or custom lambdas written as (name)(args)
    bare = [b for b in re.findall(r"(?<![\w.])([A-Za-z_]\w*)\(", t) if b not in ("lambda", "np")]
    assert not bare, bare
    print(f"template: {len(t)} characters, rule check passed")
    for R, name in ((2.5, "r2p50_ct"), (3.0, "r3p00_ct")):
        out = eval(filled(R), {"np": np})
        rep = json.load(open(os.path.join(circuits_root, name, name + "_report.json"), encoding="utf-8"))
        same = out[4] == [rep["slot_words_time_order"][k] for k in ("q0_U0", "q1_Ua", "q1_Ub")]
        print(f"R={R}: dE={out[3]:.6f} mHa (generator {rep['dE_mHa']:.6f}), gate lists identical: {same}")


if __name__ == "__main__":
    arg = sys.argv[1]
    if arg == "template":
        print(template())
    elif arg == "check":
        check(*sys.argv[2:3])
    else:
        print(filled(float(arg)))
