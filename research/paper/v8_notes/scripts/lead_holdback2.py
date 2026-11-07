"""Lead's check, existing 16k data only. (1) Discordant test of exchangeability on Qwen folds. (2) Prediction lift inside fold programs.
(3) Same-token comparison: k plain stochastic samples vs one full-data run + folds, scored pass@2, verified first."""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, random, collections, math
ROOT=_REPO
CH=json.load(open(f'{ROOT}/data/kaggle_format/agi2_eval_challenges.json'))
SOL=json.load(open(f'{ROOT}/data/kaggle_format/agi2_eval_solutions.json'))
def gkey(g): return (len(g)*len(g[0]),len(g),len(g[0]),json.dumps(g))
def lo(rec):
    rounds=[r for r in rec.get('rounds',[]) if 'test_out' in r]
    if not rounds: return None,False,None
    v=[r for r in rounds if r.get('verified')]
    r=v[0] if v else rounds[-1]
    return r['test_out'],bool(v),r
recs=[json.loads(l) for l in open(f'{ROOT}/llm/results/qwen38_faloo_greedy_b16384.jsonl')]
F=collections.defaultdict(list); FULL={}
for r in recs:
    if r.get('kind') not in('full','fold') or 'error' in r: continue
    tid=r['task_id']; out,ver,_=lo(r); nt=len(SOL[tid])
    if out is None: d={}
    else: d=dict(zip(r['query_ids'],out))
    tests=[d.get(f'test:{t}') for t in range(nt)]
    right=[tests[t]==SOL[tid][t] for t in range(nt)]
    x=dict(ver=ver,tests=tests,right=right,cost=r.get('cost',0))
    if r['kind']=='full': FULL[tid]=x
    else:
        demos=sorted(CH[tid]['train'],key=lambda p:gkey(p['input']))
        x['held']=d.get(f"demo:{r['fold']}")==demos[r['fold']]['output']
        F[tid].append(x)
tasks=sorted(FULL)
# (1) discordant test, task-clustered
def disc(ts):
    hr=sum(x['held'] for t in ts for x in F[t]); tr=sum(sum(x['right'])/len(x['right']) for t in ts for x in F[t]); n=sum(len(F[t]) for t in ts)
    a=sum(1-sum(x['right'])/len(x['right']) for t in ts for x in F[t] if x['held']); b=sum(sum(x['right'])/len(x['right']) for t in ts for x in F[t] if not x['held'])
    return hr,tr,n,a,b
hr,tr,n,a,b=disc(tasks); print(f'(1) folds {n}: held right {hr} ({100*hr/n:.1f}%), test right {tr:.1f} ({100*tr/n:.1f}%); discordant held-only {a:.1f}, test-only {b:.1f}')
random.seed(0); D=[];R=[]
for _ in range(10000):
    s=[random.choice(tasks) for _ in tasks]; hr,tr,n,a,b=disc(s); D.append(100*(hr-tr)/n); R.append(a-b)
D.sort();R.sort(); print('    held rate minus test rate, points: %+.1f [%+.1f, %+.1f]; discordant difference %+.1f [%+.1f, %+.1f]'%(sum(D)/len(D),D[250],D[9750],sum(R)/len(R),R[250],R[9750]))
pos=neg=0
for t in tasks:
    _,_,_,a,b=disc([t])
    if a>b: pos+=1
    elif b>a: neg+=1
print(f'    tasks with more held-only than test-only: {pos}; the reverse: {neg}; sign p ~ {sum(math.comb(pos+neg,k) for k in range(pos,pos+neg+1))/2**(pos+neg):.2g} (one-sided)')
# (2) prediction lift inside fold programs that fit their n-1 demos
vf=[(t,x) for t in tasks for x in F[t] if x['ver']]
def prec(xs): return sum(sum(x['right'])/len(x['right']) for x in xs)/max(1,len(xs))
hx=[x for t,x in vf if x['held']]; mx=[x for t,x in vf if not x['held']]
print(f'(2) fold programs verified on what they saw: {len(vf)}, precision {100*prec([x for t,x in vf]):.1f}%; also predict held-out {len(hx)}: {100*prec(hx):.1f}%; miss it {len(mx)}: {100*prec(mx):.1f}%')
by=collections.defaultdict(list)
for t,x in vf: by[t].append(x)
ts=sorted(by); L=[]; 
for _ in range(10000):
    s=[random.choice(ts) for _ in ts]; h=[x for t in s for x in by[t] if x['held']]; m=[x for t in s for x in by[t] if not x['held']]
    if h and m: L.append(100*(prec(h)-prec(m)))
L.sort(); print('    difference, points: %+.1f [%+.1f, %+.1f] (tasks %d)'%(sum(L)/len(L),L[int(.025*len(L))],L[int(.975*len(L))],len(ts)))
# (3) plain samples
P=collections.defaultdict(list)
for fn in ['qwen38_ps_b16384.jsonl','qwen38_ps_xhigh_b16384.jsonl']:
    for l in open(f'{ROOT}/llm/results/{fn}'):
        r=json.loads(l)
        if 'error' in r or r.get('task_id') not in SOL: continue
        tid=r['task_id']; nt=len(SOL[tid])
        rounds=[x for x in r.get('rounds',[]) if 'n_ok' in x]
        v=[x for x in rounds if x.get('verified')]
        c=(v[0] if v else (rounds[-1] if rounds else None))
        if c is None or 'test_out' not in c:
            P[tid].append(dict(ver=False,tests=[None]*nt,cost=r.get('cost',0),file=fn)); continue
        P[tid].append(dict(ver=bool(v),tests=(c['test_out']+[None]*nt)[:nt],cost=r.get('cost',0),file=fn))
cnt=collections.Counter(len(P[t]) for t in tasks); print('(3) plain samples per task:',sorted(cnt.items()))
print('    keys of a plain test_out vs SOL ok?', sum(1 for t in tasks for x in P[t] if x['ver'] and x['tests'][0] is not None))
def pass2(cands,tid):
    """cands: list of (rank, tests) ; keep first two distinct per test output; fraction of outputs right."""
    nt=len(SOL[tid]); ok=0
    for k in range(nt):
        seen=[]
        for rank,tests in sorted(cands,key=lambda c:c[0]):
            g=tests[k]
            if g is None: continue
            s=json.dumps(g)
            if s not in seen: seen.append(s)
            if len(seen)==2: break
        ok+=json.dumps(SOL[tid][k]) in seen
    return ok/nt
def plain_score(t,k):
    xs=P[t][:k]; return pass2([(0 if x['ver'] else 1,x['tests']) for x in xs],t)
def fold_score(t):
    c=[(0 if FULL[t]['ver'] else 2,FULL[t]['tests'])]
    for x in F[t]:
        c.append((0 if (x['ver'] and x['held']) else (1 if x['ver'] else 2),x['tests']))
    return pass2(c,t)
def fold_score_nofull(t,m=None):
    xs=F[t][:m] if m else F[t]
    return pass2([(0 if (x['ver'] and x['held']) else (1 if x['ver'] else 2),x['tests']) for x in xs],t)
com=[t for t in tasks if len(P[t])>=3]
print('    tasks with >=3 plain samples',len(com))
print('    mean runs per task: plain', sum(len(P[t]) for t in com)/len(com), 'full+folds', sum(1+len(F[t]) for t in com)/len(com))
print('    tokens per task: plain %.1fk ; full+folds %.1fk'%(sum(x['cost'] for t in com for x in P[t])/len(com)/1000, sum(FULL[t]['cost']+sum(x['cost'] for x in F[t]) for t in com)/len(com)/1000))
for k in (1,2,3,4):
    print(f'    plain first {k} samples: pass@2 {sum(plain_score(t,k) for t in com):.1f} of {len(com)}')
print(f'    full-data greedy alone: {sum(pass2([(0,FULL[t]["tests"])],t) for t in com):.1f}')
print(f'    full-data greedy + all folds: {sum(fold_score(t) for t in com):.1f}')
print(f'    folds only (no full-data run): {sum(fold_score_nofull(t) for t in com):.1f}')
# paired bootstrap, all plain samples vs full+folds
A={t:plain_score(t,len(P[t])) for t in com}; B={t:fold_score(t) for t in com}
Ds=[]
for _ in range(10000):
    s=[random.choice(com) for _ in com]; Ds.append(sum(B[t]-A[t] for t in s))
Ds.sort(); print('    full+folds minus all plain: %+.1f [%+.1f, %+.1f]; tasks better %d, worse %d'%(sum(B[t]-A[t] for t in com),Ds[250],Ds[9750],sum(B[t]>A[t] for t in com),sum(B[t]<A[t] for t in com)))
# second-sample yield on tasks whose first run failed verification
fail=[t for t in tasks if not FULL[t]['ver']]
print(f'(4) tasks where the greedy full run did not verify: {len(fail)}')
pl=[(t,x) for t in fail for x in P[t]]
print('    plain stochastic sample on those tasks: runs %d, verified %d (%.1f%%), right among verified %.1f'%(len(pl),sum(x['ver'] for t,x in pl),100*sum(x['ver'] for t,x in pl)/len(pl),sum(sum(json.dumps(x['tests'][k])==json.dumps(SOL[t][k]) for k in range(len(SOL[t])))/len(SOL[t]) for t,x in pl if x['ver'])))
fl=[(t,x) for t in fail for x in F[t]]
okf=[(t,x) for t,x in fl if x['ver'] and x['held']]
print('    greedy fold on those tasks:             runs %d, held-back verified %d (%.1f%%), right among those %.1f'%(len(fl),len(okf),100*len(okf)/len(fl),sum(sum(x['right'])/len(x['right']) for t,x in okf)))
