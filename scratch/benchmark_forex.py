"""Benchmark script to measure latency of _fetch_live_fawazahmed implementation."""

import time
import urllib.error
import urllib.request
from unittest.mock import patch

from src.tools.forex import _fetch_live_fawazahmed


def benchmark_normal() -> float:
    """Benchmark when endpoints respond normally."""
    start = time.perf_counter()
    res = _fetch_live_fawazahmed()
    elapsed = time.perf_counter() - start
    assert res[1] == "fawazahmed-cdn"
    return elapsed


def _mock_urlopen_first_fails(req, *args, **kwargs):
    url = req.full_url if hasattr(req, "full_url") else str(req)
    if "jsdelivr.net" in url:
        time.sleep(0.5)  # Simulate failure delay
        raise urllib.error.URLError("Primary CDN connection timeout")
    # Secondary CDN
    return orig_urlopen(req, *args, **kwargs)


orig_urlopen = urllib.request.urlopen


def benchmark_fallback_scenario() -> float:
    """Benchmark when primary CDN fails after 0.5s timeout."""
    start = time.perf_counter()
    with patch("urllib.request.urlopen", side_effect=_mock_urlopen_first_fails):
        res = _fetch_live_fawazahmed()
        elapsed = time.perf_counter() - start
        assert res[1] == "fawazahmed-cdn"
    return elapsed


if __name__ == "__main__":
    print("Running baseline benchmarks...")

    # Warmup
    try:
        _fetch_live_fawazahmed()
    except Exception:
        pass

    normal_times = [benchmark_normal() for _ in range(5)]
    avg_normal = sum(normal_times) / len(normal_times)
    print(f"Normal execution avg latency: {avg_normal:.4f}s (min: {min(normal_times):.4f}s)")

    fallback_times = [benchmark_fallback_scenario() for _ in range(5)]
    avg_fallback = sum(fallback_times) / len(fallback_times)
    print(f"Fallback scenario (primary fails in 0.5s) avg latency: {avg_fallback:.4f}s (min: {min(fallback_times):.4f}s)")
