from __future__ import annotations

import random


async def expo(attempt: int, base: float = 0.5, cap: float = 5.0) -> float:
    exp = min(cap, base * 2 ** attempt)
    return random.uniform(0, exp) 