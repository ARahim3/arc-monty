"""Expected-score model of the tri notebook (Qwen PS phase -> NVARC phase -> merge) on 240 hidden tasks.

All rates are per task and come from measurements where we have them:
  Qwen3.8 PS, xhigh, 16k/round, <=2 rounds, sample 0 on the 120 public-eval tasks (TPU, llm/results/qwen38_ps_b16384.jsonl):
    P(verified) = 23/120, P(correct | verified) = 17.5/23, P(correct | unverified, best program) = 2.5/97,
    mean cost 34.2k tokens/sample (verified-in-round-1 samples ~17.5k).
  NVARC full-coverage fork: ~31 LB (public forks 28-34). Qwen/NVARC correlation rho = 0.43 (forum, FOYSAL).
  NVARC time per eval-sized task: fitted to the 4 tasks of the tri v2 smoke run (train = 0.0369*tok + 7.64e-6*tok^2 s,
    decode ~300 s per test output, cap ~1250 s); 606 s mean on the 120 public-eval tasks (sizes like the hidden set;
    the 240-task Kaggle test placeholder is drawn from the TRAINING split, so it says nothing about hidden sizes).
Usage: python research/arc2/tri_model.py
"""
import math

N_TASKS = 240
WALL_H = 12 - 10 / 60 - 8 / 60          # global_end_time = start + 12h - 10min; ~8 min of pre-GPU cells (est.)
QWEN_SETUP_S = 760                       # measured in the v2 smoke: py312 + vllm install 250 s + server 450 s + misc
P_V, P_C_V, P_C_U = 23 / 120, 17.5 / 23, 2.5 / 97
COST = 34.2e3
P_N, RHO = 0.31, 0.43
MONTY = 0.0                              # pure Monty v5 scored 0.00 on the hidden set (lead, 10-29)


def cond_nvarc(p_q, p_n=P_N, rho=RHO):
    """P(N correct | Q correct), P(N correct | Q not correct) for binary indicators with correlation rho."""
    joint = p_n * p_q + rho * math.sqrt(p_n * (1 - p_n) * p_q * (1 - p_q))
    return joint / p_q, (p_n - joint) / (1 - p_q)


def score(qwen_hours, R=500.0, tau=606.0, p_n=P_N, rho=RHO, p_v=P_V, p_cv=P_C_V, p_cu=P_C_U, cost=COST,
          nvarc_on_verified=False):
    q_gen_s = max(0.0, qwen_hours * 3600 - QWEN_SETUP_S) * 0.95 if qwen_hours > 0 else 0.0   # 5% tail waste
    n_q = min(N_TASKS, q_gen_s * R / cost)
    q_used_h = (QWEN_SETUP_S + n_q * cost / R / 0.95) / 3600 if n_q > 0 else 0.0  # phase ends early if all done
    n_h = WALL_H - min(qwen_hours, q_used_h)
    nvarc_slots = 4 * n_h * 3600 / tau                       # tasks NVARC can finish
    p_qc = p_v * p_cv                                         # Qwen verified-and-correct
    pn_qc, pn_nqc = cond_nvarc(p_qc, p_n, rho)
    # P(N | Q unverified): unverified tasks are "not Qc" minus the verified-wrong ones (assume those look like not-Qc)
    pn_u = pn_nqc
    # NVARC queue: alphabetical, skipping Qwen-verified tasks; Qwen covers from the other end
    queue = N_TASKS - (0 if nvarc_on_verified else n_q * p_v)
    reach = min(queue, nvarc_slots)
    # tasks NVARC reaches that Qwen did not cover vs did cover: Qwen covers the LAST n_q tasks alphabetically
    fresh = N_TASKS - n_q                                    # tasks only NVARC can cover (the alphabetically first)
    nv_fresh = min(reach, fresh)
    nv_on_q = max(0.0, reach - fresh)                        # unverified Qwen tasks NVARC also reaches
    q_unv = n_q * (1 - p_v)
    s = 0.0
    s += n_q * p_v * p_cv                                    # verified Qwen programs (attempt 1)
    if nvarc_on_verified:                                    # NVARC fills attempt 2 of verified-but-wrong tasks
        s += n_q * p_v * (1 - p_cv) * pn_nqc * min(1, nv_on_q / max(n_q, 1e-9))
    s += nv_fresh * p_n
    nv_unv = min(nv_on_q, q_unv) if not nvarc_on_verified else nv_on_q * (1 - p_v)
    s += nv_unv * pn_u + (q_unv - nv_unv) * p_cu
    s += N_TASKS * MONTY * 0.5
    return 100 * s / N_TASKS, dict(n_q=round(n_q), q_h=round(min(qwen_hours, q_used_h), 2), nvarc_h=round(n_h, 2),
                                   nvarc_done=round(reach), nvarc_queue=round(queue))


if __name__ == "__main__":
    print("NVARC alone (no Qwen):", ["%.1f" % score(0, tau=t)[0] for t in (470, 606, 745)], "(tau 470/606/745 s)")
    for R in (350, 500, 650):
        for tau in (470, 606, 745):
            row = []
            for h in (0, 1.5, 2.5, 3.5, 4.5, 6.0, 8.0):
                sc, d = score(h, R=R, tau=tau)
                row.append(f"{h:>3}h {sc:5.1f}")
            print(f"R={R} tok/s tau={tau}s | " + " | ".join(row))
    print()
    print("tri v3 detail (4.5 h):", [score(4.5, R=R, tau=606)[1] for R in (350, 500, 650)])
