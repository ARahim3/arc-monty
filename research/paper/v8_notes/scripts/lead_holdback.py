"""Lead's check on the GREEDY Qwen run only (not the sampling run): is a program that was verified on a demo it never saw
more often right on test than a plain verified program, at the same token cost per run?"""
import os  # noqa: E402  (release: paths from the repo root)
_REPO = os.environ.get("ARC_MONTY_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))  # repo root
import json, os, random, sys, collections, math
ROOT=_REPO
CH=json.load(open(f'{ROOT}/data/kaggle_format/agi2_eval_challenges.json'))
SOL=json.load(open(f'{ROOT}/data/kaggle_format/agi2_eval_solutions.json'))
recs=[json.loads(l) for l in open(f'{ROOT}/llm/results/qwen38_faloo_greedy_b16384.jsonl')]
def gkey(g): return (len(g)*len(g[0]),len(g),len(g[0]),json.dumps(g))
def learner_output(rec):
    rounds=[r for r in rec.get('rounds',[]) if 'test_out' in r]
    if not rounds: return None,False
    v=[r for r in rounds if r.get('verified')]
    r=v[0] if v else rounds[-1]
    return r['test_out'],bool(v)
def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*2
    p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (round(100*(c-h),1),round(100*(c+h),1))
rows=[]
for r in recs:
    if r.get('kind') not in ('full','fold') or 'error' in r: continue
    tid=r['task_id']; out,ver=learner_output(r)
    nt=len(SOL[tid]); n=len(CH[tid]['train'])
    if out is None:
        rows.append(dict(kind=r['kind'],task=tid,fold=r['fold'],n=n,ver=False,held=None,right=0.0,cost=r.get('cost',0),tests=None)); continue
    d=dict(zip(r['query_ids'],out))
    right=sum(d.get(f'test:{t}')==SOL[tid][t] for t in range(nt))/nt
    held=None
    if r['kind']=='fold':
        demos=sorted(CH[tid]['train'],key=lambda p:gkey(p['input']))
        held=d.get(f"demo:{r['fold']}")==demos[r['fold']]['output']
    rows.append(dict(kind=r['kind'],task=tid,fold=r['fold'],n=n,ver=ver,held=held,right=right,cost=r.get('cost',0),tests=tuple(json.dumps(d.get(f'test:{t}')) for t in range(nt))))
full=[x for x in rows if x['kind']=='full']; fold=[x for x in rows if x['kind']=='fold']
def show(name,xs,den):
    k=sum(x['right'] for x in xs); n=len(xs); t=len({x['task'] for x in xs})
    print(f"{name:58s} runs {n:4d} ({100*n/max(1,den):5.1f}% of {den}), tasks {t:3d}, right {k:6.1f}, precision {100*k/max(1,n):5.1f}% wilson {wilson(round(k),n)}; mean cost {sum(x['cost'] for x in xs)/max(1,n)/1000:.1f}k")
print('--- per RUN')
show('full-data, verified (the plain rule)',[x for x in full if x['ver']],len(full))
show('fold, verified on its n-1 demos',[x for x in fold if x['ver']],len(fold))
show('fold, verified on n-1 AND predicts held-out (held-back rule)',[x for x in fold if x['ver'] and x['held']],len(fold))
show('fold, verified on n-1 but misses held-out (rejected)',[x for x in fold if x['ver'] and x['held'] is False],len(fold))
show('fold, predicts held-out, not verified on n-1',[x for x in fold if (not x['ver']) and x['held']],len(fold))
print('mean right per run: full %.4f, fold %.4f; mean held rate over folds %.4f'%(sum(x['right'] for x in full)/len(full),sum(x['right'] for x in fold)/len(fold),sum(bool(x['held']) for x in fold)/len(fold)))
print('--- exchangeability check over all folds (each fold model has one held-out demo and the test pair(s) as its unseen items)')
print('  held-out demo right: %d/%d = %.1f%%; test right: %.1f/%d = %.1f%%'%(sum(bool(x['held']) for x in fold),len(fold),100*sum(bool(x['held']) for x in fold)/len(fold),sum(x['right'] for x in fold),len(fold),100*sum(x['right'] for x in fold)/len(fold)))
hw=sum(1-x['right'] for x in fold if x['held']); wh=sum(x['right'] for x in fold if not x['held'])
print('  held right & test wrong: %.1f ; held wrong & test right: %.1f (equal in expectation under exchangeability)'%(hw,wh))
print('--- per TASK, expected over a random fold per task vs the one full run: same token cost (1 run per task)')
byt=collections.defaultdict(list)
for x in fold: byt[x['task']].append(x)
exp_ans=0;exp_right=0
for t,xs in byt.items():
    n=len(xs); ok=[x for x in xs if x['ver'] and x['held']]
    exp_ans+=len(ok)/n; exp_right+=sum(x['right'] for x in ok)/n
print('  one random held-back fold per task: expected answered %.1f of 120, expected right %.1f, precision %.1f%%'%(exp_ans,exp_right,100*exp_right/exp_ans))
fv=[x for x in full if x['ver']]
print('  one full-data run per task:          answered %d of 120, right %.1f, precision %.1f%%'%(len(fv),sum(x['right'] for x in fv),100*sum(x['right'] for x in fv)/len(fv)))
print('  total right if the answer is just the output (no gate): full %.1f; random fold %.1f'%(sum(x['right'] for x in full),sum(sum(y['right'] for y in xs)/len(xs) for xs in byt.values())))
# task-clustered bootstrap for precision difference: held-back fold vs full verified
random.seed(0); tasks=sorted(byt); B=10000; diffs=[]; ph=[]; pf=[]
fm={x['task']:x for x in full}
for _ in range(B):
    s=[random.choice(tasks) for _ in tasks]
    a=r=0.0; fa=fr=0.0
    for t in s:
        xs=byt[t]; ok=[x for x in xs if x['ver'] and x['held']]
        a+=len(ok)/len(xs); r+=sum(x['right'] for x in ok)/len(xs)
        if fm[t]['ver']: fa+=1; fr+=fm[t]['right']
    if a>0 and fa>0:
        ph.append(r/a); pf.append(fr/fa); diffs.append(r/a-fr/fa)
q=lambda v,p: sorted(v)[int(p*len(v))]
print('  bootstrap by task, precision: held-back %.1f [%.1f, %.1f]; full verified %.1f [%.1f, %.1f]; diff %+.1f [%+.1f, %+.1f]'%(100*sum(ph)/len(ph),100*q(ph,.025),100*q(ph,.975),100*sum(pf)/len(pf),100*q(pf,.025),100*q(pf,.975),100*sum(diffs)/len(diffs),100*q(diffs,.025),100*q(diffs,.975)))
print('--- tasks: held-back verified on any fold, vs full verified')
anyh={t for t,xs in byt.items() if any(x['ver'] and x['held'] for x in xs)}
fvs={x['task'] for x in fv}
print('  tasks with any held-back fold',len(anyh),'; full verified',len(fvs),'; both',len(anyh&fvs),'; only held-back',len(anyh-fvs),'; only full',len(fvs-anyh))
def best(t):
    ok=[x for x in byt[t] if x['ver'] and x['held']]
    return sum(x['right'] for x in ok)/len(ok)
print('  mean precision of held-back folds on tasks where full did NOT verify:', [ (t,round(best(t),2)) for t in sorted(anyh-fvs)])
print('  full verified right on tasks with no held-back fold:', [(t,fm[t]['right']) for t in sorted(fvs-anyh)])
print('  cost: full mean %.1fk, fold mean %.1fk'%(sum(x['cost'] for x in full)/len(full)/1000,sum(x['cost'] for x in fold)/len(fold)/1000))
print('--- by n'); 
for n in (2,3,4,5,6):
    f1=[x for x in fv if x['n']==n]; f2=[x for x in fold if x['n']==n and x['ver'] and x['held']]; f3=[x for x in fold if x['n']==n]
    if f3: print(f'  n={n}: full verified {sum(x["right"] for x in f1):.1f}/{len(f1)}; held-back {sum(x["right"] for x in f2):.1f}/{len(f2)} of {len(f3)} folds')
