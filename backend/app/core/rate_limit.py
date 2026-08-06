"""
In-process sliding-window rate limiter for embed session and chat endpoints.

Suitable for single-machine deploys. For multi-instance production, swap the
shared ``ip_limiter`` / ``site_limiter`` implementations for Redis.

Author: Sanju
Date: 2026-08-06
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict


class SlidingWindowRateLimiter:
    """
    Purpose:
        Thread-safe per-key request counter over a rolling time window.

    Typical keys:
        ``ip:203.0.113.10``, ``site:aicv_…``, ``session-ip:…``
    """

    def __init__(self, window_seconds: int = 60):
        """
        Purpose:
            Configure the rolling window length.

        Receives:
            window_seconds (int): Window size in seconds (default 60).

        Returns:
            None.
        """
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int) -> bool:
        """
        Purpose:
            Record one hit and decide if the request is within quota.

        Receives:
            key (str): Bucket identifier (IP or site).
            limit (int): Max hits allowed in the window; ``<= 0`` always allows.

        Returns:
            bool: True if allowed (and counted); False if over limit.
        """
        if limit <= 0:
            return True
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def remaining(self, key: str, limit: int) -> int:
        """
        Purpose:
            Report how many hits are still available in the current window.

        Receives:
            key (str): Bucket identifier.
            limit (int): Configured max hits.

        Returns:
            int: Non-negative remaining quota (does not record a hit).
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            return max(0, limit - len(q))


# Shared process-wide limiters (60s window)
ip_limiter = SlidingWindowRateLimiter(60)
site_limiter = SlidingWindowRateLimiter(60)
