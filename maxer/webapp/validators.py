from __future__ import annotations

import hashlib
import hmac
import json
import urllib.parse as _ulib
from typing import Any, Dict

from ..core.exceptions import MaxerException

__all__ = ["validate_init_data"]


def _parse_init_data(raw: str) -> Dict[str, str]:
    decoded = _ulib.unquote_plus(raw)
    pairs = decoded.split("&")
    result: dict[str, str] = {}
    for pair in pairs:
        if not pair:
            continue
        if "=" not in pair:
            key, value = pair, ""
        else:
            key, value = pair.split("=", 1)
        result.setdefault(key, value)
    return result


def validate_init_data(init_data: str, bot_token: str) -> Dict[str, Any]:
    params = _parse_init_data(init_data)

    recv_hash = params.pop("hash", None)
    if recv_hash is None:
        raise MaxerException("init_data does not contain 'hash' parameter")

    data_check_string = "\n".join(f"{k}={params[k]}" for k in sorted(params))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calc_hash != recv_hash:
        raise MaxerException("init_data hash validation failed")

    if "user" in params:
        try:
            params["user"] = json.loads(params["user"])
        except json.JSONDecodeError:
            pass

    return params 