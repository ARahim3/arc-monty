#!/usr/bin/env bash
# Idempotent VM setup for the LLM-column benchmark (run ON the TPU VM; safe to re-run).
# Env + vllm-tpu into /mnt/data/envs/vllm, models into tmpfs /mnt/data/ram/models.
set -euo pipefail
sudo mkdir -p /mnt/data && sudo chown "$USER:$USER" /mnt/data && mkdir -p /mnt/data/envs /mnt/data/logs
command -v tmux >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq tmux >/dev/null)
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
[ -x /mnt/data/envs/vllm/bin/python ] || uv venv --python 3.12 /mnt/data/envs/vllm
source /mnt/data/envs/vllm/bin/activate
VLLM_TPU_VERSION=${VLLM_TPU_VERSION:-0.32.0}
python -c "import vllm, tpu_inference" 2>/dev/null && [ -f /mnt/data/envs/vllm/.stamp-$VLLM_TPU_VERSION ] || {
  uv pip install "vllm-tpu==$VLLM_TPU_VERSION" "huggingface_hub[hf_xet]" 2>&1 | tail -3
  touch /mnt/data/envs/vllm/.stamp-$VLLM_TPU_VERSION; }
# RAM disk for the weights (boot disk has ~88 GB free; both models in bf16 are ~120 GB)
RAMSZ=${RAMSZ:-200g}
mkdir -p /mnt/data/ram && { mountpoint -q /mnt/data/ram || sudo mount -t tmpfs -o "size=$RAMSZ,mode=755,uid=$(id -u),gid=$(id -g)" tmpfs /mnt/data/ram; }
mkdir -p /mnt/data/ram/models
python - <<'PY'
import jax; d = jax.devices()
print(len(d), d[0].device_kind, d[0].memory_stats().get("bytes_limit", 0) / 1e9, "GB/chip", jax.__version__)
PY
python -c "import vllm; print('vllm', vllm.__version__)"
python -c "import jax; import sys; sys.exit(0 if 'v4' in jax.devices()[0].device_kind.lower() else 1)" 2>/dev/null \
  && python $(dirname "$0")/patch_v4.py
free -g | head -2; df -h /mnt/data /mnt/data/ram | tail -2
