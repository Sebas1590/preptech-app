"""FEW-SHOT: instrucción + 3 ejemplos contrastantes + la nueva entrada.

Ejemplo 1: STAR completo. Ejemplo 2: Situación/Tarea buenas pero Acción débil.
Ejemplo 3: sin Resultado.
"""
import json

from .feedback import FEEDBACK_FORMAT

FEW_SHOT_INSTRUCTION = f"""\
Eres un evaluador de respuestas conductuales con el método STAR. Sigue el patrón \
de los ejemplos: sé estricto con "present", cita evidencia textual y calibra la nota \
(5 = STAR completo y medible, 3-4 = todo presente pero algún componente vago, p. ej. un Resultado sin cifra, 3 = falta un componente, 1-2 = faltan varios). Un Resultado sin número ni evidencia verificable cuenta como vago: máximo nota 4.

{FEEDBACK_FORMAT}\
"""


def _c(p: bool, e: str = "") -> dict:
    return {"present": p, "evidence": e}


FEW_SHOT_EXAMPLES = [
    {
        "pregunta": "Describe una vez en que rompiste algo en producción.",
        "entrada": (
            "En mi pasantía desplegué una migración sin probarla en staging y la API cayó 20 "
            "minutos. Yo era responsable del despliegue. Hice rollback, avisé al equipo y escribí "
            "un post-mortem; luego añadí un paso obligatorio de staging al pipeline y no volvió "
            "a pasar en 6 meses."
        ),
        "salida": {
            "situation": _c(True, "desplegué una migración sin probarla en staging"),
            "task": _c(True, "Yo era responsable del despliegue"),
            "action": _c(True, "hice rollback, avisé al equipo, escribí un post-mortem"),
            "result": _c(True, "no volvió a pasar en 6 meses"),
            "score": 5,
            "strength": "Asumes responsabilidad y cierras con un resultado verificable.",
            "improvements": ["Cuantifica cuántos usuarios se vieron afectados."],
            "next_step": "Practica contarla en 90 segundos.",
        },
    },
    {
        "pregunta": "Cuéntame sobre un desacuerdo técnico con un compañero.",
        "entrada": (
            "En el proyecto final de la universidad el equipo discutía si usar MongoDB o "
            "PostgreSQL. Me tocaba decidir la base de datos del módulo de pagos. Se habló mucho "
            "y al final se llegó a un acuerdo entre todos."
        ),
        "salida": {
            "situation": _c(True, "el equipo discutía si usar MongoDB o PostgreSQL"),
            "task": _c(True, "Me tocaba decidir la base de datos del módulo de pagos"),
            "action": _c(False, "solo dice 'se habló mucho'; no describe qué hizo el usuario"),
            "result": _c(False, "'se llegó a un acuerdo' no indica qué se eligió ni su efecto"),
            "score": 2,
            "strength": "Contexto y responsabilidad claros desde el inicio.",
            "improvements": [
                "Describe tus acciones en primera persona: qué argumentos o pruebas presentaste.",
                "Indica qué base se eligió y qué impacto tuvo.",
            ],
            "next_step": "Reescribe solo la parte de Acción con 2 decisiones concretas tuyas.",
        },
    },
    {
        "pregunta": "Háblame de un proyecto con un plazo poco realista.",
        "entrada": (
            "En un hackathon de 24 horas nos pidieron una app de reservas completa. Yo lideraba "
            "el backend. Recorté el alcance a reservar y cancelar, monté la API con FastAPI y "
            "dividí tareas por hora con el equipo."
        ),
        "salida": {
            "situation": _c(True, "hackathon de 24 horas, app de reservas completa"),
            "task": _c(True, "Yo lideraba el backend"),
            "action": _c(True, "recorté el alcance, monté la API con FastAPI, dividí tareas"),
            "result": _c(False, "no dice si se entregó ni qué pasó"),
            "score": 3,
            "strength": "Buena priorización: recortaste alcance con criterio.",
            "improvements": ["Cierra con el resultado: ¿entregaron?, ¿posición o métrica?"],
            "next_step": "Añade una frase final con un número o aprendizaje verificable.",
        },
    },
]


def build_few_shot_messages(pregunta: str, respuesta: str) -> list[dict]:
    msgs = [{"role": "system", "content": FEW_SHOT_INSTRUCTION}]
    for ej in FEW_SHOT_EXAMPLES:
        msgs.append({"role": "user", "content": f"Pregunta: {ej['pregunta']}\n<entrada_usuario>\n{ej['entrada']}\n</entrada_usuario>"})
        msgs.append({"role": "assistant", "content": json.dumps(ej["salida"], ensure_ascii=False)})
    msgs.append({"role": "user", "content": f"Pregunta: {pregunta}\n<entrada_usuario>\n{respuesta}\n</entrada_usuario>"})
    return msgs
