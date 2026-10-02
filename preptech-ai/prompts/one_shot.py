"""ONE-SHOT: instrucción + UN ejemplo (entrada y salida) + la nueva entrada."""
import json

from .feedback import FEEDBACK_FORMAT

ONE_SHOT_INSTRUCTION = f"""\
Eres un evaluador de respuestas conductuales con el método STAR. Analiza la \
respuesta del candidato imitando el criterio y el formato del ejemplo.

{FEEDBACK_FORMAT}\
"""

ONE_SHOT_EXAMPLE = {
    "pregunta": "Describe una vez en que rompiste algo en producción.",
    "entrada": (
        "Hace un año en mi pasantía desplegué una migración sin probarla en staging y "
        "dejó la API caída 20 minutos. Yo era responsable del despliegue. Hice rollback, "
        "avisé al equipo y escribí un post-mortem. Después añadí un paso obligatorio de "
        "staging al pipeline y no volvió a ocurrir en 6 meses."
    ),
    "salida": {
        "situation": {"present": True, "evidence": "desplegué una migración sin probarla en staging"},
        "task": {"present": True, "evidence": "Yo era responsable del despliegue"},
        "action": {"present": True, "evidence": "hice rollback, avisé al equipo, escribí un post-mortem"},
        "result": {"present": True, "evidence": "no volvió a ocurrir en 6 meses"},
        "score": 5,
        "strength": "Asumes la responsabilidad y cierras con un resultado verificable.",
        "improvements": ["Cuantifica el impacto en usuarios afectados durante los 20 minutos."],
        "next_step": "Practica contarla en 90 segundos.",
    },
}


def build_one_shot_messages(pregunta: str, respuesta: str) -> list[dict]:
    ej = ONE_SHOT_EXAMPLE
    return [
        {"role": "system", "content": ONE_SHOT_INSTRUCTION},
        {"role": "user", "content": f"Pregunta: {ej['pregunta']}\n<entrada_usuario>\n{ej['entrada']}\n</entrada_usuario>"},
        {"role": "assistant", "content": json.dumps(ej["salida"], ensure_ascii=False)},
        {"role": "user", "content": f"Pregunta: {pregunta}\n<entrada_usuario>\n{respuesta}\n</entrada_usuario>"},
    ]
