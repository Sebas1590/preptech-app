"""Validación de entrada, heurística anti prompt-injection y límite de uso."""
from __future__ import annotations

import re
import time

MAX_CHARS = 2000

_INJECTION = re.compile(
    r"(ignora|ignore|olvida|forget|disregard)\W+(todas?\W+)?(las\W+|tus\W+|your\W+|all\W+|the\W+|previous\W+|prior\W+)*"
    r"(instrucciones|reglas|instructions|rules|prompt)"
    r"|(revela|muestra|imprime|reveal|show|print|repeat)\W+(tu|el|your|the)?\W*(prompt|system prompt|instrucciones internas)"
    r"|(act[uú]a|actúa|compórtate|pretend|act)\W+(como|as|like)\W+(dan|un\W+modelo\W+sin|an?\W+unrestricted)"
    r"|modo\W+(desarrollador|dios|developer)|jailbreak",
    re.IGNORECASE,
)


class InputError(ValueError):
    """Error de validación con mensaje apto para mostrar al usuario."""


def validate_input(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise InputError("Escribe un mensaje antes de enviar.")
    if len(text) > MAX_CHARS:
        raise InputError(f"El mensaje es muy largo ({len(text)} caracteres). Máximo {MAX_CHARS}.")
    return text.replace("\x00", "")


def looks_like_injection(text: str) -> bool:
    return bool(_INJECTION.search(text))


def wrap_user_text(text: str) -> str:
    """Neutraliza delimitadores falsos para que el usuario no cierre la etiqueta de datos."""
    return text.replace("<entrada_usuario>", "").replace("</entrada_usuario>", "")


class RateLimiter:
    """Ventana deslizante: máximo `max_calls` por `window` segundos (por sesión)."""

    def __init__(self, max_calls: int = 40, window: int = 3600):
        self.max_calls, self.window, self.calls = max_calls, window, []

    def check(self) -> None:
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.window]
        if len(self.calls) >= self.max_calls:
            espera = int(self.window - (now - self.calls[0])) // 60 + 1
            raise InputError(f"Alcanzaste el límite de {self.max_calls} solicitudes por hora. Intenta en ~{espera} min.")
        self.calls.append(now)
