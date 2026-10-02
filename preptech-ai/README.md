# Coach PrepTech — módulo de IA (Streamlit + OpenAI)

Chatbot de preparación para entrevistas técnicas (algoritmos, system design, behavioral con STAR) con
**prompt engineering aplicado**: biblioteca de prompts y técnicas zero-shot / one-shot / few-shot.
Es una app independiente del frontend React (`../preptech-frontend`), pero usa su banco de preguntas
(`data/banco.json`, exportado de `src/lib/preptech-data.ts`) y el mismo tema oscuro/lima.

## Instalación y ejecución

```bash
cd preptech-ai
pip install -r requirements.txt
cp .env.example .env        # y pon tu OPENAI_API_KEY real en .env
streamlit run app.py
```

Variables: `OPENAI_API_KEY` (obligatoria), `OPENAI_MODEL` (por defecto `gpt-4.1-mini`),
`OPENAI_TIMEOUT`, `MAX_REQUESTS_PER_HOUR`. `.env` está en `.gitignore`; la clave nunca se muestra en la UI.

## Dónde está cada cosa

| Ruta | Contenido |
|---|---|
| `prompts/system.py` | Prompt de sistema (Entrega 2) + composición por modo |
| `prompts/zero_shot.py` · `one_shot.py` · `few_shot.py` | Técnicas de prompting (0, 1 y 3 ejemplos) |
| `prompts/feedback.py` | Esquema JSON de retroalimentación STAR compartido |
| `prompts/algorithms.py` · `system_design.py` · `behavioral.py` | Modo de cada tipo de práctica |
| `services/llm_service.py` | Cliente OpenAI, function calling, errores, tokens |
| `services/tools.py` | `get_practice_questions`, `get_user_progress`, `save_session_feedback`, `get_interview_countdown` |
| `services/guardrails.py` | Validación de entrada, anti prompt-injection, límite de uso |

## Cómo probar las técnicas

Pestaña **🧪 Analizador STAR / Comparador**: pulsa *Cargar respuesta de ejemplo* y luego
- **Zero-shot**: elige "Zero-shot" en el sidebar → *Analizar con Zero-shot* (solo instrucción + formato).
- **One-shot**: "One-shot" → incluye 1 ejemplo de entrada/salida.
- **Few-shot**: "Few-shot" → incluye 3 ejemplos (STAR completo, Acción débil, sin Resultado).
- **Comparar las 3**: misma respuesta, tres técnicas, tabla de nota/componentes/tokens y el prompt enviado.

En **💬 Coach** (modo Behavioral) las respuestas largas se analizan con la técnica elegida en el sidebar.
La pestaña **📚 Biblioteca** muestra los prompts (solo lectura).

## Datos reales vs. demo

- Banco de preguntas: **real** (del frontend).
- Progreso: el frontend guarda en `localStorage`, así que Streamlit no puede leerlo solo. Sube tu export
  (consola del navegador: `copy(localStorage['preptech:v1'])` → guárdalo como `.json`). Sin archivo se usan
  datos **de demostración** (`data/demo_progress.json`), marcados como tales en la UI y en la respuesta del coach.
- El `user_id` lo fija el backend; el modelo no puede elegirlo. Feedback guardado en `data/feedback_log.jsonl` (ignorado por git).

## Pruebas

```bash
pip install pytest && python -m pytest tests
```
