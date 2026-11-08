"""
Thin LLM wrapper: Anthropic, OpenAI or Gemini, chosen by LLM_PROVIDER.
With no key set (or on any error / timeout) it returns None and callers use template answers,
so the demo never breaks.
"""
from __future__ import annotations

import os
import time
from contextvars import ContextVar
from typing import Optional

import httpx

TIMEOUT = 15.0
DEFAULT_MODELS = {  # override with ANTHROPIC_MODEL / OPENAI_MODEL / GEMINI_MODEL
    "anthropic": "claude-haiku-5-5",
    "openai": "gpt-4o-mini",          # OpenAI lists a 14 Jan 2027 shutdown — set OPENAI_MODEL to a newer model then
    "gemini": "gemini-3.6-flash",     # gemini-2.0-flash was retired on 1 Jun 2026
}
# Set per request from the X-HemoLink-Lang header, so AI answers match the EN / BM toggle.
reply_lang: ContextVar[str] = ContextVar("reply_lang", default="en")
MALAY_NOTE = ("\n\nLANGUAGE: The user is reading the app in Bahasa Melayu. Write your whole reply in natural Malaysian "
              "Malay (Bahasa Melayu). Keep lab test names, units and numbers exactly as given (e.g. Hb, MCV, g/dL). "
              "Translate any required closing sentence too, keeping its meaning.")
GEMINI_THINKING_ROOM = 1024  # extra output budget so Gemini's hidden "thinking" doesn't use up the whole reply


class EmptyReply(Exception):
    """The provider answered (HTTP 200) but sent no text."""


def _gemini_text(data: dict) -> str:
    cands = data.get("candidates") or []
    if not cands:
        reason = (data.get("promptFeedback") or {}).get("blockReason") or "no candidates"
        raise EmptyReply(f"blocked ({reason})")
    parts = (cands[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if not text.strip():
        raise EmptyReply(f"empty reply (finishReason {cands[0].get('finishReason', '?')})")
    return text


_last_error: dict = {"error": None, "at": None}


def provider() -> str:
    return (os.getenv("LLM_PROVIDER") or "anthropic").lower()


def model() -> str:
    p = provider()
    return os.getenv(f"{p.upper()}_MODEL") or DEFAULT_MODELS.get(p, DEFAULT_MODELS["anthropic"])


def status() -> dict:
    """Safe to show admins: never includes the key."""
    return {"provider": provider(), "model": model(), "configured": configured(),
            "last_error": _last_error["error"], "last_error_at": _last_error["at"]}


def _remember(exc: Exception) -> None:
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        hint = {401: "invalid API key", 403: "key not allowed for this model", 404: "model name not found",
                429: "rate limit or no credit left"}.get(code, "provider error")
        msg = f"HTTP {code} — {hint}"
    elif isinstance(exc, EmptyReply):
        msg = f"provider sent no text — {exc}"
    elif isinstance(exc, httpx.TimeoutException):
        msg = "timed out"
    else:
        msg = type(exc).__name__
    _last_error.update(error=msg, at=time.strftime("%Y-%m-%d %H:%M"))


def configured() -> bool:
    p = provider()
    if p == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if p == "gemini":
        return bool(os.getenv("GEMINI_API_KEY"))
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def complete(system: str, messages: list[dict], max_tokens: int = 400) -> Optional[str]:
    if not configured():
        return None
    p = provider()
    if reply_lang.get() == "ms":
        system = system + MALAY_NOTE
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            if p == "openai":
                r = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                    json={
                        "model": model(),
                        "max_tokens": max_tokens,
                        "messages": [{"role": "system", "content": system}, *messages],
                    },
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
            if p == "gemini":
                m = model()
                config = {"maxOutputTokens": max_tokens + GEMINI_THINKING_ROOM}  # thinking counts toward this limit
                if not m.startswith(("gemini-1", "gemini-2")):
                    config["thinkingConfig"] = {"thinkingLevel": "low"}  # Gemini 3+: keep thinking short (faster, cheaper)
                r = client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                    params={"key": os.environ["GEMINI_API_KEY"]},
                    json={
                        "systemInstruction": {"parts": [{"text": system}]},
                        "contents": [
                            {"role": "model" if msg["role"] == "assistant" else "user", "parts": [{"text": msg["content"]}]}
                            for msg in messages
                        ],
                        "generationConfig": config,
                    },
                )
                r.raise_for_status()
                return _gemini_text(r.json())
            r = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                json={
                    "model": model(),
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": messages,
                },
            )
            r.raise_for_status()
            return "".join(c.get("text", "") for c in r.json()["content"])
    except Exception as exc:  # network error, bad key, timeout, unexpected shape → callers fall back to templates
        _remember(exc)
        return None


def test() -> dict:
    """One tiny request to check the key and model work (used by the admin 'Test AI connection' button)."""
    if not configured():
        return {"ok": False, **status(), "message": f"No API key set for {provider()}. Add it to the .env file and restart."}
    t = time.time()
    before = _last_error["error"]
    _last_error["error"] = None
    text = complete("Reply with exactly: OK", [{"role": "user", "content": "Connection test"}], 20)
    ms = round((time.time() - t) * 1000)
    if text:
        return {"ok": True, **status(), "latency_ms": ms, "message": f"Connected · replied in {ms} ms"}
    err = _last_error["error"] or before or "no reply"
    return {"ok": False, **status(), "latency_ms": ms, "message": f"Failed: {err}"}
