"""Read-only: print this account's Kaggle accelerator quota (GPU/TPU used vs allowed, refresh time).

Usage: python tools/gpu_quota.py [--json]   (needs your own Kaggle API credentials in the environment)
"""
import json
import sys

from kagglesdk import KaggleClient
from kagglesdk.kernels.types.kernels_api_service import ApiGetAcceleratorQuotaStatisticsRequest


def quota() -> dict:
    with KaggleClient() as c:
        return c.kernels.kernels_api_client.get_accelerator_quota_statistics(
            ApiGetAcceleratorQuotaStatisticsRequest()).to_dict()


def seconds(s: str) -> float:
    # The API returns durations like '20025.444.0s' or '21600s'.
    s = s.rstrip("s")
    parts = s.split(".")
    return float(".".join(parts[:2])) if len(parts) > 1 else float(s)


if __name__ == "__main__":
    d = quota()
    if "--json" in sys.argv:
        print(json.dumps(d))
    else:
        g = d["gpuQuota"]
        used, allowed = seconds(g["timeUsed"]), seconds(g["totalTimeAllowed"])
        print(f"GPU used {used / 3600:.2f} h of {allowed / 3600:.2f} h, left {(allowed - used) / 60:.0f} min; "
              f"refresh {d['quotaRefreshTime']}")
