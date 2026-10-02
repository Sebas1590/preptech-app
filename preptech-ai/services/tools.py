"""Herramientas (function calling) del Coach, según la Entrega 2.

Seguridad: el modelo NUNCA ve ni controla `user_id`; lo inyecta el backend
desde la sesión (mitiga acceso a datos de otros usuarios).

Datos:
- Banco de preguntas: REAL (data/banco.json, exportado de preptech-frontend/src/lib/preptech-data.ts).
- Progreso: REAL solo si el usuario sube su export de localStorage; si no, DEMO
  (data/demo_progress.json) y la salida lo marca con "source": "demo".
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
FEEDBACK_LOG = DATA / "feedback_log.jsonl"

AREA_MAP = {"algorithms": "algoritmos", "system_design": "sistemas", "behavioral": "comportamiento"}
DIFF_MAP = {"easy": "facil", "medium": "medio", "hard": "dificil"}

TOOLS_SCHEMA = [
    {"type": "function", "function": {
        "name": "get_practice_questions",
        "description": "Obtiene preguntas del banco de PrepTech filtradas por área, empresa y dificultad. Úsala cuando el usuario quiera practicar o pida una recomendación.",
        "parameters": {"type": "object", "properties": {
            "area": {"type": "string", "enum": list(AREA_MAP)},
            "company": {"type": "string", "description": "Empresa objetivo, ej. 'Google'"},
            "difficulty": {"type": "string", "enum": list(DIFF_MAP)},
            "limit": {"type": "integer", "description": "Cantidad (1-5)"},
        }, "required": ["area"]}}},
    {"type": "function", "function": {
        "name": "get_user_progress",
        "description": "Devuelve el progreso del usuario: intentos, tiempo promedio y áreas débiles. Úsala antes de recomendar o resumir avance.",
        "parameters": {"type": "object", "properties": {
            "period_days": {"type": "integer", "description": "Ventana de días (por defecto 30)"},
        }}}},
    {"type": "function", "function": {
        "name": "save_session_feedback",
        "description": "Guarda la retroalimentación de una sesión de práctica (pregunta, tiempo, nota 1-5, componentes STAR faltantes).",
        "parameters": {"type": "object", "properties": {
            "question_id": {"type": "string"},
            "score": {"type": "integer", "description": "Nota de 1 a 5"},
            "time_seconds": {"type": "integer"},
            "missing_star": {"type": "array", "items": {"type": "string", "enum": ["situation", "task", "action", "result"]}},
            "notes": {"type": "string", "description": "Comentario breve"},
        }, "required": ["question_id", "score"]}}},
    {"type": "function", "function": {
        "name": "get_interview_countdown",
        "description": "Calcula los días restantes a la entrevista y el ritmo de práctica necesario según la fecha registrada por el usuario.",
        "parameters": {"type": "object", "properties": {}}}},
]


def _banco() -> dict:
    return json.loads((DATA / "banco.json").read_text(encoding="utf-8"))


def get_practice_questions(ctx: dict, area: str, company: str | None = None,
                           difficulty: str | None = None, limit: int = 3) -> dict:
    if area not in AREA_MAP:
        return {"error": f"area inválida; usa una de {list(AREA_MAP)}"}
    limit = max(1, min(int(limit or 3), 5))
    banco = _banco()
    if area == "behavioral":
        pool = banco["conductuales"]
        if company:
            pool = [q for q in pool if q["empresa"].lower() == company.lower()] or pool
        items = [{"id": q["id"], "pregunta": q["pregunta"], "empresa": q["empresa"],
                  "competencia": q["competencia"]} for q in pool[:limit]]
    else:
        pool = [q for q in banco["preguntas"] if q["area"] == AREA_MAP[area]]
        if difficulty:
            pool = [q for q in pool if q["dificultad"] == DIFF_MAP.get(difficulty)]
        exact = [q for q in pool if company and q["empresa"].lower() == company.lower()]
        pool = exact or pool
        items = [{"id": q["id"], "titulo": q["titulo"], "empresa": q["empresa"],
                  "dificultad": q["dificultad"], "minutos_objetivo": q["minutosObjetivo"],
                  "enunciado": q["enunciado"], "pistas": q["pistas"]} for q in pool[:limit]]
    note = None if company is None or (items and any(i["empresa"].lower() == company.lower() for i in items)) \
        else f"No hay preguntas de {company} con esos filtros; se muestran otras del banco."
    return {"source": "banco_real", "count": len(items), "questions": items, "note": note}


def _intentos(ctx: dict) -> tuple[list[dict], str]:
    """(intentos, fuente) — fuente 'real' si el usuario subió su export, si no 'demo'."""
    real = ctx.get("progreso_real")
    if real is not None:
        return real.get("intentos", []), "real"
    raw = json.loads((DATA / "demo_progress.json").read_text(encoding="utf-8"))
    ahora = datetime.now(timezone.utc)
    return [{**i, "fecha": (ahora - timedelta(days=i["dias_atras"])).isoformat()} for i in raw], "demo"


def get_user_progress(ctx: dict, period_days: int = 30) -> dict:
    intentos, source = _intentos(ctx)
    limite = datetime.now(timezone.utc) - timedelta(days=max(1, int(period_days or 30)))
    sel = [i for i in intentos if datetime.fromisoformat(i["fecha"].replace("Z", "+00:00")) >= limite]
    por_area: dict[str, list[dict]] = {}
    for i in sel:
        por_area.setdefault(i["area"], []).append(i)
    areas = [{"area": a, "intentos": len(v),
              "tasa_resueltos": round(sum(x["resultado"] == "resuelto" for x in v) / len(v), 2)}
             for a, v in por_area.items()]
    areas.sort(key=lambda x: x["tasa_resueltos"])
    return {
        "source": source,
        "aviso": "DATOS DE DEMOSTRACIÓN, no son del usuario real." if source == "demo" else None,
        "period_days": period_days,
        "total_intentos": len(sel),
        "resueltos": sum(i["resultado"] == "resuelto" for i in sel),
        "tiempo_promedio_seg": round(sum(i["segundos"] for i in sel) / len(sel)) if sel else 0,
        "areas_debiles": areas,
    }


def save_session_feedback(ctx: dict, question_id: str, score: int, time_seconds: int | None = None,
                          missing_star: list[str] | None = None, notes: str | None = None) -> dict:
    score = int(score)
    if not 1 <= score <= 5:
        return {"error": "score debe estar entre 1 y 5"}
    registro = {"fecha": datetime.now(timezone.utc).isoformat(), "user_id": ctx["user_id"],
                "question_id": str(question_id)[:80], "score": score, "time_seconds": time_seconds,
                "missing_star": missing_star or [], "notes": (notes or "")[:300]}
    DATA.mkdir(exist_ok=True)
    with FEEDBACK_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return {"saved": True, "registro": registro}


def get_interview_countdown(ctx: dict) -> dict:
    fecha = ctx.get("fecha_entrevista")
    if not fecha:
        return {"error": "El usuario no ha registrado una fecha de entrevista."}
    dias = (date.fromisoformat(str(fecha)) - date.today()).days
    if dias < 0:
        return {"error": "La fecha registrada ya pasó."}
    return {"dias_restantes": dias, "empresa": ctx.get("empresa"),
            "ritmo_sugerido_por_dia": round(ctx.get("meta_semanal", 15) / 7, 1) if dias else None,
            "nota": "El ritmo sale de la meta semanal registrada por el usuario."}


REGISTRY = {f.__name__: f for f in (get_practice_questions, get_user_progress,
                                    save_session_feedback, get_interview_countdown)}
ALLOWED_ARGS = {t["function"]["name"]: set(t["function"]["parameters"]["properties"]) for t in TOOLS_SCHEMA}


def execute_tool(name: str, raw_args: str, ctx: dict) -> dict:
    """Valida nombre/argumentos y ejecuta. Nunca lanza: devuelve {"error": ...}."""
    if name not in REGISTRY:
        return {"error": f"función desconocida: {name}"}
    try:
        args = json.loads(raw_args or "{}")
        if not isinstance(args, dict):
            raise ValueError
    except ValueError:
        return {"error": "argumentos JSON inválidos"}
    args = {k: v for k, v in args.items() if k in ALLOWED_ARGS[name]}  # descarta user_id y extras
    try:
        return REGISTRY[name](ctx, **args)
    except TypeError as e:
        return {"error": f"argumentos incorrectos: {e}"}
    except Exception as e:  # noqa: BLE001 - la herramienta no debe tumbar el chat
        return {"error": f"fallo interno de la herramienta: {type(e).__name__}"}
