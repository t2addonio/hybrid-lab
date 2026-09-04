"""Hybrid model routing layer (Ollama + optional Grok API)."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from openai import OpenAI, APIError, APIConnectionError, AuthenticationError, RateLimitError

logger = logging.getLogger("multi_agent.llm")
_CONFIG: Optional[Dict[str, Any]] = None


def load_config(path: Optional[str | Path] = None) -> Dict[str, Any]:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    if path is None:
        path = Path(__file__).resolve().parent.parent / "config.yaml"
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg.get("backends", {}).get("ollama", {}).get("enabled", False):
        raise RuntimeError("backends.ollama.enabled must be true (local-first invariant)")
    _CONFIG = cfg
    return cfg


def get_config() -> Dict[str, Any]:
    if _CONFIG is None:
        return load_config()
    return _CONFIG


def resolve_routing(role: str) -> Dict[str, Any]:
    cfg = get_config()
    routing = cfg.get("routing", {})
    backends = cfg.get("backends", {})
    roles = routing.get("roles", {})
    role_cfg = roles.get(role, {})
    preferred = role_cfg.get("preferred_backend", routing.get("default_backend", "ollama"))
    model = role_cfg.get("model") or routing.get("default_model")
    fallback_backend = role_cfg.get("fallback_backend")
    fallback_model = role_cfg.get("fallback_model")
    if preferred == "grok":
        if not _grok_is_usable(backends.get("grok", {})):
            logger.info("Grok preferred for role=%s but not available → forcing ollama", role)
            preferred = "ollama"
            model = fallback_model or backends["ollama"].get("default_model")
            fallback_backend = None
            fallback_model = None
    backend_cfg = backends[preferred]
    if model is None:
        model = backend_cfg.get("default_model")
    return {
        "backend": preferred,
        "model": model,
        "fallback_backend": fallback_backend,
        "fallback_model": fallback_model,
        "base_url": backend_cfg["base_url"],
        "api_key": _resolve_api_key(preferred, backend_cfg),
        "timeout_s": backend_cfg.get("timeout_s", 120),
    }


def _grok_is_usable(grok_cfg: Dict[str, Any]) -> bool:
    if not grok_cfg.get("enabled", False):
        return False
    key = os.environ.get(grok_cfg.get("api_key_env", "XAI_API_KEY"), "").strip()
    return bool(key)


def _resolve_api_key(backend: str, backend_cfg: Dict[str, Any]) -> str:
    if backend == "grok":
        env_name = backend_cfg.get("api_key_env", "XAI_API_KEY")
        key = os.environ.get(env_name, "").strip()
        if not key:
            raise RuntimeError(f"Grok selected but ${env_name} is empty")
        return key
    return backend_cfg.get("api_key", "ollama")


def _make_client(base_url: str, api_key: str, timeout_s: int) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=api_key, timeout=timeout_s)


def _call_backend(messages, model, base_url, api_key, timeout_s, temperature=0.2, max_tokens=None) -> str:
    client = _make_client(base_url, api_key, timeout_s)
    kwargs: Dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def chat(messages: List[Dict[str, str]], role: str = "coordinator", temperature: float = 0.2, max_tokens: Optional[int] = None, **kwargs: Any) -> str:
    resolved = resolve_routing(role)
    backend = resolved["backend"]
    model = resolved["model"]
    logger.debug("chat role=%s → %s / %s", role, backend, model)
    try:
        return _call_backend(messages, model, resolved["base_url"], resolved["api_key"], resolved["timeout_s"], temperature, max_tokens)
    except (APIConnectionError, AuthenticationError, RateLimitError, APIError, TimeoutError, OSError) as e:
        fb = resolved.get("fallback_backend")
        fb_model = resolved.get("fallback_model")
        if not fb:
            logger.error("No fallback for role=%s; original error: %s", role, e)
            raise
        logger.warning("Fallback triggered for role=%s: %s → %s", role, backend, fb)
        cfg = get_config()
        fb_cfg = cfg["backends"][fb]
        return _call_backend(
            messages,
            fb_model or fb_cfg.get("default_model"),
            fb_cfg["base_url"],
            _resolve_api_key(fb, fb_cfg),
            fb_cfg.get("timeout_s", 120),
            temperature,
            max_tokens,
        )
