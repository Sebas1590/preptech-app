"""API de PrepTech (FastAPI). Unifica el backend Python con el frontend React.

Ejecutar:  uvicorn server:app --reload --port 8000
Reutiliza `services/` y `prompts/` del Coach tal cual; Streamlit sigue disponible como panel interno.

Seguridad:
- La API Key de OpenAI se guarda SOLO en memoria del proceso (nunca en disco ni en la respuesta).
- El `user_id` lo fija el servidor; el cliente no puede elegirlo.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).parent / ".env", override=True)

from iot import lessons as iot_lessons  # noqa: E402
from iot.interpreter import BOARDS, simulate  # noqa: E402
from prompts import FEW_SHOT_EXAMPLES, ONE_SHOT_EXAMPLE, SYSTEM_PROMPT, TECHNIQUES, ZERO_SHOT_PROMPT  # noqa: E402
from services.guardrails import InputError, RateLimiter, validate_input  # noqa: E402
from services.llm_service import LLMError, LLMService, _translate, get_model, render_star  # noqa: E402
from services.tools import _banco  # noqa: E402

app = FastAPI(title="PrepTech API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_methods=["*"], allow_headers=["*"],
)

AREAS = {"algoritmos", "sistemas", "comportamiento", "iot"}
DEFAULT_USER = "usuario-demo"


# ------------------------------------------------------------ estado de IA
class KeyStore:
    """Clave en memoria. Prioriza la configurada desde la UI; si no hay, usa OPENAI_API_KEY del entorno."""

    def __init__(self):
        self.lock = threading.Lock()
        self.ui_key: str | None = None
        self.model: str | None = None
        self.connected_at: str | None = None
        self.verified = False

    def key(self) -> str | None:
        env = os.getenv("OPENAI_API_KEY", "").strip()
        return self.ui_key or (env if env and env != "your_api_key_here" else None)

    def source(self) -> str | None:
        if self.ui_key:
            return "interfaz"
        return "entorno" if self.key() else None


store = KeyStore()
limiters: dict[str, RateLimiter] = {}


def limiter_for(request: Request) -> RateLimiter:
    ip = request.client.host if request.client else "local"
    return limiters.setdefault(ip, RateLimiter(int(os.getenv("MAX_REQUESTS_PER_HOUR", "40"))))


def mask(key: str | None) -> str | None:
    return None if not key else f"{key[:3]}…{key[-4:]}" if len(key) > 10 else "••••"


def status_payload() -> dict:
    k = store.key()
    return {"configured": bool(k), "connected": bool(k) and store.verified, "source": store.source(),
            "key_hint": mask(k), "model": store.model or get_model(), "connected_at": store.connected_at}


def service() -> LLMService:
    k = store.key()
    if not k:
        raise HTTPException(409, "La IA no está conectada. Ve a «Configuración de IA» y conecta tu API Key.")
    client = OpenAI(api_key=k, timeout=float(os.getenv("OPENAI_TIMEOUT", "30")), max_retries=2)
    return LLMService(client=client, model=store.model or get_model())


def guard(request: Request, fn):
    """Traduce errores del dominio a respuestas HTTP con mensaje legible (nunca trazas)."""
    try:
        return fn()
    except InputError as e:
        raise HTTPException(422, str(e)) from e
    except LLMError as e:
        raise HTTPException(502, str(e)) from e


class ConnectBody(BaseModel):
    api_key: str = Field(min_length=8, max_length=300)
    model: str | None = Field(default=None, max_length=60)


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/ai/status")
def ai_status():
    return status_payload()


@app.post("/api/ai/connect")
def ai_connect(body: ConnectBody):
    """Valida la clave contra OpenAI y, si es válida, la deja activa en memoria."""
    key = body.api_key.strip()
    try:
        OpenAI(api_key=key, timeout=15, max_retries=0).models.list()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(401 if "Authentication" in type(e).__name__ else 502, str(_translate(e))) from e
    with store.lock:
        store.ui_key, store.verified = key, True
        store.model = (body.model or "").strip() or None
        store.connected_at = datetime.now(timezone.utc).isoformat()
    return status_payload()


@app.post("/api/ai/test")
def ai_test():
    """Reintenta la conexión con la clave ya configurada (UI o entorno)."""
    k = store.key()
    if not k:
        raise HTTPException(409, "No hay API Key configurada.")
    try:
        OpenAI(api_key=k, timeout=15, max_retries=0).models.list()
    except Exception as e:  # noqa: BLE001
        store.verified = False
        raise HTTPException(401 if "Authentication" in type(e).__name__ else 502, str(_translate(e))) from e
    store.verified = True
    store.connected_at = datetime.now(timezone.utc).isoformat()
    return status_payload()


@app.delete("/api/ai/connect")
def ai_disconnect():
    with store.lock:
        store.ui_key, store.verified, store.connected_at, store.model = None, False, None, None
    return status_payload()


# ------------------------------------------------------------------- coach
class Msg(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class Perfil(BaseModel):
    nombre: str = "Postulante"
    empresaObjetivo: str = "Google"
    fechaEntrevista: str | None = None
    metaSemanal: int = 15


class ChatBody(BaseModel):
    message: str
    area: str = "algoritmos"
    history: list[Msg] = []
    perfil: Perfil = Perfil()
    progreso: dict | None = None  # export de localStorage del frontend ({intentos: [...]})


@app.post("/api/coach/chat")
def coach_chat(body: ChatBody, request: Request):
    if body.area not in AREAS:
        raise HTTPException(422, f"Área inválida. Usa una de {sorted(AREAS)}.")

    def run():
        text = validate_input(body.message)
        limiter_for(request).check()
        p = body.perfil
        ctx = {"user_id": DEFAULT_USER, "empresa": p.empresaObjetivo, "fecha_entrevista": p.fechaEntrevista,
               "meta_semanal": p.metaSemanal,
               "progreso_real": body.progreso if isinstance((body.progreso or {}).get("intentos"), list) else None}
        r = service().chat([m.model_dump() for m in body.history], text, body.area,
                           {"nombre": p.nombre, "empresa": p.empresaObjetivo}, ctx)
        return {"text": r.text, "injection_flag": r.injection_flag,
                "tools": [{"name": t["name"], "args": t["args"], "source": t["result"].get("source")} for t in r.tools_used],
                "usage": {"prompt": r.usage.prompt, "completion": r.usage.completion, "total": r.usage.total}}
    return guard(request, run)


class StarBody(BaseModel):
    technique: str = "Few-shot"
    pregunta: str = Field(max_length=500)
    respuesta: str


@app.post("/api/coach/star")
def coach_star(body: StarBody, request: Request):
    def run():
        texto = validate_input(body.respuesta)
        limiter_for(request).check()
        d, u, _ = service().analyze_star(body.technique, body.pregunta, texto)
        return {"analysis": d, "markdown": render_star(d),
                "usage": {"prompt": u.prompt, "completion": u.completion, "total": u.total}}
    return guard(request, run)


@app.get("/api/coach/library")
def coach_library():
    """Biblioteca de prompts (solo lectura) y técnicas disponibles."""
    return {"techniques": list(TECHNIQUES), "system_prompt": SYSTEM_PROMPT, "zero_shot": ZERO_SHOT_PROMPT,
            "one_shot": ONE_SHOT_EXAMPLE, "few_shot": FEW_SHOT_EXAMPLES}


@app.get("/api/coach/behavioral-questions")
def behavioral_questions():
    return [{"id": q["id"], "pregunta": q["pregunta"], "empresa": q["empresa"]} for q in _banco()["conductuales"]]


# --------------------------------------------------------------------- IoT
class SimBody(BaseModel):
    code: str = Field(max_length=8000)
    board: str = "esp32"
    lesson_id: str | None = None
    inputs: dict[str, float | int | list[list[float]]] = {}
    duration_ms: int = 5000


def _res_payload(res) -> dict:
    return {"ok": res.ok, "error": res.error, "error_line": res.error_line, "events": res.events,
            "serial": res.serial, "warnings": res.warnings, "pin_modes": res.pin_modes,
            "duration_ms": res.duration_ms, "loops": res.loops}


@app.get("/api/iot/boards")
def iot_boards():
    return [{"id": k, "nombre": v["nombre"], "adc_max": v["adc_max"], "led_builtin": v["led_builtin"]}
            for k, v in BOARDS.items()]


@app.get("/api/iot/lessons")
def iot_lessons_list():
    return [iot_lessons.public(l) for l in iot_lessons.LESSONS]


@app.post("/api/iot/simulate")
def iot_simulate(body: SimBody):
    if body.board not in BOARDS:
        raise HTTPException(422, "Placa no soportada.")
    if body.lesson_id and body.lesson_id not in iot_lessons.BY_ID:
        raise HTTPException(404, "Lección no encontrada.")
    run = simulate(body.code, body.board, body.inputs, body.duration_ms)
    out = _res_payload(run)
    if body.lesson_id:
        scen = simulate(body.code, body.board, iot_lessons.BY_ID[body.lesson_id]["scenario"], 5000)
        checks = iot_lessons.evaluate(body.lesson_id, scen) if scen.ok else []
        out["checks"] = checks
        out["passed"] = bool(checks) and all(c["ok"] for c in checks)
    return out


class HintBody(BaseModel):
    lesson_id: str
    code: str = Field(max_length=8000)
    result_summary: str = Field(default="", max_length=1500)
    question: str = Field(default="Dame una pista.", max_length=500)


@app.post("/api/iot/hint")
def iot_hint(body: HintBody, request: Request):
    lesson = iot_lessons.BY_ID.get(body.lesson_id)
    if not lesson:
        raise HTTPException(404, "Lección no encontrada.")

    def run():
        validate_input(body.question)
        limiter_for(request).check()
        msg = (f"Lección: {lesson['titulo']}. Objetivo: {lesson['objetivo']}\n<entrada_usuario>\n"
               f"Pregunta del estudiante: {body.question}\n"
               f"Resultado del simulador: {body.result_summary or 'sin ejecutar'}\n"
               f"Código:\n{body.code}\n</entrada_usuario>")
        r = service().chat([], msg, "iot", {"nombre": "Estudiante", "empresa": "-"},
                           {"user_id": DEFAULT_USER, "progreso_real": None})
        return {"text": r.text, "usage": {"total": r.usage.total}}
    return guard(request, run)
