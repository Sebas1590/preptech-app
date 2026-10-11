# Módulo educativo IoT — diseño, simulación y presupuesto

## 1. Arquitectura unificada

```
preptech-frontend (React, UI)  ──/api──►  preptech-ai/server.py (FastAPI, API)
   /coach  /iot  /ia                        ├─ services/ + prompts/   (Coach ya existente, sin reescribir)
                                            └─ iot/                   (simulador propio + lecciones)
```

- **Frontend = interfaz.** Nuevas pantallas: `/ia` (API Key + botón *Conectar* + estado), `/coach` (chat) y `/iot` (lecciones + simulador).
- **Backend = API.** `server.py` expone `/api/ai/*`, `/api/coach/*`, `/api/iot/*` reutilizando `services/` y `prompts/`. Streamlit (`app.py`) queda como panel interno opcional; no se tocó.
- **Clave de la API:** se envía una vez a `POST /api/ai/connect`, se valida contra OpenAI y vive solo en memoria del servidor. Nunca se guarda en el navegador, en disco ni se devuelve (solo `sk-…abcd`). Coherente con la Entrega 2: *la clave reside solo en el backend*.
- **Seguridad heredada:** `user_id` lo fija el servidor, validación de entrada, heurística anti prompt-injection y límite de solicitudes por hora.
- **Progreso real:** el frontend envía su `localStorage` en cada chat, así el coach deja de usar datos de demostración.

## 2. Diseño del módulo IoT

| Elemento | Decisión |
|---|---|
| Placas | ESP32 DevKit y Arduino Uno (ADC 12 y 10 bits) |
| Lenguaje | Subconjunto de C/Arduino: `pinMode`, `digitalWrite/Read`, `analogRead/Write`, `delay`, `millis`, `Serial.print/println`, `if/for/while`, funciones propias, `#define` |
| Simulador | Intérprete propio en Python (`iot/interpreter.py`) con reloj virtual. Devuelve una línea de tiempo de eventos de pines y salida serie; el frontend la reproduce animando LED/botón/sensor |
| Protecciones | Máx. 200 000 instrucciones, 30 s virtuales, 2 000 eventos; detecta `loop()` sin `delay()`; errores con número de línea |
| Lecciones | 1) Parpadear un LED · 2) Botón con `INPUT_PULLUP` · 3) Sensor analógico + monitor serie |
| Evaluación | Cada lección tiene un *escenario* fijo (p. ej. botón pulsado de 1.0 a 2.5 s) y checks automáticos sobre la línea de tiempo |
| IA | Botón «Pista con IA»: pistas graduales (modo `iot` del prompt de sistema), sin entregar la solución |
| Límite | Es una simulación didáctica: no modela electrónica real (rebotes, corrientes, WiFi) |

## 3. Simulación del comportamiento del usuario

1. Entra a **Módulo IoT** → elige la lección 1 (ve objetivo y teoría breve).
2. Lee el sketch inicial con `TODO`; escribe `pinMode(LED, OUTPUT)` y el parpadeo.
3. Pulsa **▶ Compilar y simular**. Si hay un error de sintaxis ve «línea N: …» y corrige.
4. El LED virtual parpadea en la placa, el monitor serie muestra `[0.0s] on`.
5. La verificación marca ✅/⬜ cada criterio; si falla, pide **💡 Pista con IA** (requiere conectar la IA en `/ia`).
6. Lección superada → pasa a la 2: mueve el control «Pulsación automática» y observa cómo el LED responde.
7. En la lección 3 ajusta el slider de oscuridad y compara la lectura del sensor con el umbral.

Fricciones esperadas y su mitigación: olvidar `pinMode` (aviso en pantalla), `loop` sin `delay` (error explicativo), IA desconectada (el simulador funciona igual; solo se desactivan las pistas).

## 4. Presupuesto

**Decisión: simulador propio por código → costo de licencias y hardware = S/ 0.**

| Alternativa | Costo | Observación |
|---|---|---|
| **Simulador propio (elegida)** | **S/ 0** en licencias/hardware | Sin dependencias externas, integrado a la UI y a las lecciones; control total de checks y de la IA |
| Simulador de terceros embebido (p. ej. Wokwi, Tinkercad) | Gratis en planes básicos; planes de pago para uso comercial/embebido | Más realista, pero se depende de un tercero, sus límites y su licencia; difícil evaluar automáticamente |
| Hardware real (ESP32 + sensores) | Referencial ≈ S/ 40–80 por kit/estudiante | Fuera del alcance: el objetivo es aprender sin comprar nada |

> Los precios de terceros y de hardware son **referenciales**; confirmar vigencia antes de usarlos en la entrega.

**Esfuerzo (equipo de 3 estudiantes, costo monetario nulo):** intérprete y API ≈ 20 h · UI (3 pantallas) ≈ 16 h · lecciones y pruebas ≈ 8 h · documentación ≈ 4 h → **≈ 48 h**.

**Costos operativos recurrentes:** infraestructura ya cubierta por el despliegue Dokploy de la Entrega 1; el único gasto variable es el uso de tokens de OpenAI en las pistas (modelo `gpt-4.1-mini`, respuestas ≤ 700 tokens y límite de 40 solicitudes/hora por usuario).

## 5. Cómo ejecutar

```bash
# API
cd preptech-ai && pip install -r requirements.txt && uvicorn server:app --port 8000
# Frontend (proxy /api → :8000)
cd preptech-frontend && pnpm install && pnpm run dev
# Todo junto
docker compose up --build   # http://localhost:8080
```
