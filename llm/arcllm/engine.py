"""Talk to a vLLM OpenAI server through raw /v1/completions with token-id prompts.

Why raw completions instead of /chat/completions: we render the chat template ourselves,
so we see the exact reasoning tokens, and we can EMULATE A THINKING BUDGET exactly:
truncate the reasoning at B tokens, append "\n</think>\n\n" and let the model write only
the answer (s1-style budget forcing; the same thing vLLM's --reasoning-config /
thinking_token_budget does server-side on GPUs). One long generation at the top budget
therefore yields the results for every smaller budget at the cost of short answer
continuations only.
"""
import json
import os
import time
import urllib.error
import urllib.request
import zlib


class Engine:
    def __init__(self, base_url, served_name, tokenizer_path, sampling, template_kwargs=None,
                 timeout=6 * 3600):
        from transformers import AutoTokenizer
        self.url = base_url.rstrip("/") + "/completions"
        self.name = served_name
        self.tok = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
        self.end_think = self.tok.convert_tokens_to_ids("</think>")
        self.sampling = sampling                     # temperature/top_p/top_k
        self.template_kwargs = template_kwargs or {}
        self.timeout = timeout
        self.supports_ids = None                     # does the server return completion token ids?
        self.use_seed = os.environ.get("ARC_SEED", "0") == "1"   # vLLM-TPU 0.32: HTTP 500 on per-request seeds
        self.close_ids = self.encode("\n") + [self.end_think] + self.encode("\n\n")

    # -------------------------------------------------------------- tokenizer helpers
    def encode(self, s):
        return self.tok.encode(s, add_special_tokens=False)

    def decode(self, ids):
        return self.tok.decode(ids, skip_special_tokens=False)

    def render(self, messages, **extra):
        ids = self.tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=True,
                                           **dict(self.template_kwargs, **extra))
        if isinstance(ids, dict) or hasattr(ids, "input_ids"):
            ids = ids["input_ids"]
        return list(ids)

    # -------------------------------------------------------------- one raw request
    def complete(self, prompt_ids, max_tokens, seed):
        payload = {"model": self.name, "prompt": prompt_ids, "max_tokens": int(max_tokens),
                   "skip_special_tokens": False, **self.sampling}
        if self.use_seed:
            payload["seed"] = int(seed)
        if self.supports_ids is not False:
            payload["return_token_ids"] = True
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:600]
            if e.code == 500 and self.use_seed:
                self.use_seed = False                    # retry once, unseeded from now on
                return self.complete(prompt_ids, max_tokens, seed)
            if self.supports_ids is None and "return_token_ids" in detail:
                self.supports_ids = False
                return self.complete(prompt_ids, max_tokens, seed)
            return {"error": f"HTTP {e.code}: {detail}"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"[:400]}
        ch = body["choices"][0]
        ids = ch.get("token_ids")
        if ids is None:
            if self.supports_ids is None:
                self.supports_ids = False
            ids = self.encode(ch.get("text") or "")      # re-tokenised: close enough for budgets
        elif self.supports_ids is None:
            self.supports_ids = True
        usage = body.get("usage") or {}
        return {"ids": list(ids), "text": ch.get("text") or "", "finish": ch.get("finish_reason"),
                "n": usage.get("completion_tokens", len(ids)), "wall": time.time() - t0}

    # -------------------------------------------------------------- budgeted generation
    def generate(self, prompt_ids, budget, answer_room, seed):
        """Reason for at most `budget` tokens, then answer within `answer_room` tokens.

        Returns a record with reasoning_ids (natural reasoning, up to budget+answer_room
        tokens, kept so smaller budgets can be emulated later), the answer text and the
        token cost actually charged at this budget."""
        r = self.complete(prompt_ids, budget + answer_room, seed)
        if "error" in r:
            return {"error": r["error"], "cost": 0}
        ids, calls, wall = r["ids"], 1, r["wall"]
        gen_tokens = len(ids)
        if self.end_think in ids:
            p = ids.index(self.end_think)
            reasoning = ids[:p]
            natural_end = True
        else:
            p, reasoning, natural_end = None, ids, False
        rec = {"reasoning_len": len(reasoning), "natural_end": natural_end, "seed": seed}
        if natural_end and p <= budget:
            answer_ids = ids[p + 1:]
            if r["finish"] == "length":                 # answer itself cut: give it more room once
                c = self.complete(prompt_ids + ids, answer_room, seed + 17)
                calls += 1
                if "error" not in c:
                    answer_ids = answer_ids + c["ids"]
                    gen_tokens += len(c["ids"])
                    wall += c["wall"]
            rec.update(forced=False, answer=self.decode(answer_ids),
                       cost=p + 1 + len(answer_ids))
        else:
            ans = self.force_answer(prompt_ids, reasoning[:budget], answer_room, seed + 31)
            calls += 1
            gen_tokens += ans.get("n", 0)
            wall += ans.get("wall", 0)
            rec.update(forced=True, answer=ans.get("text", ""), answer_error=ans.get("error"),
                       cost=min(budget, len(reasoning)) + len(self.close_ids) + ans.get("n", 0))
        rec.update(reasoning_ids=reasoning, calls=calls, gen_tokens=gen_tokens, wall=wall,
                   loop=is_loop(self.decode(reasoning[-4000:])) if reasoning else False)
        return rec

    def force_answer(self, prompt_ids, reasoning_ids, answer_room, seed):
        """Close the reasoning after `reasoning_ids` and generate only the answer."""
        c = self.complete(prompt_ids + list(reasoning_ids) + self.close_ids, answer_room, seed)
        if "error" in c:
            return {"error": c["error"], "text": "", "n": 0, "wall": 0}
        text = c["text"]
        if self.end_think in c["ids"]:                   # rare: it re-opened and closed thinking
            text = self.decode(c["ids"][c["ids"].index(self.end_think) + 1:])
        return {"text": text, "n": len(c["ids"]), "wall": c["wall"], "finish": c["finish"]}


def is_loop(text, ratio=0.02):
    """A degenerate repetition loop: compresses far better than prose or grids."""
    raw = (text or "").encode("utf-8", "replace")
    return len(raw) > 2000 and len(zlib.compress(raw, 6)) / len(raw) < ratio
