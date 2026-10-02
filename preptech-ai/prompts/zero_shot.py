"""ZERO-SHOT: instrucción + formato, SIN ejemplos."""
from .feedback import FEEDBACK_FORMAT

ZERO_SHOT_PROMPT = f"""\
Eres un evaluador de respuestas conductuales con el método STAR. Analiza la \
respuesta del candidato y señala qué componentes están presentes.

{FEEDBACK_FORMAT}\
"""


def build_zero_shot_messages(pregunta: str, respuesta: str) -> list[dict]:
    return [
        {"role": "system", "content": ZERO_SHOT_PROMPT},
        {"role": "user", "content": f"Pregunta: {pregunta}\n<entrada_usuario>\n{respuesta}\n</entrada_usuario>"},
    ]
