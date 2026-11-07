import os
import threading
import time
from collections import defaultdict, deque

WINDOW_SECONDS = 3600
_hits: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()

def limit_per_hour() -> int:
    try:
        return int(os.getenv("GENERATE_LIMIT_PER_HOUR", "10"))
    except ValueError:
        return 10

def hit(key: str) -> int:
    limit = limit_per_hour()
    if limit <= 0:
        return 0
    now = time.monotonic()
    with _lock:
        queue = _hits[key]
        while queue and now - queue[0] > WINDOW_SECONDS:
            queue.popleft()
        if len(queue) >= limit:
            return max(1, int(WINDOW_SECONDS - (now - queue[0])))
        queue.append(now)
        return 0

def reset() -> None:
    with _lock:
        _hits.clear()
