"""Servicio LLM: chat con function calling y análisis STAR con zero/one/few-shot."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import openai
from openai import OpenAI

from prompts import TECHNIQUES, build_system_prompt
from prompts.review import build_review_messages
from prompts.feedback import STAR_KEYS
from services.guardrails import looks_like_injection, wrap_user_text
from services.tools import TOOLS_SCHEMA, execute_tool

DEFAULT_MODEL = "gpt-4.1-mini"
HISTORY_LIMIT = 12  # mensajes previos enviados al modelo (ahorro de tokens)
MAX_TOOL_ROUNDS = 4


class LLMError(Exception):
    """Error con mensaje comprensible para el usuario final."""


@dataclass
class Usage:
    prompt: int = 0
    completion: int = 0

    @property
    def total(self) -> int:
        return self.prompt + self.completion

    def add(self, u) -> None:
        if u is not None:
            self.prompt += u.prompt_tokens or 0
            self.completion += u.completion_tokens or 0


@dataclass
class ChatResult:
    text: str
    usage: Usage
    tools_used: list[dict] = field(default_factory=list)
    injection_flag: bool = False


def get_model() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def make_client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key == "your_api_key_here":
        raise LLMError("Falta la API Key. Define OPENAI_API_KEY en tu archivo .env (ver .env.example) y reinicia la app.")
    return OpenAI(api_key=key, timeout=float(os.getenv("OPENAI_TIMEOUT", "30")), max_retries=2)


def _translate(e: Exception) -> LLMError:
    if isinstance(e, openai.AuthenticationError):
        return LLMError("La API Key fue rechazada por OpenAI. Verifica OPENAI_API_KEY.")
    if isinstance(e, openai.RateLimitError):
        return LLMError("OpenAI rechazó la solicitud por límite de uso o saldo. Espera un momento o revisa tu cuenta.")
    if isinstance(e, openai.APITimeoutError):
        return LLMError("OpenAI tardó demasiado en responder (timeout). Intenta de nuevo.")
    if isinstance(e, openai.APIConnectionError):
        return LLMError("No se pudo conectar con OpenAI. Revisa tu conexión a internet.")
    if isinstance(e, openai.NotFoundError):
        return LLMError(f"El modelo '{get_model()}' no existe o no está disponible. Cambia OPENAI_MODEL.")
    if isinstance(e, openai.APIStatusError):
        return LLMError(f"OpenAI devolvió un error ({e.status_code}). Intenta de nuevo en un momento.")
    return LLMError("Ocurrió un error inesperado al consultar el modelo.")


class LLMService:
    def __init__(self, client: OpenAI | None = None, model: str | None = None):
        self.client = client or make_client()
        self.model = model or get_model()

    # ---------- Chat con herramientas ----------
    def chat(self, history: list[dict], user_text: str, area: str, perfil: dict, ctx: dict) -> ChatResult:
        flag = looks_like_injection(user_text)
        messages = [{"role": "system", "content": build_system_prompt(area, perfil, flag)}]
        messages += history[-HISTORY_LIMIT:]
        messages.append({"role": "user", "content": wrap_user_text(user_text)})
        usage, used = Usage(), []
        try:
            for _ in range(MAX_TOOL_ROUNDS):
                r = self.client.chat.completions.create(
                    model=self.model, messages=messages, tools=TOOLS_SCHEMA,
                    temperature=0.4, max_completion_tokens=700)
                usage.add(r.usage)
                msg = r.choices[0].message
                if not msg.tool_calls:
                    if not (msg.content or "").strip():
                        raise LLMError("El modelo devolvió una respuesta vacía. Intenta reformular.")
                    return ChatResult(msg.content.strip(), usage, used, flag)
                messages.append(msg.model_dump(exclude_none=True))
                for tc in msg.tool_calls:
                    out = execute_tool(tc.function.name, tc.function.arguments, ctx)
                    used.append({"name": tc.function.name, "args": tc.function.arguments, "result": out})
                    messages.append({"role": "tool", "tool_call_id": tc.id,
                                     "content": json.dumps(out, ensure_ascii=False)})
            raise LLMError("El asistente no logró terminar la consulta. Intenta de nuevo con un pedido más simple.")
        except LLMError:
            raise
        except Exception as e:  # noqa: BLE001
            raise _translate(e) from e

    # ---------- Análisis STAR (zero / one / few-shot) ----------
    def analyze_star(self, technique: str, pregunta: str, respuesta: str) -> tuple[dict, Usage, list[dict]]:
        if technique not in TECHNIQUES:
            raise LLMError(f"Técnica desconocida: {technique}")
        messages = TECHNIQUES[technique](pregunta, wrap_user_text(respuesta))
        usage = Usage()
        try:
            r = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.2,
                max_completion_tokens=600, response_format={"type": "json_object"})
        except Exception as e:  # noqa: BLE001
            raise _translate(e) from e
        usage.add(r.usage)
        return parse_star(r.choices[0].message.content), usage, messages

    # ---------- Revisión de una solución técnica ----------
    def review_solution(self, titulo: str, enunciado: str, area: str, solucion: str, notas: str) -> tuple[dict, Usage]:
        messages = build_review_messages(titulo, wrap_user_text(enunciado), area,
                                         wrap_user_text(solucion), wrap_user_text(notas))
        usage = Usage()
        try:
            r = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.2,
                max_completion_tokens=600, response_format={"type": "json_object"})
        except Exception as e:  # noqa: BLE001
            raise _translate(e) from e
        usage.add(r.usage)
        return parse_review(r.choices[0].message.content), usage


def parse_review(raw: str | None) -> dict:
    try:
        d = json.loads(raw or "")
        correct = d.get("correctness")
        return {
            "score": max(1, min(5, int(d["score"]))),
            "correctness": correct if correct in ("correcto", "parcial", "incorrecto", "sin_intento") else "parcial",
            "strength": str(d["strength"]),
            "improvements": [str(x) for x in d.get("improvements", [])][:2],
            "complexity": str(d.get("complexity", "")),
            "next_step": str(d["next_step"]),
        }
    except (ValueError, KeyError, TypeError) as e:
        raise LLMError("El modelo devolvió una respuesta con formato inválido. Intenta de nuevo.") from e


def parse_star(raw: str | None) -> dict:
    """Valida el JSON del modelo; lanza LLMError si no cumple el esquema."""
    try:
        d = json.loads(raw or "")
        out = {}
        for k in STAR_KEYS:
            out[k] = {"present": bool(d[k]["present"]), "evidence": str(d[k].get("evidence", ""))[:300]}
        out["score"] = max(1, min(5, int(d["score"])))
        out["strength"] = str(d["strength"])
        out["improvements"] = [str(x) for x in d.get("improvements", [])][:2]
        out["next_step"] = str(d["next_step"])
        return out
    except (ValueError, KeyError, TypeError) as e:
        raise LLMError("El modelo devolvió una respuesta con formato inválido. Intenta de nuevo.") from e


NOMBRES_STAR = {"situation": "Situación", "task": "Tarea", "action": "Acción", "result": "Resultado"}


def render_star(d: dict) -> str:
    lines = []
    for k in STAR_KEYS:
        icon = "✅" if d[k]["present"] else "❌"
        ev = f" — _{d[k]['evidence']}_" if d[k]["evidence"] else ""
        lines.append(f"- {icon} **{NOMBRES_STAR[k]}**{ev}")
    mejoras = "\n".join(f"  {i}. {m}" for i, m in enumerate(d["improvements"], 1)) or "  (ninguna)"
    return (f"**Nota: {d['score']}/5** (orientativa, no predice una contratación)\n\n" + "\n".join(lines) +
            f"\n\n👍 **Acierto:** {d['strength']}\n\n🔧 **Mejoras:**\n{mejoras}\n\n➡️ **Siguiente paso:** {d['next_step']}")
