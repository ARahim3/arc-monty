"""CPU test of qwen_phase with a mock /v1/completions server (no GPU, no vLLM).

    python3 llm/kaggle/test_qwen_phase.py                 # mock end-to-end + deadline + smoke
    python3 llm/kaggle/test_qwen_phase.py --template DIR  # also compare render_qwen38 with the HF
                                                          # chat template in DIR (needs transformers)
"""
import json
import os
import random
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qwen_phase as qp                                    # noqa: E402

CH = json.load(open(os.path.join(HERE, "..", "..", "data", "kaggle_format", "agi2_eval_challenges.json")))
SOL = json.load(open(os.path.join(HERE, "..", "..", "data", "kaggle_format", "agi2_eval_solutions.json")))
TEST_IN = {json.dumps(t["test"][0]["input"]): tid for tid, t in CH.items()}


class Mock(BaseHTTPRequestHandler):
    delay = 0.0

    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        p, mt = req["prompt"], req["max_tokens"]
        time.sleep(self.delay)
        tid = next((t for t in CH if qp.render_qwen38(qp.ps_messages(CH[t]))[:4000] in p[:4000]), None)
        rnd = random.Random(req.get("seed", 0))
        if tid and sorted(CH).index(tid) % 3 == 0:
            # a "correct" program: look the train/test answers up by input (verifies on train)
            table = {json.dumps(x["input"]): x["output"] for x in CH[tid]["train"]}
            table[json.dumps(CH[tid]["test"][0]["input"])] = SOL[tid][0]
            prog = ("import json\nT=%s\ndef transform(grid):\n    return T.get(json.dumps(grid), grid)\n"
                    % json.dumps(table))
        else:
            prog = "def transform(grid):\n    return grid\n"
        answer = "Here is the program.\n```python\n" + prog + "```"
        if p.endswith(qp.CLOSE_THINK):                      # forced: answer only
            text = answer
        elif rnd.random() < 0.5 or len(answer) // 4 + 10 > mt:   # thinks past the cap
            text = "hmm " * mt
        else:
            text = "short reasoning\n</think>\n\n" + answer
        n = len(text) // 4
        if n > mt:
            text, n, fin = text[:mt * 4], mt, "length"
        else:
            fin = "stop"
        body = json.dumps({"choices": [{"text": text, "finish_reason": fin}], "usage": {"completion_tokens": n}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(port):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    if "--template" in sys.argv:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(sys.argv[sys.argv.index("--template") + 1])
        t = CH[sorted(CH)[0]]
        msgs = qp.ps_messages(t)
        for conv in (msgs, msgs + [{"role": "assistant", "content": "prog A"}, {"role": "user", "content": "fix it"}]):
            ref = tok.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
            mine = qp.render_qwen38(conv)
            assert ref == mine, ("template mismatch", ref[-400:], mine[-400:])
        print("template: render_qwen38 == HF apply_chat_template (1- and 2-round conversations)")

    srv = serve(18123)
    url = "http://127.0.0.1:18123/v1"
    order = sorted(CH)[:12]
    out = os.path.join(tempfile.mkdtemp(), "qwen.json")
    res = qp.run_qwen_phase(CH, order, time.time() + 3600, out, budget_per_round=512, max_rounds=2,
                            base_url=url, concurrency=6, answer_room=40000, min_round_s=0)
    disk = json.load(open(out))
    assert disk == res and len(res) == 12, len(res)
    right = sum(r["outputs"][0]["attempt"] == SOL[t][0] for t, r in res.items())
    ver = sum(r["verified"] for r in res.values())
    exp = sum(sorted(CH).index(t) % 3 == 0 for t in order)
    assert ver == exp and right >= exp, (ver, right, exp)
    for t, r in res.items():
        assert set(r) >= {"verified", "outputs", "n_tokens"} and len(r["outputs"]) == len(CH[t]["test"])
    print(f"end-to-end: 12 tasks, {ver} verified (expected {exp}), {right} test-correct, file ok")

    # deadline: slow server, deadline in 6 s -> stops cleanly with partial results
    Mock.delay = 1.5
    out2 = os.path.join(tempfile.mkdtemp(), "qwen.json")
    t0 = time.time()
    res2 = qp.run_qwen_phase(CH, sorted(CH), time.time() + 8, out2, 512, 2, base_url=url, concurrency=4,
                             answer_room=4096, min_round_s=2, shutdown_margin_s=2)
    el = time.time() - t0
    assert el < 20 and len(res2) < len(CH), (el, len(res2))
    print(f"deadline: returned after {el:.1f}s with {len(res2)} tasks done (of {len(CH)})")

    # smoke: 3 tasks, 1 round
    Mock.delay = 0.0
    out3 = os.path.join(tempfile.mkdtemp(), "qwen.json")
    res3 = qp.run_qwen_phase(CH, sorted(CH), time.time() + 600, out3, 16384, 2, base_url=url, smoke=3,
                             min_round_s=0)
    assert len(res3) == 3
    print("smoke: 3 tasks ok")
    srv.shutdown()
    print("ALL OK")


if __name__ == "__main__":
    main()
