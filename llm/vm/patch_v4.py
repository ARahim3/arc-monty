"""Local, unofficial patches that let vllm-tpu 0.32 serve Qwen3.8 (hybrid GDN) on TPU v4 (16 MiB VMEM).
Idempotent. Applied by setup.sh only when JAX reports TPU v4."""
import os
import sys
import tpu_inference
D = os.path.dirname(tpu_inference.__file__)
k = os.path.join(D, "kernels/ragged_paged_attention/v3/kernel.py")
s = open(k).read()
if "case 4:  # local patch" not in s:
    v4 = """        case 4:  # local patch (arc_monty): TPU v4 has 16 MiB VMEM, use 8x smaller KV tiles
            if case == RpaCase.DECODE:
                bq_sz = 1
                bkv_sz = min(max(min_bkv_sz_to_peak // 8, page_size), max_kv)
                bq_csz = 1
                bkv_csz = min(max(min_bkv_sz_to_peak // 8, page_size), max_kv)
            else:
                bq_sz = min(256 // num_q_heads_per_kv_head, max_q // 2)
                bkv_sz = min(256, max_kv)
                bq_csz = min(128 // num_q_heads_per_kv_head, max_q)
                bkv_csz = min(256, align_to(max_kv // 2, page_size))
"""
    anchor = "        case 5 | 6:\n            if case == RpaCase.DECODE:"
    assert anchor in s, "RPA anchor not found"
    open(k, "w").write(s.replace(anchor, v4 + anchor, 1))
    print("patched RPA kernel")
c = os.path.join(D, "kernels/gdn/v3/config.py")
s = open(c).read()
if "DEFAULT_VMEM_FRACTION = 0.7" in s:
    open(c, "w").write(s.replace("DEFAULT_VMEM_FRACTION = 0.7", "DEFAULT_VMEM_FRACTION = 0.9", 1))
    print("patched GDN VMEM fraction")
