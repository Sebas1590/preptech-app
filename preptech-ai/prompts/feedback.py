"""Formato de retroalimentación y esquema JSON compartido por zero/one/few-shot."""

FEEDBACK_FORMAT = """\
Devuelve SOLO un objeto JSON con esta forma exacta:
{
  "situation": {"present": true|false, "evidence": "cita corta de la respuesta o ''"},
  "task":      {"present": true|false, "evidence": "..."},
  "action":    {"present": true|false, "evidence": "..."},
  "result":    {"present": true|false, "evidence": "..."},
  "score": entero 1-5,
  "strength": "un acierto concreto",
  "improvements": ["máximo 2 mejoras concretas"],
  "next_step": "un siguiente paso accionable"
}
Criterios: present=true solo si el componente está explícito en el texto. \
La Acción debe describir lo que hizo el usuario (no "nosotros"). El Resultado \
debe ser medible o verificable. No inventes datos que no estén en la respuesta.\
"""

STAR_KEYS = ("situation", "task", "action", "result")
