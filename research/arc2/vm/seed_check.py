"""VM side: do seeds reach vLLM-TPU, and do outputs vary? Toy non-ARC prompt only (plan section 0). Prints a small report."""
import json
import urllib.error
import urllib.request

PROMPT = "Here is a short invented sentence about a river, a boat and the weather:"
SAMPLING = {"temperature": 1.0, "top_p": 0.95, "top_k": 20}


def call(port, payload):
    body = dict(model="qwen38", prompt=PROMPT, max_tokens=48, **payload)
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return 200, json.loads(r.read().decode())["choices"][0]["text"]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:220]


for port in (8001, 8003):
    code, txt = call(port, dict(SAMPLING, seed=123))
    print(f"port {port} request with seed=123: HTTP {code}: {txt[:200]!r}")
a = [call(8001, SAMPLING)[1] for _ in range(4)]
b = [call(8003, SAMPLING)[1] for _ in range(4)]
print("same prompt, temperature 1, server 8001, 4 repeats: distinct =", len(set(a)))
print("same prompt, temperature 1, server 8003, 4 repeats: distinct =", len(set(b)))
print("across servers: shared outputs =", len(set(a) & set(b)))
g = [call(8001, {"temperature": 0.0})[1] for _ in range(2)] + [call(8003, {"temperature": 0.0})[1]]
print("control, temperature 0, 2 on 8001 + 1 on 8003: distinct =", len(set(g)))
for t in a[:2] + b[:1]:
    print("  sample:", repr(t[:110]))
